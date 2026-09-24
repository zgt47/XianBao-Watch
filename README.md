# XianBao-Watch

用于 **XianBao-Lite** 的外部存活监控 Skill。

适合部署在 **QwenPaw / AgentScope 等托管 Agent** 中：Agent 不需要拥有 VPS，也不需要开放端口。它只需要定时运行本仓库里的监控脚本，主动访问 XianBao-Lite 提供的 `/alive/...` 地址。

## 工作方式

```text
QwenPaw / Agent
      │
      │ 每 90 秒执行一次
      ▼
xianbao_watch.py check
      │
      ├─ 正常 → OK → 保持静默
      ├─ 连续失败达到阈值 → ALERT → Agent 通知用户
      └─ 故障后恢复 → RECOVERED → Agent 通知用户
```

脚本自己保存连续失败次数和报警状态，Agent 不需要每次重新推理。

## 给 Agent 的安装说明

如果你是 Agent，请执行：

```bash
git clone https://github.com/zgt47/XianBao-Watch.git
cd XianBao-Watch
```

然后阅读：

```text
SKILL.md
```

并按照其中的调用规则执行。

如果当前环境已经存在本仓库，则使用：

```bash
git pull --ff-only
```

更新即可。

> 不要覆盖或删除本地运行生成的 `config.json` 和 `state.json`。

## 第一次配置 XianBao 地址

用户会从 XianBao-Lite：

```text
运行状态 → 运行设置 → 外部存活检测
```

复制完整检测地址，例如：

```text
https://xb.example.com/alive/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

然后执行：

```bash
python xianbao_watch.py set-url "https://xb.example.com/alive/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

以后检测地址变化时，只需要再次执行 `set-url`，无需修改源码。

## 手动检查

```bash
python xianbao_watch.py check
```

正常：

```text
OK
```

连续失败达到阈值：

```text
ALERT|XianBao-Lite 已连续 3 次无法访问|最后成功时间 ...
```

故障后恢复：

```text
RECOVERED|XianBao-Lite 已恢复|...
```

## 查看配置

```bash
python xianbao_watch.py show
```

## 修改参数

连续失败次数：

```bash
python xianbao_watch.py set-threshold 3
```

请求超时：

```bash
python xianbao_watch.py set-timeout 10
```

默认值：

- 请求超时：10 秒
- 连续失败阈值：3 次
- 建议定时周期：90 秒

详细调用规则见 [SKILL.md](./SKILL.md)。
