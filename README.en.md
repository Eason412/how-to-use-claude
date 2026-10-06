# How to Use Claude

[中文](README.md) | English

**Keep Claude's local state clean and its connection stable.** This repository holds three Agent Skills in the order you use them: clean up first, then set up, then maintain. Each Skill starts at `SKILL.md` and is carried out by an agent such as Codex or Claude Code. The Skill texts are written in Chinese.

> ⚠️ These Skills are not for evading bans, payment checks, device or IP reputation, browser fingerprinting or any platform risk control. A fixed egress does not guarantee any account outcome.

## 🧭 Three steps

| Step | Skill | What it does | References |
| --- | --- | --- | --- |
| 1. Clean up | [claude-cleanup](skills/claude-cleanup/SKILL.md) | Clean Claude's local privacy traces on macOS at four levels: caches only, turn off reporting, clear device identifiers (stay signed in), sign out and clear local sessions | [Privacy scope and data map](skills/claude-cleanup/references/privacy.md), [Cleanup script](skills/claude-cleanup/scripts/claude_cleanup.py) |
| 2. Set up | [proxy-setup](skills/proxy-setup/SKILL.md) | Build a VPS and fixed egress from scratch: buy a VPS, deploy a protocol, import clients, design routing and the fixed-egress chain, first verification; also for replacing an entry or rebuilding a chain | [Setup](skills/proxy-setup/references/setup.md), [Fixed-egress chain](skills/proxy-setup/references/egress-chain.md) |
| 3. Maintain | [proxy-maintenance](skills/proxy-maintenance/SKILL.md) | Maintain a chain already in use: subscription updates, troubleshooting and performance comparison, leak checks, usage card, renewals and billing, SSH source changes, client upgrade failures | [Troubleshooting](skills/proxy-maintenance/references/troubleshooting.md), [Connection safety](skills/proxy-maintenance/references/connection-safety.md) |

Setup covers getting from nothing to working plus structural changes; maintenance covers chains already in use. Each `SKILL.md` states the boundary at the top. claude-cleanup can be installed on its own; proxy-setup and proxy-maintenance link to each other's references, so install both.

## 🛠️ Requirements

| Feature | Dependencies |
| --- | --- |
| claude-cleanup | macOS, uv, Python ≥ 3.10; standard library only |
| proxy-setup, proxy-maintenance | An agent that can read Markdown references; clients (Clash Verge/Mihomo, Shadowrocket, etc.), a VPS and SSH as the task requires |

## 🚀 Install

```sh
git clone https://github.com/Eason412/how-to-use-claude.git
cd how-to-use-claude
scripts/link-skills.sh
```

Add `--dry-run` to preview first. The script symlinks every Skill under `skills/` into `~/.codex/skills` and `~/.claude/skills`. An existing real directory with the same name is first moved to a sibling `skills-backup/`. Start a new agent session afterwards.

When proxy-maintenance looks for your own environment records, it reads the untracked `references/environment.local.md` next to it. Put links to your private handoff or operations notes there; see [Project entry](skills/proxy-maintenance/references/environment.md).

## 📁 Maintenance

Editing and verification rules are in [AGENTS.md](AGENTS.md). Regression tests for claude-cleanup:

```sh
cd skills/claude-cleanup
PYTHONDONTWRITEBYTECODE=1 uv run --no-project python -m unittest discover -s tests -v
```

## 📄 License

[MIT](LICENSE)
