#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent
CONFIG = BASE / "config.json"
STATE = BASE / "state.json"
CN = timezone(timedelta(hours=8))

DEFAULT_CONFIG = {"url": "", "timeout": 10, "failThreshold": 3}
DEFAULT_STATE = {"failures": 0, "alerting": False, "lastSuccess": "", "lastSeq": None, "lastError": ""}


def now_cn():
    return datetime.now(CN).isoformat(timespec="seconds")


def load(path, fallback):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            merged = dict(fallback)
            merged.update(data)
            return merged
    except Exception:
        pass
    return dict(fallback)


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


def fetch_alive(url, timeout):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "XianBao-Watch/1.0",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
        method="GET",
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


def check():
    cfg = load_config()
    state = load_state()

    if not cfg["url"]:
        print("ERROR|尚未配置检测地址，请先执行 set-url")
        return 2

    try:
        seq, remote_time = fetch_alive(cfg["url"], cfg["timeout"])

        was_alerting = state["alerting"]
        state.update({
            "failures": 0,
            "alerting": False,
            "lastSuccess": remote_time or now_cn(),
            "lastSeq": seq,
            "lastError": "",
        })
        save(STATE, state)

        if was_alerting:
            print(f"RECOVERED|XianBao-Lite 已恢复|{state['lastSuccess']}")
        else:
            print("OK")
        return 0

    except Exception as exc:
        state["failures"] = int(state.get("failures") or 0) + 1
        state["lastError"] = str(exc)
        threshold = cfg["failThreshold"]

        if state["failures"] >= threshold and not state["alerting"]:
            state["alerting"] = True
            save(STATE, state)
            last = state.get("lastSuccess") or "无成功记录"
            print(
                f"ALERT|XianBao-Lite 已连续 {state['failures']} 次无法访问"
                f"|最后成功时间 {last}|错误 {state['lastError']}"
            )
            return 1

        save(STATE, state)
        print("OK")
        return 0


def show():
    print(json.dumps({
        "config": load_config(),
        "state": load_state(),
    }, ensure_ascii=False, indent=2))
    return 0


def reset():
    save(STATE, DEFAULT_STATE)
    print("SAVED|监控状态已重置")
    return 0


def help_text():
    print("""XianBao Watch

命令：
  python xianbao_watch.py set-url "https://.../alive/..."
  python xianbao_watch.py check
  python xianbao_watch.py show
  python xianbao_watch.py set-threshold 3
  python xianbao_watch.py set-timeout 10
  python xianbao_watch.py reset
""")
    return 0


def main():
    if len(sys.argv) < 2:
        return help_text()

    cmd = sys.argv[1].lower().strip()

    if cmd == "check":
        return check()
    if cmd == "show":
        return show()
    if cmd == "reset":
        return reset()
    if cmd == "set-url" and len(sys.argv) >= 3:
        return set_url(sys.argv[2])
    if cmd == "set-threshold" and len(sys.argv) >= 3:
        return set_threshold(sys.argv[2])
    if cmd == "set-timeout" and len(sys.argv) >= 3:
        return set_timeout(sys.argv[2])

    return help_text()


if __name__ == "__main__":
    raise SystemExit(main())
