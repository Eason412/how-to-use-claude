# How to Use Claude

[中文](README.md) | English

**Fewer local traces, a connection you control.** Three Agent Skills, in the order you use them: clean up the privacy traces Claude leaves on your computer, set up your own VPS and fixed egress, then let an agent maintain that chain. A Skill is an operating spec for agents such as Codex or Claude Code; hand it to the agent and it carries out the work. The Skill texts are written in Chinese.

> ⚠️ These Skills are not for evading bans, payment checks, device or IP reputation, browser fingerprinting or any platform risk control. A fixed egress does not guarantee any account outcome.

- **Fixed egress**: the final IP a target website sees. Chosen apps or domains always leave through the same egress; if it fails, connections are refused instead of quietly switching to another IP.
- **VPS**: a cloud server you rent to run the proxy service.

## 🧭 Three steps

| Step | Skill | Effect |
| --- | --- | --- |
| 1. Clean up | [claude-cleanup](skills/claude-cleanup/SKILL.md) | Claude's local reporting, device identifiers and sessions are cleared to the chosen level |
| 2. Set up | [proxy-setup](skills/proxy-setup/SKILL.md) | A working proxy and fixed-egress chain, starting from nothing |
| 3. Maintain | [proxy-maintenance](skills/proxy-maintenance/SKILL.md) | The chain in use keeps working as agreed at setup |

## 🧹 1. Clean up: claude-cleanup

Cleans the privacy traces Claude Code and Claude Desktop leave on macOS. Pick one level; each level includes the ones before it:

| Level | Effect | Sign-in |
| --- | --- | --- |
| 0 Caches only | Caches, logs and crash reports go to the Trash | Kept |
| 1 Stop reporting | Also turns off telemetry, error reports, surveys and the WebFetch domain preflight | Kept |
| 2 Clear device IDs | Also deletes device identifiers, experiment caches, old identity snapshots and prompt history | Kept |
| 3 Sign out and clear sessions | Also signs out and deletes local sessions and the Keychain credentials | Signed out |

- **Backup first**: the first write is a full backup, verified file by file. At the end it is packed into `Claude清理包-<time>.tar.gz` ("Claude cleanup pack"), on the Desktop by default or in a folder you choose. If that folder is synced by iCloud Desktop & Documents, a reminder appears before confirmation and again at the end.
- **Reversible**: files only move to the Trash. Level 3 session purge and Keychain removal are the exception; they can only be restored from the cleanup pack.
- **Personal assets kept**: skills, hooks, plugins, `CLAUDE.md`, unselected settings keys, project folders and Codex data always stay; project memory is restored from the backup by default.
- **One confirmation, a completion notice**: nothing is written until you review the full list and type `CONFIRM` once. A "cleanup complete" dialog appears at the end and can reveal the pack in Finder.
- **Scope**: local machine only. Conversations already sent to Anthropic and cloud records on claude.ai are out of scope; the web privacy switch and token revocation need your own sign-in.

After cleaning, open a new Claude Code session and check that it works, then delete the cleanup pack and empty the Trash; only then are the old traces gone from the machine. Run the write steps from Codex or a plain terminal; a Claude Code session that is using `~/.claude` only runs the read-only audit. Switch meanings and data locations are in [Privacy scope and data map](skills/claude-cleanup/references/privacy.md) (Chinese).

## 🏗️ 2. Set up: proxy-setup

Starts with no server and ends with a working proxy and fixed egress. Also used later to replace an entry, change protocol or rebuild the chain.

- **Staged progress**: requirements and current state, feasibility, cloud resources, protocol deployment, client import, routing and fixed egress, first verification. Each stage records its actual state, so an interrupted run resumes from the last confirmed stage without buying or importing twice.
- **Multiple clients**: covers Clash Verge／Mihomo, Shadowrocket and Windows; other clients are checked for capability before a native config is generated.
- **Fixed egress**: chosen apps or domains leave through the same final IP; when the protected chain fails, connections are refused instead of falling back to direct or another egress.
- **Evidence-based acceptance**: before handover, the final IP, rule hits, performance and DNS／WebRTC leaks are checked, and untested devices are listed as not verified.

References include [Setup](skills/proxy-setup/references/setup.md), [DigitalOcean creation](skills/proxy-setup/references/digitalocean-create.md), [Hysteria2 deployment](skills/proxy-setup/references/hysteria2.md) and [Fixed-egress chain](skills/proxy-setup/references/egress-chain.md) (all Chinese).

## 🔧 3. Maintain: proxy-maintenance

Handles a chain already in use so it keeps working as agreed at setup; new resources or a rebuilt chain go back to proxy-setup.

| Situation | Effect |
| --- | --- |
| Subscription update | Nodes and rules update while the connection and fixed egress stay the same |
| Slow or dropped connection | The cause is located layer by layer: DNS, rules, node, protocol, server, firewall |
| Leak check | DNS and WebRTC are confirmed not to bypass the proxy |
| Usage card | The client's subscription card shows the VPS monthly traffic |
| Renewals and billing | DigitalOcean and IPRoyal usage, renewals and SSH sources are checked |
| Client upgrade | Clash Verge service-lock conflicts after an upgrade are resolved |

During maintenance, the proxy or tunnel the agent itself depends on is never stopped from inside that chain. Diagnosis ends at a cause and a recommendation; changes need an explicit request.

## 🛠️ Requirements

| Feature | Dependency |
| --- | --- |
| claude-cleanup | macOS, uv, Python ≥ 3.10; standard library only |
| proxy-setup, proxy-maintenance | An agent that reads Markdown; clients, VPS and SSH as the task needs |

proxy-setup and proxy-maintenance link to each other's references, so install both; claude-cleanup can be installed on its own.

## 🚀 Setup

Have an agent read [SETUP.md](SETUP.md) (Chinese) to install, then start a new agent session. Payments, quitting Claude and signing in to web accounts during cleanup or setup are done by you.

| Setting | Location | Notes |
| --- | --- | --- |
| Private environment notes | `skills/proxy-maintenance/references/environment.local.md` | Points to your own ops notes, untracked; see [Project entry](skills/proxy-maintenance/references/environment.md) (Chinese) |
| Cleanup pack location | Entered when the cleanup runs | Desktop by default |

## 📁 Document roles

| File | Reader | Content |
| --- | --- | --- |
| `README.md` | Users | What each Skill does and when to use it |
| [SETUP.md](SETUP.md) | Agents | Install steps and success checks |
| `skills/*/SKILL.md` | Agents | Execution spec, order and boundaries |
| `skills/*/references/` | Agents | Task-specific details, such as [Setup](skills/proxy-setup/references/setup.md) |
| [AGENTS.md](AGENTS.md) | Maintainers and agents | Editing and verification rules |

## 🧪 Development checks

Regression tests for claude-cleanup:

```sh
cd skills/claude-cleanup
PYTHONDONTWRITEBYTECODE=1 uv run --no-project python -m unittest discover -s tests -v
```

## 📄 License

[MIT](LICENSE)
