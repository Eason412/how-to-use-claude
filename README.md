# How to Use Claude

中文 | [English](README.en.md)

**让 Claude 在本机用得干净、连得稳定。** 本仓库收录三个 Agent Skill：清理 Claude 的本机状态，搭建和维护代理，以及让指定应用保持固定的最终出口。每个 Skill 以 `SKILL.md` 为入口，由 Codex、Claude Code 等 Agent 按规范执行。

> ⚠️ 这些 Skill 不用于规避封禁、支付检查、设备或 IP 信誉、浏览器指纹或任何平台风控；固定出口也不保证账号结果。

## 🧩 Skill 组成

| Skill | 用途 | 配套资料 |
| --- | --- | --- |
| [claude-cleanup](skills/claude-cleanup/SKILL.md) | 在 macOS 上审计、备份、清理或重置 Claude Code 与 Claude Desktop 的本机状态：缓存、日志、登录态、卸载 | [清理脚本](skills/claude-cleanup/scripts/claude_cleanup.py) |
| [proxy-setup](skills/proxy-setup/SKILL.md) | 建立和维护 VPS 代理，导入订阅，配置分流与流量统计，检查 DNS／WebRTC 泄露，排查连接和速度 | [搭建流程](skills/proxy-setup/references/setup.md)、[分层排查](skills/proxy-setup/references/troubleshooting.md) |
| [fixed-egress](skills/fixed-egress/SKILL.md) | 设计、迁移和验收指定应用或流量的固定最终出口：链式代理、入口替换、失败隔离 | [链路与边界](skills/fixed-egress/references/chain-policy.md)、[验证与迁移](skills/fixed-egress/references/validation.md) |

claude-cleanup 可单独安装。proxy-setup 与 fixed-egress 是一对：前者负责资源、部署与日常维护，后者负责固定出口的设计和验收，二者互相引用对方的参考资料，需要一起安装。

## 🛠️ 运行条件

| 功能 | 依赖 |
| --- | --- |
| claude-cleanup | macOS、uv、Python ≥ 3.10；只用标准库 |
| proxy-setup、fixed-egress | Agent 能读取 Markdown 参考资料；实际操作所需的客户端（Clash Verge／Mihomo、Shadowrocket 等）、VPS 与 SSH 按任务准备 |

## 🚀 安装

```sh
git clone https://github.com/Eason412/how-to-use-claude.git
cd how-to-use-claude
scripts/link-skills.sh
```

可先加 `--dry-run` 预览。脚本把 `skills/` 下每个 Skill 软链到 `~/.codex/skills` 与 `~/.claude/skills`；目标位置已有同名真实目录时先移到同级的 `skills-backup/`。完成后开启新的 Agent 会话。

proxy-setup 读取使用者自己的环境记录时，查找同目录下不入库的 `references/environment.local.md`，在其中写指向私有交接或运维文档的链接即可，见 [项目入口](skills/proxy-setup/references/environment.md)。

## 📁 维护

修改与验证规则见 [AGENTS.md](AGENTS.md)。claude-cleanup 的回归测试：

```sh
cd skills/claude-cleanup
PYTHONDONTWRITEBYTECODE=1 uv run --no-project python -m unittest discover -s tests -v
```

## 📄 许可证

[MIT](LICENSE)
