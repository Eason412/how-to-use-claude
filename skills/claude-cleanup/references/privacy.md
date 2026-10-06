# 隐私范围与数据地图

字段和开关以安装版本为准；本页写法按 Claude Code 2.1 核对，新版本先用 `--help` 和官方文档复核。处理原则是“字段存在就处理”，不假设固定的 JSON 骨架。

## 能停什么、不能停什么

“少给隐私”指关掉非必要上报、清本地身份和会话，不等于官方收不到你的输入。

| 想停的 | 本机能否做到 | 说明 |
|---|---|---|
| 用量遥测、错误上报、问卷、特性开关拉取 | 能 | 用户级 `settings.json` 的 env 开关 |
| 本机 `userID`／`machineID` 把多次使用串成同一设备 | 能 | 删除键后下次启动重新生成；仍登录时用量照样记在该账号 |
| 官方 OAuth 登录（邮箱、令牌、组织信息） | 能 | `claude auth logout` 后再扫残留 |
| 发给官方后端的对话内容 | 不能 | 提示词就是请求本身 |
| 发给第三方中转或自建网关的内容 | 本机关不掉 | 内容去往 `ANTHROPIC_BASE_URL` 指向的一端，按其政策 |
| 请求里由仓库 remote 算出的短哈希 | 不能 | 每次请求现算 |
| claude.ai 上的云端记录 | 本机清不掉 | 到网页隐私设置与账号页处理 |

## 隐私开关（档位 1）

写在用户级 `~/.claude/settings.json` 的 `env`，不写进会提交到 Git 的项目级 `.claude/settings.json`。合并写入，保留已有键。

| 键 | 作用 |
|---|---|
| `DISABLE_TELEMETRY` | 停用量遥测 |
| `DISABLE_ERROR_REPORTING` | 停错误上报 |
| `DISABLE_BUG_COMMAND` | 停 `/bug` |
| `DO_NOT_TRACK` | 连带停问卷等 |
| `CLAUDE_CODE_DISABLE_OFFICIAL_MARKETPLACE_AUTOINSTALL` | 不自动安装官方市场插件 |
| `feedbackSurveyRate: 0` | 不再弹会话质量问卷 |
| `skipWebFetchPreflight: true` | WebFetch 前不再把目标域名发给官方预检 |
| `cleanupPeriodDays` | 本地会话保留天数（默认 30，最小 1）；会自动删除更早的会话，用户要求才设 |
| `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` | 总开关：等价于上面几项再加停自动更新、发版检查和其他非必要出站；要安全补丁时不用 |

这些开关“设了非空值即生效”，写成 `"0"` 仍是开启；恢复时删除该键。改完必须新开 Claude Code。

## 本地数据地图

`~` 在 macOS／Linux 是 `$HOME`，Windows 是 `%USERPROFILE%`。设置了 `CLAUDE_CONFIG_DIR` 时，配置根改为该目录，`.claude.json` 与凭证文件也随之移动，macOS 钥匙串条目名也会带上区分后缀。

| 路径 | 内容 | 档位 |
|---|---|---|
| `~/.claude.json` | 设备标识、账号块 `oauthAccount`、项目信任项、实验缓存 | 2 删标识与缓存键；3 再删账号块 |
| `~/.claude/backups/.claude.json.backup*` | 滚动快照，含旧标识和账号 | 2 移走 |
| `~/.claude/settings.json` | 模型、主题、env 开关 | 1 合并写入；不整文件删除 |
| `~/.claude/history.jsonl` | 输入过的全部提示词 | 2 移走（失去 Ctrl+R 历史） |
| `~/.claude/sessions`、`session-env`、`paste-cache`、`shell-snapshots`、`statsig`、`debug`、`file-history` | 会话边角料、特性开关设备 ID、文件回滚记录 | 2 移走 |
| `~/.claude/projects/` | 会话记录、工具结果、memory/ | 3 由 `claude purge` 删除 |
| `~/.claude/.credentials.json`、`mcp-needs-auth-cache.json` | 凭证落盘回退、MCP 授权缓存 | 3 移走 |
| `~/.claude/skills`、`hooks`、`plugins` 等 | 用户资产 | 始终保留 |

删除身份键时删整个键，不改成空字符串。清除的键：`userID`、`anonymousId`、`machineID`、`remoteControlMachineId`、`firstStartTime`、`claudeCodeFirstTokenDate`，以及 `cachedGrowthBookFeatures`、`cachedExperimentFeatures`、`cachedExperimentData`、`metricsStatusCache`、`clientDataCacheSlots`、`groveConfigCache`、`passesEligibilityCache` 等缓存键。项目条目里的 `last*` 用量统计可选清除；`allowedTools` 和信任状态保留，否则每个目录会再问一次。

## 凭证位置

| 系统 | 位置 | 处理 |
|---|---|---|
| macOS | 钥匙串，常见条目 `Claude Code-credentials`（自定义配置根时带后缀）；钥匙串锁定（如 SSH 会话）时回退写到 `~/.claude/.credentials.json` | 脚本按条目名列出并删除全部匹配项，再移走回退文件 |
| Linux | `~/.claude/.credentials.json`（0600） | `claude auth logout` 后确认文件不存在或已无 `claudeAiOauth` |
| Windows | `%USERPROFILE%\.claude\.credentials.json` | 同 Linux；凭据管理器（`cmdkey /list`）通常没有官方 OAuth 条目，不按 macOS 步骤去空找 |

Linux／Windows 手动执行时，先只读探测键是否存在（只输出布尔），例如：

```bash
jq '{has_userID: has("userID"), has_machineID: has("machineID"), has_oauth: has("oauthAccount")}' ~/.claude.json
```

```powershell
$j = Get-Content (Join-Path $env:USERPROFILE '.claude.json') -Raw | ConvertFrom-Json
[pscustomobject]@{ has_userID = [bool]$j.PSObject.Properties['userID']; has_oauth = [bool]$j.PSObject.Properties['oauthAccount'] }
```

再按档位顺序：备份 → 写隐私开关 → `claude auth logout` → `claude purge --all` → 删身份键与快照 → 删凭证文件 → `claude auth status` 复查。Windows 另有 `%LOCALAPPDATA%\claude-cli-nodejs\Cache\`，可按缓存处理。

## 登出与 purge（档位 3）

`claude auth logout` 移除令牌与 `oauthAccount`，并重置首次启动状态。`claude purge --all`（旧版本为 `claude project purge --all`）删除全部项目会话与 memory/、`tasks`、`debug`、`file-history`，以及 `.claude.json` 中所有项目信任项；技能和 hooks 不受影响。

登出后复查：`.claude.json` 不再有 `oauthAccount`、`userID`、`machineID`；凭证文件与钥匙串条目已无；`claude auth status` 为 `loggedIn=false`、`authMethod=none`。仍有旧 `claude` 进程时先退出，否则它可能把登录态写回文件。本机登出不等于服务端立刻作废令牌，还要到网页端吊销。

## 供应商切换器

以 CC Switch 为例，原则同样适用于其他切换器：官方 Claude 登录态不在切换器数据库里，第三方 Key 在。

- 切换器的“官方登录”槽位通常只表示“不写 `ANTHROPIC_AUTH_TOKEN`、走官方 OAuth”，没有令牌。切回官方时先 `claude auth logout` 再 `claude auth login`。
- 可删：由本机 Claude 会话解析出的用量行（`proxy_request_logs`、`usage_daily_rollups` 中 `app_type='claude'`，`session_log_sync` 中指向 `.claude` 的记录）。官方与第三方用量在这里分不开，会话已 purge 后只剩脏索引。
- 不动：`providers`、`provider_endpoints`、通用配置片段、Codex／Gemini 等其他产品的表和用量、切换器自己的 backups（含 API Key）。表名随版本变化，先看结构再删；脚本遇到不存在的表或列直接跳过。
- 切换器运行时可能把当前供应商配置回写进 `settings.json`。写完隐私开关后到切换器的通用配置里核对 env 仍在。

Codex 是另一套登录：`~/.codex/auth.json`，以及切换器中官方 Codex 槽位里的令牌。清 Claude 时不动它们。

## 网页端

1. [数据隐私设置](https://claude.ai/settings/data-privacy-controls)：关闭 “Help Improve our AI models”。
2. [Settings → Claude Code](https://claude.ai/settings)：吊销不用的本机令牌；[账号页](https://claude.ai/settings/account) 可登出全部会话。

## 常见误区

- 只改当前 `.claude.json` 不够，backups 快照、本脚本的清理包（`Claude清理包-时间.tar.gz`）和废纸篓里都还有旧身份；确认无误后删除清理包并清空废纸篓。
- 备份放在开了 iCloud“桌面与文稿”同步的桌面时，会连同凭证信息上传到 iCloud；这种情况换一个本地位置。
- 不要 `rm -rf ~/.claude`：技能、hooks 和隐私开关会一起丢失。
- 不要把整份 `.claude.json` 或 `claude auth status` 输出贴到公开位置。
- purge 会删除 memory/；需要保留时先备份，脚本默认从备份恢复。

## 参考

- [环境变量](https://code.claude.com/docs/en/env-vars)、[设置项](https://code.claude.com/docs/en/settings-reference)、[数据使用](https://code.claude.com/docs/en/data-usage)、[认证与凭证](https://code.claude.com/docs/en/authentication)
- [登出全部会话](https://support.claude.com/en/articles/10310342-how-do-i-log-out-of-all-active-sessions)
- [CC Switch](https://github.com/farion1231/cc-switch)
