# How to Use Claude

[中文](README.md) | English

**Keep Claude's local state clean and its connection stable.** This repository holds three Agent Skills: cleaning Claude's local state, setting up and maintaining proxies, and keeping chosen apps on a fixed final egress. Each Skill starts at `SKILL.md` and is carried out by an agent such as Codex or Claude Code. The Skill texts are written in Chinese.

> ⚠️ These Skills are not for evading bans, payment checks, device or IP reputation, browser fingerprinting or any platform risk control. A fixed egress does not guarantee any account outcome.

## 🧩 Skills

| Skill | Purpose | References |
| --- | --- | --- |
| [claude-cleanup](skills/claude-cleanup/SKILL.md) | Audit, back up, clean or reset Claude Code and Claude Desktop local state on macOS: caches, logs, sign-in state, uninstall | [Cleanup script](skills/claude-cleanup/scripts/claude_cleanup.py) |
| [proxy-setup](skills/proxy-setup/SKILL.md) | Build and maintain VPS proxies, import subscriptions, configure routing and usage stats, check DNS/WebRTC leaks, troubleshoot connectivity and speed | [Setup](skills/proxy-setup/references/setup.md), [Troubleshooting](skills/proxy-setup/references/troubleshooting.md) |
| [fixed-egress](skills/fixed-egress/SKILL.md) | Design, migrate and verify a fixed final egress for chosen apps or traffic: proxy chains, entry replacement, failure isolation | [Chain policy](skills/fixed-egress/references/chain-policy.md), [Validation](skills/fixed-egress/references/validation.md) |

claude-cleanup can be installed on its own. proxy-setup and fixed-egress work as a pair: the first covers resources, deployment and routine maintenance, the second covers fixed-egress design and verification. They link to each other's references, so install both.

## 🛠️ Requirements

| Feature | Dependencies |
| --- | --- |
| claude-cleanup | macOS, uv, Python ≥ 3.10; standard library only |
| proxy-setup, fixed-egress | An agent that can read Markdown references; clients (Clash Verge/Mihomo, Shadowrocket, etc.), a VPS and SSH as the task requires |

## 🚀 Install

```sh
git clone https://github.com/Eason412/how-to-use-claude.git
cd how-to-use-claude
scripts/link-skills.sh
```

Add `--dry-run` to preview first. The script symlinks every Skill under `skills/` into `~/.codex/skills` and `~/.claude/skills`. An existing real directory with the same name is first moved to a sibling `skills-backup/`. Start a new agent session afterwards.

When proxy-setup looks for your own environment records, it reads the untracked `references/environment.local.md` next to it. Put links to your private handoff or operations notes there; see [Project entry](skills/proxy-setup/references/environment.md).

## 📁 Maintenance

Editing and verification rules are in [AGENTS.md](AGENTS.md). Regression tests for claude-cleanup:

```sh
cd skills/claude-cleanup
PYTHONDONTWRITEBYTECODE=1 uv run --no-project python -m unittest discover -s tests -v
```

## 📄 License

[MIT](LICENSE)
