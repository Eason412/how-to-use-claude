---
name: claude-cleanup
description: "在 macOS 上审计、备份、清理或重置 Claude Code 与 Claude Desktop 的本机状态（缓存、日志、登录态、卸载）。不用于规避封禁或平台风控。"
---

# Claude 本机清理

使用随附脚本执行，不要临时拼接 `rm`。脚本采用窄白名单、先备份并逐项校验、一次最终知情确认和失败即停止。无法确认 Claude 进程状态（`ps` 失败）时，脚本停止且不写盘，只有 `--audit` 会报告“无法确认”。`SKILL_DIR` 指本 `SKILL.md` 所在目录的绝对路径。

## 运行顺序

1. 如果当前执行者就是 Claude Code，只运行只读审计并提醒用户切换到 Codex 或普通终端。不要让正在使用 `~/.claude` 的 Claude Code 自己修改该目录。

   ```bash
   uv run --no-project python "$SKILL_DIR/scripts/claude_cleanup.py" --audit
   ```

2. 如果由 Codex 或普通终端执行，先运行审计并向用户说明：
   - 第一个写操作是备份：`~/.claude` 存在就完整复制，`~/.claude.json` 存在就复制，不存在的项跳过（只有 Claude Desktop 数据时不受影响）；复制后逐相对路径比较文件类型、大小、sha256 摘要和符号链接目标，`~/.claude.json` 副本比较大小和 sha256，任何不一致即停止并保留未完成副本；
   - 可再生缓存和日志会自动纳入最终清单，不逐项询问；
   - 身份、钥匙串、桌面端登录态、应用和精简模式属于风险操作，仍由用户选择；
   - 所有移除只进入时间戳废纸篓目录，不会永久删除或清空废纸篓；
   - 保护路径和遥测设置保持不变。

3. 用户明确要求继续后，在真实终端运行：

   ```bash
   uv run --no-project python "$SKILL_DIR/scripts/claude_cleanup.py"
   ```

   不要用管道代答，不要增加跳过确认参数。若只有自动安全清理且 Claude 正在运行，脚本直接跳过安全目标，不要求退出；若用户选择风险操作，再交由用户正常退出并复检。脚本不能自动结束进程。

4. 脚本显示展开后的完整清单。用户输入一次 `CONFIRM` 后才开始写盘。脚本不读取、不保存开机密码；不要让用户把密码发给执行者。

5. 结束后报告备份路径、废纸篓批次、实际选择和遥测继承结果。任何中途停止都报告为部分完成，不能笼统声称清理成功。

## 自动安全清理

在 Claude Code 和 Claude Desktop 都已退出后，自动把下列现存目标纳入最终清单，无需逐项提问：

```text
~/.claude/cache
~/.claude/stats-cache.json
~/.claude/telemetry
~/.claude/usage-data
~/.claude/usage.jsonl
~/.claude/usage.with-fix.jsonl
~/Library/Caches/claude-cli-nodejs
~/Library/Caches/com.anthropic.claudefordesktop*
~/Library/Logs/Claude
~/Library/Logs/DiagnosticReports/Claude*
~/Library/Application Support/CrashReporter/Claude*
```

这些目标必须仍通过脚本白名单检查，并且只移入废纸篓。

## 绝对保护范围

绝不删除或移动：

```text
~/.claude/projects、sessions、history.jsonl、file-history、debug
~/.claude/skills、plugins、hooks、commands、scripts、agents、mcp-servers
~/.claude/backups、CLAUDE.md、settings.json、settings.local.json
任何项目目录、Git 仓库、Codex 会话，以及未明确列入白名单的路径
```

`settings.json` 只允许结构化修改被用户明确选择的键。保留其他 env、hooks、plugins、权限、模型、MCP、状态栏和秘密。目标与保护路径重叠时立即停止。移动前会解析目标的真实路径（父目录的符号链接都会展开）；真实路径落在任一受保护目录之内、与其相同或是其祖先时拒绝。目标本身是符号链接时只移动链接，不跟随。

## 风险操作

- **本地身份轮换**：轮换 `~/.claude.json` 的 `userID`、`machineID`，清除已知账号缓存字段，并把同一组新值同步到 `~/.claude/backups/.claude.json.backup.*`。仅用于隐私和排障，不宣称能改变平台关联判断。
- **钥匙串**：删除 `Claude Code-credentials` 会退出 CLI 登录，单独选择。
- **Claude Desktop**：可选择仅清持久数据与登录态，或连 `/Applications/Claude.app` 一并移入废纸篓。不能自动结束应用进程。
- **最小提示词模式**：在 `settings.json` 的 `env` 中设置或移除 `CLAUDE_CODE_SIMPLE=1`。启用后使用最小系统提示词和有限工具，并跳过 hooks、skills、plugins、MCP、自动记忆及 `CLAUDE.md` 自动发现；这些资产不会被删除。一次性脚本调用优先考虑 `claude --bare`。

## 遥测继承

逐值保存以下键：

```text
DISABLE_TELEMETRY
DISABLE_ERROR_REPORTING
CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC
```

当前关闭就保持关闭；当前未关闭就不主动关闭。改变遥测状态不属于本 skill 的清理范围。

本 skill 不用于规避封禁、支付检查、设备或 IP 信誉、浏览器指纹或任何平台风控。
