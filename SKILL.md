# XianBao-Watch Skill

## 任务

安装并配置 XianBao-Watch，使它独立监控 XianBao-Lite。

安装完成后，周期检测由脚本自己执行。

## 安装步骤

### 1. 获取项目

```bash
git clone https://github.com/zgt47/XianBao-Watch.git
cd XianBao-Watch
```

目录已存在时：

```bash
cd XianBao-Watch
git pull --ff-only
```

不要删除已有的 `config.json` 和 `state.json`。

### 2. 配置检测地址

```bash
python xianbao_watch.py set-url "用户提供的完整 /alive/ 地址"
```

测试：

```bash
python xianbao_watch.py check
```

正常应返回：

```text
OK
```

### 3. 配置原消息出口

根据当前环境已有能力选择一种。

如果有可以直接发送消息的命令：

```bash
python xianbao_watch.py set-command <真实命令> <真实参数...> "{message}"
```

如果有 Webhook：

```bash
python xianbao_watch.py set-webhook "真实Webhook地址"
```

不要猜命令、参数、用户 ID、会话 ID 或 Webhook。

### 4. 配置企业微信应用

如果用户提供企业微信应用参数，配置为第二路独立通知：

```bash
python xianbao_watch.py set-wecom-app "<企业ID>" "<应用AgentID>" "<应用Secret>"
```

默认发送给应用可见范围内全部成员。

如果用户指定企业微信成员账号：

```bash
python xianbao_watch.py set-wecom-app "<企业ID>" "<应用AgentID>" "<应用Secret>" "<成员账号>"
```

如果用户已经在 XianBao-Lite 使用企业微信应用，可以复用同一套企业 ID、AgentID 和 Secret。

不要把 Secret 提交到 GitHub。

### 5. 测试通知

```bash
python xianbao_watch.py notify-test
```

通知测试成功后再继续。

如果配置了多路通知，检查输出中各路状态。

### 6. 启动监控

```bash
python xianbao_watch.py start
python xianbao_watch.py status
```

确认 `running` 为 `true`。

## 多路通知规则

异常或恢复时，所有已经配置的通知链路都会尝试发送。

例如：

```text
原消息出口 → TG / 机器人 / 其他聊天接口
企业微信应用 → 企业微信官方接口
```

只要任意一路成功，就认为本次报警已经送达。

只有全部通知链路都失败时，才保留待发送事件并在后续继续重试。

这样某一路消息服务失效时，另一条链路仍能收到报警。

## 运行规则

默认：

```text
每 60 秒访问一次 /alive/
成功 → 静默
连续失败 1 次 → 静默
连续失败 2 次 → 静默
连续失败 3 次 → 发送一次异常消息
持续失败 → 不重复创建新报警
恢复 → 发送一次恢复消息
```

## 重要限制

不要另外创建会重复执行 `check` 的周期任务。

不要让大模型维护失败次数。

不要在正常状态下发送消息。

如果当前环境不能保持普通 Python 后台进程长期运行，应明确说明无法在该环境长期运行，不要改成高频调用大模型代替。

## 常用命令

```bash
python xianbao_watch.py status
python xianbao_watch.py stop
python xianbao_watch.py set-interval 60
python xianbao_watch.py set-threshold 3
python xianbao_watch.py set-timeout 10
python xianbao_watch.py set-wecom-app "<企业ID>" "<应用AgentID>" "<应用Secret>"
python xianbao_watch.py disable-wecom-app
python xianbao_watch.py notify-test
```
