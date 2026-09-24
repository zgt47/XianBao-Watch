# XianBao Watch Skill

## 目标

监控 XianBao-Lite 的公网存活检测地址。

这个 Skill 负责确定：

- XianBao 是否还能被公网访问；
- 是否已经连续失败达到报警阈值；
- 故障状态是否已经通知过；
- 故障后是否恢复。

这些状态由脚本维护，不要让大模型自行重新计算。

## 安装

如果本目录还不存在：

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

## 配置检测地址

用户提供 XianBao-Lite 的完整检测地址后，执行：

```bash
python xianbao_watch.py set-url "用户提供的完整检测地址"
```

例如：

```bash
python xianbao_watch.py set-url "https://xb.example.com/alive/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

如果用户以后重新生成了 XianBao 检测地址，再执行一次 `set-url` 即可。

不要把用户真实检测地址写回 GitHub 仓库。

## 周期检测

建议每 90 秒执行一次：

```bash
python xianbao_watch.py check
```

### 输出处理规则

#### 1. 输出 `OK`

保持静默。

不要：

- 给用户发送“运行正常”；
- 生成冗长总结；
- 重置状态文件。

#### 2. 输出以 `ALERT|` 开头

这是首次进入故障状态。

把 `ALERT|` 后面的内容作为故障信息通知用户。

脚本已经负责防止重复报警；不要自行再次累计失败次数。

#### 3. 输出以 `RECOVERED|` 开头

这是故障后的首次恢复。

把 `RECOVERED|` 后面的内容作为恢复通知发送给用户。

#### 4. 输出以 `ERROR|` 开头

表示监控 Skill 本身配置不完整或命令错误。

通知用户需要检查 XianBao-Watch 配置。

## 脚本状态

脚本运行时会自动生成：

```text
config.json
state.json
```

其中：

- `config.json` 保存检测地址、请求超时、失败阈值；
- `state.json` 保存连续失败次数、报警状态、最近一次成功时间和 seq。

这两个文件是运行状态，不应提交到 GitHub，也不要在普通更新时删除。

## 可用命令

设置或更换检测地址：

```bash
python xianbao_watch.py set-url "https://.../alive/..."
```

检查一次：

```bash
python xianbao_watch.py check
```

查看配置和当前状态：

```bash
python xianbao_watch.py show
```

修改连续失败阈值：

```bash
python xianbao_watch.py set-threshold 3
```

修改请求超时：

```bash
python xianbao_watch.py set-timeout 10
```

仅在用户明确要求时重置监控状态：

```bash
python xianbao_watch.py reset
```

## 定时任务调用模板

如果 Agent 支持 Heartbeat / Scheduled Task，任务内容保持简单：

```text
进入 XianBao-Watch 目录，执行 python xianbao_watch.py check。
严格按照 SKILL.md 的输出处理规则处理结果。
OK 时保持静默；ALERT 时通知故障；RECOVERED 时通知恢复；ERROR 时通知配置异常。
```

不要让 Heartbeat 每次重新分析 XianBao 状态，判断工作已经由脚本完成。
