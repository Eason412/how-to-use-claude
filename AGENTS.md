# How to Use Claude 项目规则

本仓库维护三个 Agent Skill：claude-cleanup（Claude 本机清理）、proxy-setup（代理搭建与排障）和 fixed-egress（固定出口）。运行行为以各 Skill 的源码与测试为准，任务按对应 `SKILL.md` 执行。

## 工作范围

| 任务 | 入口 |
| --- | --- |
| Claude 本机清理 | [claude-cleanup](skills/claude-cleanup/SKILL.md) |
| 代理搭建、分流与排障 | [proxy-setup](skills/proxy-setup/SKILL.md) |
| 固定出口设计与验收 | [fixed-egress](skills/fixed-egress/SKILL.md) |
| 安装、导航与 CI | 根 README、`scripts/link-skills.sh` 和 `.github/workflows/` |

claude-cleanup 是独立安装单元。proxy-setup 与 fixed-egress 互相引用对方的 `references/`，作为一对安装；改动其中一方的文件名或锚点时，同步修复另一方的链接。入口为 `SKILL.md`，Codex 的显示信息放在 `agents/openai.yaml`。

本机的 `~/.codex/skills/<name>`、`~/.claude/skills/<name>` 由 `scripts/link-skills.sh` 软链到本仓库 `skills/<name>`，在本机优化 Skill 即修改本仓库；验证通过后提交并推送。

## 修改与验证

- 先检查 Git 状态，保留现有改动；只处理用户要求及其必要关联变更。
- claude-cleanup 的行为修复补充回归测试，在其目录运行 `PYTHONDONTWRITEBYTECODE=1 uv run --no-project python -m unittest discover -s tests -v`。测试使用临时 HOME，不碰真实 `~/.claude`。
- proxy-setup、fixed-egress 只有规范文本，改动检查内容、差异与相对链接。修改 Skill 规范后用 `quick_validate.py` 等校验工具检查 frontmatter；README 改动用 project-docs 的 `check_readme.py` 检查链接，中英文 README 保持一致。

## 数据与发布

使用者自己的环境定位写在不入库的 `references/environment.local.md`。IP、订单、节点、订阅 URL、凭证、账号、用量、私人路径与交接记录都不进入源码、示例或提示词；示例一律用 `SERVER_IP`、`REPLACE_WITH_...` 这类占位符。提交前用 `git grep` 检查 IP、邮箱、`/Users/` 路径和长令牌。

提交使用 GitHub noreply 邮箱。打 tag、发 Release、改名、公开和删除按用户授权执行；破坏性操作先说明具体目标及影响并等待确认。
