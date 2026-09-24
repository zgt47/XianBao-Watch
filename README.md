# XianBao-Watch

**平台无关的 XianBao-Lite 外部存活监控工具。**

这个项目不绑定任何一家云 Agent。QwenPaw 只是一个现成的可选适配器，不是运行依赖。

核心原则只有一个：

> **正常巡检由普通 Python 脚本自己完成，不调用 Agent / 大模型；只有真正异常或恢复时，才通过当前平台的“直接消息接口”给用户发消息。**

因此以后从 QwenPaw 换到其他云 Agent，XianBao-Lite 本身和监控逻辑都不用改，只需要重新配置“消息出口”。

## 给任何 Agent：看到这里先做什么

如果用户让你安装或接管 XianBao-Watch：

1. 拉取本仓库；
2. 阅读 `SKILL.md`；
3. 配置用户提供的 XianBao `/alive/...` 地址；
4. 找到**当前平台不经过大模型的直接消息发送方式**；
5. 为 XianBao-Watch 配置对应通知适配器；
6. 运行 `notify-test` 验证用户确实能收到消息；
7. 启动后台监控；
8. 安装完成后退出监控链路，不要创建会周期唤醒大模型的 Heartbeat / Agent 定时任务。

## 工作方式

```text
XianBao-Watch 普通后台进程
        │
        │ 默认每 60 秒
        ▼
访问 XianBao-Lite /alive/...
        │
        ├─ 正常 → 完全静默
        ├─ 第 1、2 次失败 → 静默
        ├─ 连续第 3 次失败 → 直接消息接口 → 故障通知
        └─ 故障后恢复 → 直接消息接口 → 恢复通知
```

正常巡检不需要 Token。

## 第一次安装

```bash
git clone https://github.com/zgt47/XianBao-Watch.git
cd XianBao-Watch
```

已经安装：

```bash
cd XianBao-Watch
git pull --ff-only
```

配置 XianBao 检测地址：

```bash
python xianbao_watch.py set-url "https://你的地址/alive/xxxxxxxx"
```

测试检测：

```bash
python xianbao_watch.py check
```

正常应输出：

```text
OK
```

## 通知适配器

### 方式一：通用命令

适合当前云 Agent / 平台提供“直接发送消息”的命令行工具时使用。

```bash
python xianbao_watch.py set-command <发送命令> <参数...> "{message}"
```

`{message}` 是 XianBao-Watch 自动替换的消息正文。

安装 Agent 必须根据自己所在平台的实际能力填写，**不要猜命令**。

### 方式二：Webhook

如果平台提供可直接接收 HTTP 消息的 Webhook：

```bash
python xianbao_watch.py set-webhook "https://你的Webhook地址"
```

XianBao-Watch 会 POST：

```json
{"text":"异常或恢复消息"}
```

### 方式三：QwenPaw 可选适配器

仅当当前环境确实是 QwenPaw 时使用：

```bash
python xianbao_watch.py set-qwenpaw "<agent-id>" "<channel>" "<target-user>" "<target-session>"
```

这只是方便 QwenPaw 使用的预设，不代表 XianBao-Watch 依赖 QwenPaw。

## 测试消息出口

无论使用哪种适配器，都必须测试：

```bash
python xianbao_watch.py notify-test
```

用户确认收到测试消息以后再启动。

## 启动与管理

启动：

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

查看完整配置：

```bash
python xianbao_watch.py show
```

## 默认参数

- 检测间隔：60 秒
- 请求超时：10 秒
- 连续失败 3 次报警
- 正常时完全静默
- 持续故障只发首次报警
- 恢复后发一次恢复通知
- 如果通知发送失败，会保留待发送事件，后续继续重试

修改检测间隔：

```bash
python xianbao_watch.py set-interval 60
```

修改失败阈值：

```bash
python xianbao_watch.py set-threshold 3
```

修改超时：

```bash
python xianbao_watch.py set-timeout 10
```

## 以后更换云 Agent

不需要改 XianBao-Lite，也不需要重新生成检测接口。

在新平台：

```text
重新拉取 XianBao-Watch
→ set-url 写入原来的 /alive/ 地址
→ 按新平台能力重新配置通知适配器
→ notify-test
→ start
```

只有“消息怎么发给你”这一层需要换。

## 对运行平台的最低要求

XianBao-Watch 需要一个能持续运行普通 Python 后台进程的环境。

如果某个云 Agent 平台只允许短时对话执行、会自动杀掉后台进程，那么它本身不适合作为 XianBao-Watch 的长期宿主。此时应换到支持常驻进程的平台，而不是改成每分钟唤醒大模型。

详细机器执行协议见 [SKILL.md](./SKILL.md)。
