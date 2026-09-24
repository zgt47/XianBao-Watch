# XianBao-Watch

**给 XianBao-Lite 配套使用的低消耗外部存活监控脚本。**

它的核心原则是：

> **正常巡检完全不调用 Agent / 大模型。**
>
> XianBao-Watch 自己在后台每 60 秒访问一次 XianBao-Lite 的 `/alive/...` 检测地址。
> 只有连续异常达到阈值，或故障恢复时，才通过 QwenPaw 的消息通道直接给用户推送消息。

因此不要使用 QwenPaw Heartbeat 来每分钟询问大模型。

## 给 Agent：安装时这样做

当用户要求“安装 XianBao-Watch”或“监控 XianBao-Lite”时，只在**首次安装和配置**阶段执行下面步骤。

### 1. 下载 / 更新

```bash
git clone https://github.com/zgt47/XianBao-Watch.git
cd XianBao-Watch
```

如果目录已经存在：

```bash
cd XianBao-Watch
git pull --ff-only
```

然后读取本仓库的 `SKILL.md`。

### 2. 配置 XianBao 检测地址

用户会提供完整地址，例如：

```text
https://xb.example.com/alive/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

执行：

```bash
python xianbao_watch.py set-url "用户提供的完整检测地址"
```

### 3. 找到当前 QwenPaw 聊天目标

先查询用户当前使用的聊天会话：

```bash
qwenpaw chats list --agent-id <当前AgentID> --channel <当前渠道>
```

不要猜 `target-user` 或 `target-session`。

取用户当前实际使用的：

- Agent ID
- channel
- user_id
- session_id

然后写入 XianBao-Watch：

```bash
python xianbao_watch.py set-qwenpaw "<agent-id>" "<channel>" "<target-user>" "<target-session>"
```

这里配置的只是 **QwenPaw 消息直推通道**，不是让 Agent 大模型参与巡检。

### 4. 测试

先测试 XianBao：

```bash
python xianbao_watch.py check
```

正常应输出：

```text
OK
```

再测试消息直推：

```bash
python xianbao_watch.py notify-test
```

用户收到测试消息后即可启动后台监控。

### 5. 启动后台监控

```bash
python xianbao_watch.py start
```

查看状态：

```bash
python xianbao_watch.py status
```

以后 **不要创建 QwenPaw Heartbeat，不要创建 Agent 类型定时任务，也不要每 60 秒唤醒大模型**。

## 实际工作方式

```text
XianBao-Watch 后台普通 Python 进程
        │
        │ 每 60 秒
        ▼
访问 XianBao-Lite /alive/随机密钥
        │
        ├─ 正常
        │    └─ 什么都不做
        │       不调用 Agent
        │       不调用模型
        │       不发消息
        │
        ├─ 连续失败 1 次
        │    └─ 静默
        │
        ├─ 连续失败 2 次
        │    └─ 静默
        │
        ├─ 连续失败 3 次
        │    └─ qwenpaw channels send
        │       直接推送故障消息
        │
        └─ 故障后恢复
             └─ qwenpaw channels send
                直接推送恢复消息
```

默认参数：

- 检测间隔：60 秒
- 请求超时：10 秒
- 连续失败阈值：3 次
- 正常状态：完全静默
- 持续故障：只通知首次故障，不重复轰炸
- 恢复：通知一次

## 为什么不使用 QwenPaw Heartbeat

QwenPaw Heartbeat 的作用是按周期把 `HEARTBEAT.md` 当成用户消息交给 Agent 执行。

这意味着如果拿它做 60 秒一次的存活检查，大模型也会被周期性唤醒，不符合本项目“正常运行零模型巡检”的目标。

本项目只借用：

```bash
qwenpaw channels send
```

作为消息发送出口。

它是单向消息推送，不需要先让大模型分析 XianBao 状态。

## XianBao 本身有没有 60 秒心跳

当前 XianBao-Lite 的 `/alive/...` 是**被动检测接口**。

它不是每 60 秒主动向外发送一次心跳。

谁访问它，它就立即返回：

```json
{
  "alive": true,
  "seq": 138,
  "time": "2026-09-24T12:00:00+08:00"
}
```

所以现在只有 **XianBao-Watch 自己的 60 秒巡检周期**，不存在两个心跳周期需要互相匹配。

## 常用命令

修改检测地址：

```bash
python xianbao_watch.py set-url "https://你的域名/alive/xxxxxxxx"
```

修改检测间隔：

```bash
python xianbao_watch.py set-interval 60
```

修改连续失败阈值：

```bash
python xianbao_watch.py set-threshold 3
```

修改请求超时：

```bash
python xianbao_watch.py set-timeout 10
```

查看完整状态：

```bash
python xianbao_watch.py show
```

停止后台监控：

```bash
python xianbao_watch.py stop
```

重新启动：

```bash
python xianbao_watch.py start
```

## 本地运行文件

脚本会在目录内生成：

```text
config.json
state.json
xianbao_watch.pid
xianbao_watch.log
```

其中：

- `config.json`：检测地址、间隔、阈值以及 QwenPaw 消息直推参数。
- `state.json`：连续失败次数、报警状态、最近成功时间等。
- `xianbao_watch.pid`：后台进程编号。
- `xianbao_watch.log`：只记录后台启动、异常通知和通知失败等必要信息。

这些运行文件不会提交到 GitHub。

详细 Agent 安装规则见 [SKILL.md](./SKILL.md)。
