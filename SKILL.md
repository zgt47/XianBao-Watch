# XianBao-Watch Agent Skill

## 身份

XianBao-Watch 是**平台无关**的 XianBao-Lite 外部存活监控工具。

QwenPaw 只是一个可选通知适配器。看到仓库里出现 QwenPaw 相关命令时，不要把项目判断为“仅支持 QwenPaw”。

## 核心目标

用户要求的是低 Token 监控：

- 普通 Python 脚本自行巡检；
- 正常情况下不调用 Agent / 大模型；
- 连续异常达到阈值后才发送消息；
- 恢复后发送一次恢复消息；
- 安装完成后 Agent 退出周期运行链路。

## 严禁

不要：

- 用 Agent Heartbeat 每分钟执行检查；
- 用会唤醒大模型的定时任务执行 `check`；
- 让大模型维护失败次数；
- 正常时发送“运行正常”消息；
- 因为当前平台不是 QwenPaw 就拒绝安装；
- 猜测不存在的消息发送命令或用户 ID。

## 安装前先确认

当前平台必须能持续运行普通 Python 后台进程。

如果平台会在对话结束后立即杀掉后台进程，则不能满足本项目的长期监控目标。不要偷偷改成周期唤醒大模型。

## 安装

```bash
git clone https://github.com/zgt47/XianBao-Watch.git
cd XianBao-Watch
```

已存在：

```bash
cd XianBao-Watch
git pull --ff-only
```

更新不得删除本地 `config.json`、`state.json`。

## 配置 XianBao

用户提供完整 `/alive/...` 地址后：

```bash
python xianbao_watch.py set-url "用户提供的完整地址"
```

然后：

```bash
python xianbao_watch.py check
```

正常应输出 `OK`。

## 选择消息适配器

目标是找到**不经过大模型推理的直接消息出口**。

优先顺序：

### 1. 当前平台有直接发送消息的命令行接口

验证命令真实存在后，配置：

```bash
python xianbao_watch.py set-command <发送命令> <参数...> "{message}"
```

`{message}` 必须保留，脚本会自动替换。

### 2. 当前平台提供 Webhook

```bash
python xianbao_watch.py set-webhook "https://..."
```

脚本会 POST JSON：

```json
{"text":"消息正文"}
```

### 3. 当前环境是 QwenPaw

仅在确定安装了 `qwenpaw` 时，读取当前真实聊天目标，再配置：

```bash
python xianbao_watch.py set-qwenpaw "<agent-id>" "<channel>" "<target-user>" "<target-session>"
```

不得猜 target-user 或 target-session。

### 4. 当前平台没有任何模型外直接消息出口

明确告诉用户该平台暂时无法实现“零模型常规巡检 + 异常直推”的完整目标。不要改成高频调用模型来冒充适配成功。

## 必须测试通知

```bash
python xianbao_watch.py notify-test
```

确认测试消息成功以后才能启动。

## 启动

```bash
python xianbao_watch.py start
```

再检查：

```bash
python xianbao_watch.py status
```

确认 `running` 为 true。

## 运行逻辑

默认每 60 秒：

```text
HTTP GET /alive/...
→ 成功：清零失败次数，静默
→ 第 1 次失败：静默
→ 第 2 次失败：静默
→ 第 3 次连续失败：记录 ALERT 并通过已配置适配器发送
→ 持续失败：不重复创建新 ALERT
→ 恢复：记录 RECOVERED 并发送一次
```

如果消息出口临时发送失败，待发送事件会保留，后台循环继续重试，不应因一次消息失败永久丢失报警。

## 常用命令

```bash
python xianbao_watch.py set-interval 60
python xianbao_watch.py set-threshold 3
python xianbao_watch.py set-timeout 10
python xianbao_watch.py notify-test
python xianbao_watch.py status
python xianbao_watch.py stop
python xianbao_watch.py show
```

仅用户明确要求时：

```bash
python xianbao_watch.py reset
```

## 换平台迁移协议

用户从旧云 Agent 换到新云 Agent 时：

1. 在新平台拉取本仓库；
2. 配置原来的 XianBao `/alive/...` 地址；
3. 根据新平台选择新的消息适配器；
4. 执行 `notify-test`；
5. 启动后台监控；
6. 不要求修改 XianBao-Lite；
7. 不要求 QwenPaw 存在。

监控核心与 Agent 品牌无关。
