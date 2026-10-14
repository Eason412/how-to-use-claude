---
name: claude-cleanup
description: "在 macOS 上分档清理 Claude Code 与 Claude Desktop 的本机隐私痕迹：关上报、清设备标识、登出并清本地会话、清缓存日志与桌面端数据。不用于规避封禁或平台风控。"
---

# Claude 本机清理

使用随附脚本，不临时拼接删除命令。`SKILL_DIR` 为本文件所在目录的绝对路径；各档范围见 [隐私范围与数据地图](references/privacy.md)。

## 输出纪律

令牌、邮箱、`userID`／`machineID` 等标识的值、提示词与会话正文、`claude auth status` 的完整输出，一律不打印、不贴进对话、不写进提交或文档。审计只报告“有／无”和数量；登录状态只转述 `loggedIn` 与 `authMethod`。

## 选档

档位逐级包含，默认推荐档位 3；用户要保留登录时选 2 或更低：

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

2. 由 Codex 或普通终端执行时，先审计，说明推荐档位与以下影响，再由用户在脚本中选档并最终确认：
   - 首个写操作备份配置目录与 `.claude.json`，选清 CC Switch 时另备份数据库；校验通过才清理。备份放在指定位置（默认桌面）的 `Claude清理包` 文件夹，完成后打成 `Claude清理包-时间.tar.gz`（0600，保留符号链接），读回校验通过才删未打包副本；中断保留恢复目录。默认位置可能受 iCloud“桌面与文稿”同步，连同凭证信息上传；这种情况换一个本地位置；
   - 文件只进时间戳废纸篓目录；`claude purge` 与钥匙串删除不经废纸篓。项目会话可从清理包恢复；钥匙串凭证不备份，删除后需重新登录；
   - 档位 1 起要求先正常退出所有 Claude Code / Claude Desktop，脚本不结束进程；只清缓存且 Claude 正在运行时，缓存目标直接跳过，不要求退出；
   - 无法确认 Claude 进程状态（`ps` 失败）时脚本停止且不写盘，只有 `--audit` 会报告“无法确认”。

3. 在真实终端运行，不用管道代答或跳过确认：

   ```bash
   uv run --no-project python "$SKILL_DIR/scripts/claude_cleanup.py"
   ```

4. 脚本展示展开后的完整清单，用户输入一次 `CONFIRM` 才写盘。脚本不读取、不保存开机密码；不要让用户把密码发给执行者。

5. 执行者报告清理包路径、废纸篓批次、实际档位与选择、复查结果（身份键是否已无、登录状态两项；档位 3 选保留 memory 时含脚本报告的恢复目录数）。中途停止一律报告为部分完成。清理包落在 iCloud“桌面与文稿”同步范围内时，提醒删除后还要到 iCloud.com 的“最近删除”中彻底删除。

   然后请用户再确认一次：新开 Claude Code，确认登录状态符合所选档位、技能和 hooks 仍在，选了保留时各项目 memory 也在。用户确认正常后，提醒删除清理包并清空废纸篓，清理才算彻底；其中仍有旧身份、账号和会话，清理包删掉后项目会话无法从中恢复。钥匙串凭证不备份，删除后需重新登录。执行者不代删。

6. 新开 Claude Code 使设置生效；按 [网页端](references/privacy.md#网页端) 完成隐私设置及档位 3 的令牌吊销。执行者不代登网页账号。

## 自动清理的缓存与日志

档位 0 起自动纳入可再生缓存和日志，仍经白名单，仅移入废纸篓；路径见 [本地数据地图](references/privacy.md#本地数据地图)。

## 始终保护

```text
skills、plugins、hooks、commands、scripts、agents、mcp-servers、plans、todos
backups 目录本身（档位 2 起只移走其中的 .claude.json 快照）
CLAUDE.md、settings.json 与 settings.local.json 中本次未选择的键
任何项目目录、Git 仓库、Codex 登录与会话、CC Switch 的供应商、端点与 Key
```

不整删 `settings.json`，只合并所选键并保护上述用户资产；`projects`、`tasks` 只由档位 3 的 `claude purge` 处理，不经脚本移动。路径保护见 [本地数据地图](references/privacy.md#本地数据地图)。

## 其他选项

- **Claude Desktop**：可只清持久数据与登录态，或连 `/Applications/Claude.app` 一并移入废纸篓。
- **最小提示词模式**：在 `settings.json` 的 `env` 中设置或移除 `CLAUDE_CODE_SIMPLE=1`；启用后跳过 hooks、skills、plugins、MCP、自动记忆及 `CLAUDE.md` 发现，这些资产不会被删除。

## 平台

脚本只支持 macOS。Linux 与 Windows 的凭证位置和手动步骤见 [隐私范围与数据地图](references/privacy.md#凭证位置)，按其中的布尔探测与删除顺序人工执行。
