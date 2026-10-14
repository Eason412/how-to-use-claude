# How to Use Claude 项目规则

本仓库维护两个独立的 Agent Skill：本机清理 claude-cleanup，以及代理与固定出口 proxy，按需使用。运行行为以各 Skill 的源码与测试为准，任务按对应 `SKILL.md` 执行。

## 工作范围

| 任务 | 入口 |
| --- | --- |
| Claude 本机清理 | [claude-cleanup](skills/claude-cleanup/SKILL.md) |
| 搭建 VPS、协议、客户端、分流与固定出口 | [proxy 搭建与改造](skills/proxy/SKILL.md#搭建与改造) |
| 维护已在用的链路 | [proxy 维护与排障](skills/proxy/SKILL.md#维护与排障) |
| 安装、导航与 CI | 根 README（给使用者，讲效果）、`SETUP.md`（给 Agent，讲安装步骤）、`scripts/link-skills.sh` 和 `.github/workflows/` |

claude-cleanup 与 proxy 各自是完整安装单元。proxy 内分搭建与改造、维护与排障两组：搭建管“从无到可用”与结构性改动（新建、换入口、换协议、重做链路），维护管已在用链路的日常事务；新增内容按这条分界放，不重复正文。入口为 `SKILL.md`，Codex 的显示信息放在 `agents/openai.yaml`。

本机的 `~/.codex/skills/<name>`、`~/.claude/skills/<name>` 由 `scripts/link-skills.sh` 软链到本仓库 `skills/<name>`，在本机优化 Skill 即修改本仓库；验证通过后提交并推送。

## 修改与验证

- 先检查 Git 状态，保留现有改动；只处理用户要求及其必要关联变更。
- claude-cleanup 的行为修复补充回归测试；新增清理目标或键时，先用安装版本的 `--help` 与官方文档核对名称，在其目录运行 `PYTHONDONTWRITEBYTECODE=1 uv run --no-project python -m unittest discover -s tests -v`。测试使用临时 HOME，不碰真实 `~/.claude`。
- proxy 只有规范文本，改动检查内容、差异与相对链接。修改 Skill 规范后用 `quick_validate.py` 等校验工具检查 frontmatter；README 只有中文版，改动用 project-docs 的 `check_readme.py --file README.md` 检查链接；Skill 的效果、档位或安装方式变化时，同步 README 与 `SETUP.md`。

## 数据与发布

使用者自己的环境定位写在不入库的 `references/environment.local.md`。IP、订单、节点、订阅 URL、凭证、账号、用量、私人路径与交接记录都不进入源码、示例或提示词；示例一律用 `SERVER_IP`、`REPLACE_WITH_...` 这类占位符。提交前用 `git grep` 检查 IP、邮箱、`/Users/` 路径和长令牌。

提交使用 GitHub noreply 邮箱。打 tag、发 Release、改名、公开和删除按用户授权执行；破坏性操作先说明具体目标及影响并等待确认。
