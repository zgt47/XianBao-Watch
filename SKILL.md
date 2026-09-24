# XianBao Watch Skill

## 目标

给 XianBao-Lite 提供低消耗外部存活检测。

**必须遵守：正常巡检不调用 Agent / 大模型。**

Agent 只负责：

1. 第一次安装 XianBao-Watch；
2. 第一次写入 XianBao 检测地址；
3. 第一次识别用户当前 QwenPaw 聊天目标并配置直推参数；
4. 启动普通后台脚本；
5. 用户以后明确要求修改配置时再执行对应命令。

安装完成后，Agent 不参与每 60 秒巡检。

## 禁止的做法

不要：

- 创建 QwenPaw Heartbeat 来检测 XianBao；
- 创建 Agent 类型的周期任务来执行 `check`；
- 每分钟向大模型发送“检查一下 XianBao”；
- 让大模型维护连续失败次数；
- 正常时给用户发送任何消息。

## 安装

```bash
git clone https://github.com/zgt47/XianBao-Watch.git
cd XianBao-Watch
```

已安装时：

```bash
cd XianBao-Watch
git pull --ff-only
```

更新时不得删除本地 `config.json` 和 `state.json`。

## 配置检测地址

用户提供完整 XianBao 地址后：

```bash
python xianbao_watch.py set-url "用户提供的完整检测地址"
```

检测地址可以随时重新设置，不需要修改脚本。

## 配置 QwenPaw 消息直推

先根据用户当前实际使用的渠道查询聊天会话：

```bash
qwenpaw chats list --agent-id <当前AgentID> --channel <当前渠道>
```

不要猜 user_id 和 session_id。

选择用户当前实际会话后执行：

```bash
python xianbao_watch.py set-qwenpaw "<agent-id>" "<channel>" "<target-user>" "<target-session>"
```

这里使用的是 `qwenpaw channels send` 单向直推能力，不是 Agent 对话，不需要让大模型判断监控结果。

## 首次测试

```bash
python xianbao_watch.py check
```

正常应输出：

```text
OK
```

然后：

```bash
python xianbao_watch.py notify-test
```

确认用户收到测试消息。

## 启动

```bash
python xianbao_watch.py start
```

查看：

```bash
python xianbao_watch.py status
```

停止：

```bash
python xianbao_watch.py stop
```

## 运行逻辑

后台脚本默认每 60 秒自行访问 XianBao 的 `/alive/...`。

默认连续失败阈值为 3 次。

正常：

```text
检测成功
→ 清零失败次数
→ 不调用 Agent
→ 不调用模型
→ 不推送消息
```

第一次、第二次失败：

```text
累计失败次数
→ 静默
```

第三次连续失败：

```text
进入报警状态
→ 直接执行 qwenpaw channels send
→ 给用户推送一次故障消息
```

持续故障：

```text
继续检测
→ 不重复发送故障消息
```

恢复：

```text
首次检测成功
→ 退出报警状态
→ 直接执行 qwenpaw channels send
→ 给用户推送一次恢复消息
```

## 常用设置

检测间隔：

```bash
python xianbao_watch.py set-interval 60
```

失败阈值：

```bash
python xianbao_watch.py set-threshold 3
```

请求超时：

```bash
python xianbao_watch.py set-timeout 10
```

状态：

```bash
python xianbao_watch.py show
```

仅在用户明确要求时重置报警状态：

```bash
python xianbao_watch.py reset
```

## 关键说明

当前 XianBao-Lite 的 `/alive/...` 是被动接口，不是 XianBao 自己每 60 秒发一次心跳。

因此不存在“XianBao 60 秒”和“Agent 90 秒”两个周期。

实际周期只有：

```text
XianBao-Watch 自己每 60 秒访问一次 XianBao。
```

Agent 安装完成后退出运行链路。
