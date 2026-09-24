#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent
CONFIG = BASE / "config.json"
STATE = BASE / "state.json"
PID_FILE = BASE / "xianbao_watch.pid"
LOG_FILE = BASE / "xianbao_watch.log"
CN = timezone(timedelta(hours=8))

DEFAULT_CONFIG = {
    "url": "",
    "timeout": 10,
    "failThreshold": 3,
    "intervalSeconds": 60,
    "notify": {
        "mode": "none",
        "command": [],
        "webhookUrl": ""
    }
}

DEFAULT_STATE = {
    "failures": 0,
    "alerting": False,
    "lastSuccess": "",
    "lastSeq": None,
    "lastError": "",
    "pendingEvent": "",
    "pendingMessage": "",
    "lastNotifyError": ""
}


def now_cn():
    return datetime.now(CN).isoformat(timespec="seconds")


def deep_merge(base, extra):
    result = dict(base)
    for key, value in (extra or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load(path, fallback):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return deep_merge(fallback, data)
    except Exception:
        pass
    return deep_merge({}, fallback)


def save(path, obj):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def load_config():
    cfg = load(CONFIG, DEFAULT_CONFIG)
    cfg["url"] = str(cfg.get("url") or "").strip()

    try:
        cfg["timeout"] = max(2, min(60, int(cfg.get("timeout") or 10)))
    except Exception:
        cfg["timeout"] = 10

    try:
        cfg["failThreshold"] = max(1, min(20, int(cfg.get("failThreshold") or 3)))
    except Exception:
        cfg["failThreshold"] = 3

    try:
        cfg["intervalSeconds"] = max(10, min(3600, int(cfg.get("intervalSeconds") or 60)))
    except Exception:
        cfg["intervalSeconds"] = 60

    notify = deep_merge(DEFAULT_CONFIG["notify"], cfg.get("notify") or {})
    notify["mode"] = str(notify.get("mode") or "none").strip().lower()
    notify["webhookUrl"] = str(notify.get("webhookUrl") or "").strip()

    if not isinstance(notify.get("command"), list):
        notify["command"] = []
    notify["command"] = [str(x) for x in notify["command"]]

    cfg["notify"] = notify
    return cfg


def load_state():
    state = load(STATE, DEFAULT_STATE)
    state["failures"] = max(0, int(state.get("failures") or 0))
    state["alerting"] = bool(state.get("alerting"))
    return state


def set_url(url):
    url = str(url or "").strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        print("ERROR|网址必须以 http:// 或 https:// 开头")
        return 2

    cfg = load_config()
    cfg["url"] = url
    save(CONFIG, cfg)
    print("SAVED|检测地址已更新")
    return 0


def set_threshold(value):
    try:
        n = int(value)
    except Exception:
        print("ERROR|失败阈值必须是整数")
        return 2

    if not 1 <= n <= 20:
        print("ERROR|失败阈值范围是 1-20")
        return 2

    cfg = load_config()
    cfg["failThreshold"] = n
    save(CONFIG, cfg)
    print(f"SAVED|失败阈值={n}")
    return 0


def set_timeout(value):
    try:
        n = int(value)
    except Exception:
        print("ERROR|超时必须是整数秒")
        return 2

    if not 2 <= n <= 60:
        print("ERROR|超时范围是 2-60 秒")
        return 2

    cfg = load_config()
    cfg["timeout"] = n
    save(CONFIG, cfg)
    print(f"SAVED|超时={n}秒")
    return 0


def set_interval(value):
    try:
        n = int(value)
    except Exception:
        print("ERROR|检测间隔必须是整数秒")
        return 2

    if not 10 <= n <= 3600:
        print("ERROR|检测间隔范围是 10-3600 秒")
        return 2

    cfg = load_config()
    cfg["intervalSeconds"] = n
    save(CONFIG, cfg)
    print(f"SAVED|检测间隔={n}秒")
    return 0


def set_command(argv):
    argv = [str(x) for x in argv]

    if not argv:
        print("ERROR|必须提供消息发送命令")
        return 2

    if not any("{message}" in x for x in argv):
        print("ERROR|命令参数中必须包含 {message} 占位符")
        return 2

    cfg = load_config()
    cfg["notify"] = {
        "mode": "command",
        "command": argv,
        "webhookUrl": ""
    }
    save(CONFIG, cfg)
    print("SAVED|命令通知已配置")
    return 0


def set_webhook(url):
    url = str(url or "").strip()

    if not (url.startswith("http://") or url.startswith("https://")):
        print("ERROR|Webhook 地址必须以 http:// 或 https:// 开头")
        return 2

    cfg = load_config()
    cfg["notify"] = {
        "mode": "webhook",
        "command": [],
        "webhookUrl": url
    }
    save(CONFIG, cfg)
    print("SAVED|Webhook 通知已配置")
    return 0


def disable_notify():
    cfg = load_config()
    cfg["notify"] = {
        "mode": "none",
        "command": [],
        "webhookUrl": ""
    }
    save(CONFIG, cfg)
    print("SAVED|通知已关闭")
    return 0


def fetch_alive(url, timeout):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "XianBao-Watch/4.0",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        },
        method="GET"
    )

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        code = getattr(resp, "status", 200)
        if code != 200:
            raise RuntimeError(f"HTTP {code}")
        raw = resp.read(65536)

    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise RuntimeError("返回内容不是有效 JSON") from exc

    if data.get("alive") is not True:
        raise RuntimeError("返回内容缺少 alive=true")

    return data.get("seq"), str(data.get("time") or "").strip()


def perform_check():
    cfg = load_config()
    state = load_state()

    if not cfg["url"]:
        return "ERROR", "尚未配置检测地址，请先执行 set-url", 2

    try:
        seq, remote_time = fetch_alive(cfg["url"], cfg["timeout"])
        was_alerting = state["alerting"]

        state.update({
            "failures": 0,
            "alerting": False,
            "lastSuccess": remote_time or now_cn(),
            "lastSeq": seq,
            "lastError": ""
        })

        if was_alerting:
            state["pendingEvent"] = "RECOVERED"
            state["pendingMessage"] = (
                f"XianBao-Lite 已恢复\n"
                f"恢复时间：{state['lastSuccess']}"
            )

        save(STATE, state)

        if was_alerting:
            return "RECOVERED", state["pendingMessage"], 0

        return "OK", "", 0

    except Exception as exc:
        state["failures"] = int(state.get("failures") or 0) + 1
        state["lastError"] = str(exc)
        threshold = cfg["failThreshold"]

        if state["failures"] >= threshold and not state["alerting"]:
            state["alerting"] = True
            last = state.get("lastSuccess") or "无成功记录"
            state["pendingEvent"] = "ALERT"
            state["pendingMessage"] = (
                f"XianBao-Lite 可能已离线\n"
                f"连续失败：{state['failures']} 次\n"
                f"最后成功：{last}\n"
                f"错误：{state['lastError']}"
            )
            save(STATE, state)
            return "ALERT", state["pendingMessage"], 1

        save(STATE, state)
        return "OK", "", 0


def run_command_notify(message, command):
    if not command:
        return False, "消息发送命令为空"

    argv = [str(x).replace("{message}", message) for x in command]
    exe = shutil.which(argv[0]) or (argv[0] if Path(argv[0]).exists() else None)

    if not exe:
        return False, f"找不到通知命令：{argv[0]}"

    argv[0] = exe

    try:
        cp = subprocess.run(
            argv,
            cwd=str(BASE),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
            check=False
        )
    except Exception as exc:
        return False, str(exc)

    if cp.returncode == 0:
        return True, ""

    detail = (cp.stderr or cp.stdout or f"退出码 {cp.returncode}").strip()
    return False, detail[:1000]


def run_webhook_notify(message, url):
    if not url:
        return False, "Webhook 地址为空"

    body = json.dumps({"text": message}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "XianBao-Watch/4.0"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            code = getattr(resp, "status", 200)
            if 200 <= code < 300:
                return True, ""
            return False, f"Webhook HTTP {code}"
    except Exception as exc:
        return False, str(exc)


def notify_message(message):
    notify = load_config()["notify"]
    mode = notify.get("mode")

    if mode == "command":
        return run_command_notify(message, notify.get("command") or [])

    if mode == "webhook":
        return run_webhook_notify(message, notify.get("webhookUrl") or "")

    return False, "尚未配置消息通知接口"


def flush_pending_notification():
    state = load_state()
    event = str(state.get("pendingEvent") or "")
    message = str(state.get("pendingMessage") or "")

    if not event or not message:
        return True, ""

    ok, error = notify_message(message)
    state = load_state()

    if ok:
        state["pendingEvent"] = ""
        state["pendingMessage"] = ""
        state["lastNotifyError"] = ""
    else:
        state["lastNotifyError"] = str(error or "")

    save(STATE, state)
    return ok, error


def check_command():
    event, message, code = perform_check()

    if event == "OK":
        print("OK")
    else:
        print(f"{event}|{message.replace(chr(10), '|')}")

    return code


def notify_test():
    ok, error = notify_message("XianBao-Watch 通知测试：消息出口工作正常。")

    state = load_state()
    state["lastNotifyError"] = "" if ok else str(error or "")
    save(STATE, state)

    if ok:
        print("SENT|测试消息已发送")
        return 0

    print(f"ERROR|测试消息发送失败|{error}")
    return 2


def daemon_loop():
    cfg = load_config()

    if not cfg["url"]:
        print(f"{now_cn()} ERROR 尚未配置检测地址", flush=True)
        return 2

    print(
        f"{now_cn()} START interval={cfg['intervalSeconds']}s "
        f"threshold={cfg['failThreshold']} notify={cfg['notify']['mode']}",
        flush=True
    )

    while True:
        event, message, _ = perform_check()

        if event == "ERROR":
            print(f"{now_cn()} ERROR {message}", flush=True)

        state = load_state()

        if state.get("pendingEvent"):
            pending = state.get("pendingEvent")
            ok, error = flush_pending_notification()

            if ok:
                print(f"{now_cn()} {pending} notification_sent", flush=True)
            else:
                print(f"{now_cn()} {pending} notification_failed: {error}", flush=True)

        time.sleep(load_config()["intervalSeconds"])


def read_pid():
    try:
        return int(PID_FILE.read_text(encoding="utf-8").strip())
    except Exception:
        return None


def pid_running(pid):
    if not pid or pid <= 0:
        return False

    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def start_daemon():
    pid = read_pid()

    if pid_running(pid):
        print(f"RUNNING|XianBao-Watch 已在后台运行|PID={pid}")
        return 0

    cfg = load_config()

    if not cfg["url"]:
        print("ERROR|尚未配置检测地址，请先执行 set-url")
        return 2

    if cfg["notify"].get("mode") == "none":
        print("ERROR|尚未配置消息通知接口")
        return 2

    log = open(LOG_FILE, "a", encoding="utf-8")

    try:
        proc = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "_daemon"],
            cwd=str(BASE),
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True
        )
    finally:
        log.close()

    PID_FILE.write_text(str(proc.pid), encoding="utf-8")
    time.sleep(0.4)

    if not pid_running(proc.pid):
        try:
            PID_FILE.unlink()
        except Exception:
            pass

        print("ERROR|后台监控启动失败，请查看 xianbao_watch.log")
        return 2

    print(f"STARTED|XianBao-Watch 已在后台运行|PID={proc.pid}")
    return 0


def stop_daemon():
    pid = read_pid()

    if not pid_running(pid):
        try:
            PID_FILE.unlink()
        except Exception:
            pass

        print("STOPPED|当前未运行")
        return 0

    try:
        os.kill(pid, signal.SIGTERM)
    except Exception as exc:
        print(f"ERROR|停止失败|{exc}")
        return 2

    for _ in range(30):
        if not pid_running(pid):
            break
        time.sleep(0.2)

    try:
        PID_FILE.unlink()
    except Exception:
        pass

    print("STOPPED|后台监控已停止")
    return 0


def show():
    pid = read_pid()

    print(json.dumps({
        "config": load_config(),
        "state": load_state(),
        "daemon": {
            "running": pid_running(pid),
            "pid": pid if pid_running(pid) else None
        },
        "logFile": str(LOG_FILE)
    }, ensure_ascii=False, indent=2))

    return 0


def reset():
    save(STATE, DEFAULT_STATE)
    print("SAVED|监控状态已重置")
    return 0


def help_text():
    print("""XianBao Watch

后台脚本自行检测 XianBao-Lite 存活状态。
通知接口与具体平台无关。

命令：
  python xianbao_watch.py set-url "https://.../alive/..."
  python xianbao_watch.py set-command <命令> <参数...> "{message}"
  python xianbao_watch.py set-webhook "https://..."
  python xianbao_watch.py disable-notify
  python xianbao_watch.py set-interval 60
  python xianbao_watch.py set-threshold 3
  python xianbao_watch.py set-timeout 10
  python xianbao_watch.py notify-test
  python xianbao_watch.py check
  python xianbao_watch.py start
  python xianbao_watch.py stop
  python xianbao_watch.py status
  python xianbao_watch.py reset
""")

    return 0


def main():
    if len(sys.argv) < 2:
        return help_text()

    cmd = sys.argv[1].lower().strip()

    if cmd == "check":
        return check_command()
    if cmd == "start":
        return start_daemon()
    if cmd == "stop":
        return stop_daemon()
    if cmd in ("show", "status"):
        return show()
    if cmd == "reset":
        return reset()
    if cmd == "notify-test":
        return notify_test()
    if cmd == "disable-notify":
        return disable_notify()
    if cmd == "_daemon":
        return daemon_loop()
    if cmd == "set-url" and len(sys.argv) >= 3:
        return set_url(sys.argv[2])
    if cmd == "set-threshold" and len(sys.argv) >= 3:
        return set_threshold(sys.argv[2])
    if cmd == "set-timeout" and len(sys.argv) >= 3:
        return set_timeout(sys.argv[2])
    if cmd == "set-interval" and len(sys.argv) >= 3:
        return set_interval(sys.argv[2])
    if cmd == "set-webhook" and len(sys.argv) >= 3:
        return set_webhook(sys.argv[2])
    if cmd == "set-command" and len(sys.argv) >= 3:
        return set_command(sys.argv[2:])

    return help_text()


if __name__ == "__main__":
    raise SystemExit(main())
