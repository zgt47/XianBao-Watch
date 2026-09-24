# XianBao-Watch

**给 XianBao-Lite 配套使用的外部存活监控 Skill。**

适合 **QwenPaw / AgentScope / 其他托管 Agent**：不需要拥有 VPS，不需要开放额外端口。Agent 只需定时运行脚本，主动访问 XianBao-Lite 的 `/alive/...` 检测地址。

## 给 Agent：看到这里后直接这样做

如果你是 Agent，并且用户让你“安装 XianBao-Watch”或“监控 XianBao-Lite”，请按下面顺序执行：

```bash
git clone https://github.com/zgt47/XianBao-Watch.git
cd XianBao-Watch
```

如果目录已经存在：

```bash
cd XianBao-Watch
git pull --ff-only
```

然后读取本仓库的：

```text
SKILL.md
```

并严格按照其中的调用规则执行。

用户随后会给你一个完整的 XianBao 检测地址，例如：

```text
https://xb.example.com/alive/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

收到后执行：

```bash
python xianbao_watch.py set-url "用户提供的完整检测地址"
```

之后进行一次测试：

```bash
python xianbao_watch.py check
```

如果输出 `OK`，说明适配成功。

## Agent 最简调用规则

建议每 **90 秒**执行一次：

```bash
python xianbao_watch.py check
```

根据脚本输出处理：

| 输出 | Agent 应做什么 |
|---|---|
| `OK` | 完全静默，不通知用户 |
| `ALERT|...` | 将后面的内容作为故障通知发送一次 |
| `RECOVERED|...` | 将后面的内容作为恢复通知发送一次 |
| `ERROR|...` | 通知用户监控 Skill 配置异常 |

**不要让大模型自己重新计算失败次数。** 连续失败、是否已经报警、恢复状态都由脚本保存。

## 工作方式

```text
QwenPaw / Agent
      │
      │ 每 90 秒执行一次
      ▼
xianbao_watch.py check
      │
      ├─ 正常 → OK → 保持静默
      ├─ 连续失败达到阈值 → ALERT → Agent 通知用户一次
      └─ 故障后恢复 → RECOVERED → Agent 通知用户一次
```

## 第一次配置 / 更换 XianBao 地址

用户从 XianBao-Lite：

```text
运行状态 → 运行设置 → 外部存活检测
```

复制完整检测地址。

设置地址：

```bash
python xianbao_watch.py set-url "https://你的域名/alive/xxxxxxxx"
```

以后用户重新生成了检测地址，只需要再次执行一次 `set-url`，**不需要修改脚本**。

## 查看当前配置

```bash
python xianbao_watch.py show
```

## 修改参数

连续失败多少次报警：

```bash
python xianbao_watch.py set-threshold 3
```

请求超时：

```bash
python xianbao_watch.py set-timeout 10
```

默认：

- 请求超时：10 秒
- 连续失败阈值：3 次
- 推荐检测周期：90 秒

## 运行文件

脚本运行后会在本地生成：

```text
config.json
state.json
```

其中：

- `config.json`：保存 XianBao 检测地址、超时、失败阈值。
- `state.json`：保存连续失败次数、报警状态、最近成功时间和 seq。

它们已经加入 `.gitignore`。以后执行 `git pull` 更新 Skill 时，不会覆盖用户已经设置好的检测地址和运行状态。

详细调用协议见 [SKILL.md](./SKILL.md)。
