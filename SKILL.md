# XianBao Watch Skill

## 目标

监控 XianBao-Lite 的公网存活检测地址，并把“是否需要通知用户”的判断交给脚本状态机，而不是交给大模型反复推理。

## Agent 安装流程

当用户要求安装本 Skill 时：

```bash
git clone https://github.com/zgt47/XianBao-Watch.git
cd XianBao-Watch
```

如果已经安装：

```bash
cd XianBao-Watch
git pull --ff-only
```

更新时不得删除本地 `config.json` 和 `state.json`。

## 用户提供检测地址后

执行：

```bash
python xianbao_watch.py set-url "用户提供的完整 XianBao 检测地址"
```

随后立刻测试一次：

```bash
python xianbao_watch.py check
```

若输出 `OK`，安装和地址配置完成。

如果用户以后重新生成 XianBao 检测地址，只需要再次执行 `set-url`。

不要把用户真实检测地址提交回 GitHub。

## 周期调用

推荐每 90 秒执行一次：

```bash
python xianbao_watch.py check
```

## 输出处理协议

### `OK`

表示当前检测正常，或者失败次数尚未达到报警阈值。

Agent 必须：

- 保持静默；
- 不给用户发送“运行正常”；
- 不生成周期性总结；
- 不自行修改失败次数；
- 不清空状态文件。

### `ALERT|...`

表示首次达到连续失败阈值。

Agent 必须：

- 将 `ALERT|` 后面的文字作为故障信息通知用户一次；
- 不自行再次累计失败次数；
- 后续如果脚本继续返回 `OK`，仍然保持静默。

脚本会自行保存“已经报警”的状态，因此持续故障不会重复返回 ALERT。

### `RECOVERED|...`

表示之前处于故障报警状态，现在首次恢复。

Agent 必须：

- 将 `RECOVERED|` 后面的文字作为恢复通知发送用户一次；
- 之后恢复正常静默检测。

### `ERROR|...`

表示 Skill 本身没有完成配置，或命令调用错误。

Agent 应通知用户需要检查 XianBao-Watch 配置。

## 状态文件

脚本运行时自动生成：

```text
config.json
state.json
```

`config.json` 保存：

- XianBao 检测地址
- 请求超时
- 连续失败报警阈值

`state.json` 保存：

- 连续失败次数
- 是否已经进入报警状态
- 最近一次成功时间
- 最近一次 seq
- 最近错误

这些状态由脚本维护，Agent 不要自行重写。

## 可调用命令

设置或更换地址：

```bash
python xianbao_watch.py set-url "https://.../alive/..."
```

检查：

```bash
python xianbao_watch.py check
```

查看状态：

```bash
python xianbao_watch.py show
```

修改失败阈值：

```bash
python xianbao_watch.py set-threshold 3
```

修改超时：

```bash
python xianbao_watch.py set-timeout 10
```

仅在用户明确要求时重置：

```bash
python xianbao_watch.py reset
```

## Heartbeat / Scheduled Task 调用模板

如果平台支持 Heartbeat 或定时任务，任务内容保持简单：

```text
进入 XianBao-Watch 目录，执行 python xianbao_watch.py check。
严格按照 SKILL.md 的输出协议处理：
OK 静默；
ALERT 通知故障；
RECOVERED 通知恢复；
ERROR 通知配置异常。
不要自行重新判断连续失败次数。
```

判断工作已经由脚本完成，不需要每次让大模型重新分析 XianBao 状态。
