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

XianBao-Watch 不规定使用哪个聊天平台。

只需要提供一种能直接发送消息的方法。

### 命令方式

如果当前环境有发送消息的命令：

```bash
python xianbao_watch.py set-command <命令> <参数...> "{message}"
```

`{message}` 会自动替换成异常或恢复内容。

### Webhook 方式

如果有 Webhook：

```bash
python xianbao_watch.py set-webhook "https://你的Webhook地址"
```

发送内容：

```json
{"text":"消息正文"}
```

配置完成后测试：

```bash
python xianbao_watch.py notify-test
```

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
