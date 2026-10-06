# How to Use Claude

中文 | [English](README.en.md)

**让 Claude 在本机用得干净、连得稳定。** 本仓库按使用顺序收录三个 Agent Skill，对应三步：先清理，再搭建，后维护。每个 Skill 以 `SKILL.md` 为入口，由 Codex、Claude Code 等 Agent 按规范执行。

> ⚠️ 这些 Skill 不用于规避封禁、支付检查、设备或 IP 信誉、浏览器指纹或任何平台风控；固定出口也不保证账号结果。

## 🧭 三步

| 步骤 | Skill | 做什么 | 配套资料 |
| --- | --- | --- | --- |
| 一、清理 | [claude-cleanup](skills/claude-cleanup/SKILL.md) | 在 macOS 上分四档清理 Claude 本机隐私痕迹：只清缓存，关上报，清设备标识（保留登录），登出并清本地会话 | [隐私范围与数据地图](skills/claude-cleanup/references/privacy.md)、[清理脚本](skills/claude-cleanup/scripts/claude_cleanup.py) |
| 二、搭建 | [proxy-setup](skills/proxy-setup/SKILL.md) | 从零搭建 VPS 与固定出口：选购 VPS、部署协议、导入客户端、设计分流与固定出口链路、首次验收；换入口或重做链路也在这里 | [搭建流程](skills/proxy-setup/references/setup.md)、[固定出口链路](skills/proxy-setup/references/egress-chain.md) |
| 三、维护 | [proxy-maintenance](skills/proxy-maintenance/SKILL.md) | 维护已在用的链路：订阅更新、排障与性能对照、泄露检查、用量卡片、续费与账单、SSH 来源变化、客户端升级故障 | [分层排查](skills/proxy-maintenance/references/troubleshooting.md)、[连接保护](skills/proxy-maintenance/references/connection-safety.md) |

搭建只管“从无到可用”和结构性改动，维护只管已在用的链路，二者的分界写在各自 `SKILL.md` 开头。claude-cleanup 可单独安装；proxy-setup 与 proxy-maintenance 互相引用对方的参考资料，需要一起安装。

## 🛠️ 运行条件

| 功能 | 依赖 |
| --- | --- |
| claude-cleanup | macOS、uv、Python ≥ 3.10；只用标准库 |
| proxy-setup、proxy-maintenance | Agent 能读取 Markdown 参考资料；实际操作所需的客户端（Clash Verge／Mihomo、Shadowrocket 等）、VPS 与 SSH 按任务准备 |

## 🚀 安装

```sh
git clone https://github.com/Eason412/how-to-use-claude.git
cd how-to-use-claude
scripts/link-skills.sh
```

可先加 `--dry-run` 预览。脚本把 `skills/` 下每个 Skill 软链到 `~/.codex/skills` 与 `~/.claude/skills`；目标位置已有同名真实目录时先移到同级的 `skills-backup/`。完成后开启新的 Agent 会话。

proxy-maintenance 读取使用者自己的环境记录时，查找同目录下不入库的 `references/environment.local.md`，在其中写指向私有交接或运维文档的链接即可，见 [项目入口](skills/proxy-maintenance/references/environment.md)。

## 📁 维护

修改与验证规则见 [AGENTS.md](AGENTS.md)。claude-cleanup 的回归测试：

```sh
cd skills/claude-cleanup
PYTHONDONTWRITEBYTECODE=1 uv run --no-project python -m unittest discover -s tests -v
```

## 📄 许可证

[MIT](LICENSE)
