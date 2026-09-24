# XianBao-Watch

XianBao-Lite 的外部存活监控脚本。

它只做三件事：

1. 定时访问 XianBao-Lite 的 `/alive/...` 地址；
2. 连续失败达到阈值时发送一次异常消息；
3. 恢复后发送一次恢复消息。

正常运行时只是普通 HTTP 请求，不需要大模型参与。

## 默认规则

- 每 60 秒检测一次
- 请求超时 10 秒
- 连续失败 3 次报警
- 持续故障不重复报警
- 恢复后通知一次
- 通知失败会继续重试

## 安装

```bash
git clone https://github.com/zgt47/XianBao-Watch.git
cd XianBao-Watch
```

配置检测地址：

```bash
python xianbao_watch.py set-url "https://你的地址/alive/xxxxxxxx"
```

测试检测：

```bash
python xianbao_watch.py check
```

正常返回：

```text
OK
```

## 配置消息出口

XianBao-Watch 支持同时使用多路通知。

原消息出口可以使用“命令”或“Webhook”其中一种；企业微信应用可以作为独立的第二路通知。

异常或恢复时，两路都会尝试发送。只要任意一路成功，就认为本次消息已经送达；如果全部失败，脚本会继续重试。

### 原消息出口：命令方式

如果当前环境有直接发送消息的命令：

```bash
python xianbao_watch.py set-command <命令> <参数...> "{message}"
```

`{message}` 会自动替换成异常或恢复内容。

### 原消息出口：Webhook 方式

如果有 Webhook：

```bash
python xianbao_watch.py set-webhook "https://你的Webhook地址"
```

发送内容：

```json
{"text":"消息正文"}
```

### 企业微信应用

企业微信应用是一条独立外部通知链路。即使原来的 TG、聊天机器人或其他消息出口失效，企业微信仍会单独尝试发送。

需要：

- 企业 ID
- 应用 AgentID
- 应用 Secret
- 接收成员，可选；默认 `@all`，即应用可见范围内全部成员

配置：

```bash
python xianbao_watch.py set-wecom-app "<企业ID>" "<应用AgentID>" "<应用Secret>"
```

如果只想发送给某个企业微信成员，可再加成员账号：

```bash
python xianbao_watch.py set-wecom-app "<企业ID>" "<应用AgentID>" "<应用Secret>" "<成员账号>"
```

如果你已经在 XianBao-Lite 里配置过“企业微信应用”，可以直接使用同一套企业 ID、AgentID 和 Secret。

关闭企业微信应用通知：

```bash
python xianbao_watch.py disable-wecom-app
```

## 测试通知

配置完成后：

```bash
python xianbao_watch.py notify-test
```

测试结果会显示每一路是否成功，例如：

```text
SENT|测试消息已发送|原消息出口:成功；企业微信应用:成功
```

如果原消息出口失败、企业微信成功，也会视为测试消息已成功送达。

## 启动

```bash
python xianbao_watch.py start
```

查看状态：

```bash
python xianbao_watch.py status
```

停止：

```bash
python xianbao_watch.py stop
```

## 修改参数

```bash
python xianbao_watch.py set-interval 60
python xianbao_watch.py set-threshold 3
python xianbao_watch.py set-timeout 10
```

## 给自动化工具 / Agent

如果由自动化工具或 Agent 安装，请先读取 [SKILL.md](./SKILL.md)。

安装完成后，周期检测由 XianBao-Watch 自己运行，不要再创建额外的周期检查任务。
