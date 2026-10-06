---
name: claude-cleanup
description: "在 macOS 上分档清理 Claude Code 与 Claude Desktop 的本机隐私痕迹：关上报、清设备标识、登出并清本地会话、清缓存日志与桌面端数据。不用于规避封禁或平台风控。"
---

# Claude 本机清理

三步中的第一步：先清理，再按 proxy-setup 搭建，最后按 proxy-maintenance 维护。

使用随附脚本执行，不要临时拼接 `rm`。脚本采用窄白名单、先完整备份并逐项校验、一次最终知情确认和失败即停止。`SKILL_DIR` 指本 `SKILL.md` 所在目录的绝对路径。能做什么、不能做什么，以及各开关的含义，读 [隐私范围与数据地图](references/privacy.md)。

## 输出纪律

令牌、邮箱、`userID`／`machineID` 等标识的值、提示词与会话正文、`claude auth status` 的完整输出，一律不打印、不贴进对话、不写进提交或文档。审计只报告“有／无”和数量；登录状态只转述 `loggedIn` 与 `authMethod`。

## 选档

档位逐级包含，按用户目标选最低够用的一档：

| 档位 | 做什么 | 登录 | 会话与历史 |
|---|---|---|---|
| 0 只清缓存 | 可再生缓存和日志移入废纸篓 | 保留 | 保留 |
| 1 关上报 | 再合并写入用户级隐私开关 | 保留 | 保留 |
| 2 清设备标识 | 再删除设备标识与实验缓存键、带旧身份的 backups 快照、会话边角料（history.jsonl、sessions、file-history 等） | 保留 | 项目会话保留，输入历史与文件回滚记录移走 |
| 3 登出并清会话 | 再 `claude auth logout`、`claude purge --all`、删除钥匙串凭证与 `.credentials.json`；可选清 CC Switch 的 Claude 用量行 | 退出 | 全部项目会话删除，memory/ 默认从备份恢复 |

档位 1 起会改变遥测设置；总开关 `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` 会连带停掉自动更新和安全补丁，脚本单独询问，默认不开。会话保留天数默认不动，用户要求时才设置。

## 运行顺序

1. 当前执行者是 Claude Code 时，只运行只读审计，并提醒用户换到 Codex 或普通终端执行写操作；不要让正在使用 `~/.claude` 的 Claude Code 修改它。

   ```bash
   uv run --no-project python "$SKILL_DIR/scripts/claude_cleanup.py" --audit
   ```

2. 由 Codex 或普通终端执行时，先运行审计，按上表说明各档影响，确认用户要哪一档。说明以下几点：
   - 第一个写操作是完整备份 Claude 配置目录与 `.claude.json`（选清 CC Switch 时另备份其数据库），逐相对路径比较类型、大小、sha256 和符号链接目标，不一致即停止。备份放在用户指定位置（默认桌面）下的 `Claude清理包` 文件夹，全部步骤完成后打成 `Claude清理包-时间.tar.gz`（0600，保留符号链接），读回逐项比对一致才删掉未打包的目录；中途停止时保留目录供恢复。位置开了 iCloud“桌面与文稿”同步时脚本会提示，压缩包会被上传；
   - 文件只进时间戳废纸篓目录；`claude purge` 与钥匙串删除不经过废纸篓，只能靠备份恢复；
   - 档位 1 起要求先正常退出所有 Claude Code / Claude Desktop，脚本不结束进程；只清缓存且 Claude 正在运行时，缓存目标直接跳过，不要求退出；
   - 无法确认 Claude 进程状态（`ps` 失败）时脚本停止且不写盘，只有 `--audit` 会报告“无法确认”。

3. 用户明确要求继续后，在真实终端运行，不要用管道代答或增加跳过确认的参数：

   ```bash
   uv run --no-project python "$SKILL_DIR/scripts/claude_cleanup.py"
   ```

4. 脚本展示展开后的完整清单，用户输入一次 `CONFIRM` 才写盘。脚本不读取、不保存开机密码；不要让用户把密码发给执行者。

5. 脚本结束时在终端打印“已完成清理”，并弹出同名对话框（可在访达中显示清理包；SSH 等无图形界面时跳过）。执行者随后报告清理包路径、废纸篓批次、实际档位与选择、复查结果（身份键是否已无、登录状态两项）。中途停止一律报告为部分完成。

   然后请用户再确认一次：新开 Claude Code，确认登录状态符合所选档位、技能和 hooks 仍在。用户确认正常后，提醒删除清理包并清空废纸篓，清理才算彻底；清理包和废纸篓里仍有旧身份、账号和会话。档位 3 的 purge 和钥匙串删除不经过废纸篓，清理包删掉后就无法恢复。执行者不代删。

6. 提醒脚本做不到的部分：新开 Claude Code 让开关生效；到 claude.ai 数据隐私设置关闭 “Help Improve our AI models”；档位 3 还要在 Settings → Claude Code 吊销本机 token，共享设备按需登出全部会话。执行者不代登网页账号。

## 自动清理的缓存与日志

档位 0 起自动纳入，仍须通过白名单检查，只移入废纸篓：

```text
~/.claude/cache、stats-cache.json、telemetry、usage-data、usage.jsonl、usage.with-fix.jsonl
~/Library/Caches/claude-cli-nodejs、com.anthropic.claudefordesktop*
~/Library/Logs/Claude、DiagnosticReports/Claude*
~/Library/Application Support/CrashReporter/Claude*
```

## 始终保护

```text
skills、plugins、hooks、commands、scripts、agents、mcp-servers、plans、todos
backups 目录本身（档位 2 起只移走其中的 .claude.json 快照）
CLAUDE.md、settings.json 与 settings.local.json 中本次未选择的键
任何项目目录、Git 仓库、Codex 登录与会话、CC Switch 的供应商、端点与 Key
```

`projects`、`tasks` 只由 `claude purge`（档位 3）处理，不经脚本移动。`settings.json` 只合并写入所选键，保留其他 env、hooks、权限、模型、MCP、状态栏和秘密。移动前解析目标真实路径（父目录符号链接都会展开），落在受保护目录之内、与其相同或是其祖先时拒绝；目标本身是符号链接时只移动链接。

## 其他选项

- **Claude Desktop**：可只清持久数据与登录态，或连 `/Applications/Claude.app` 一并移入废纸篓。
- **最小提示词模式**：在 `settings.json` 的 `env` 中设置或移除 `CLAUDE_CODE_SIMPLE=1`；启用后跳过 hooks、skills、plugins、MCP、自动记忆及 `CLAUDE.md` 发现，这些资产不会被删除。一次性脚本调用优先考虑 `claude --bare`。

## 平台

脚本只支持 macOS。Linux 与 Windows 的凭证位置和手动步骤见 [隐私范围与数据地图](references/privacy.md#凭证位置)，按其中的布尔探测与删除顺序人工执行。

本 skill 不用于规避封禁、支付检查、设备或 IP 信誉、浏览器指纹或任何平台风控。
