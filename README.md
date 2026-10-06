# How to Use Claude

中文 | [English](README.en.md)

**本机少留痕迹，连接稳定可控。** 三个 Agent Skill 按使用顺序排列：先清理 Claude 留在电脑上的隐私痕迹，再搭建自己的 VPS 与固定出口，之后由 Agent 维护这条链路。Skill 是写给 Codex、Claude Code 等 Agent 的操作规范，交给 Agent 后由它按规范执行。

> ⚠️ 这些 Skill 不用于规避封禁、支付检查、设备或 IP 信誉、浏览器指纹或任何平台风控；固定出口也不保证账号结果。

- **固定出口**：目标网站看到的最终 IP。指定应用或域名始终经同一个出口访问，出口失效时拒绝连接，而不是悄悄换成其他 IP。
- **VPS**：自己租用的云服务器，用来部署代理服务。

## 🧭 三步

| 步骤 | Skill | 效果 |
| --- | --- | --- |
| 一、清理 | [claude-cleanup](skills/claude-cleanup/SKILL.md) | Claude 在本机的上报、设备标识与会话按所选档位清除 |
| 二、搭建 | [proxy-setup](skills/proxy-setup/SKILL.md) | 从零得到一条可用的代理与固定出口链路 |
| 三、维护 | [proxy-maintenance](skills/proxy-maintenance/SKILL.md) | 已在用的链路持续按搭建时的约定工作 |

## 🧹 一、清理：claude-cleanup

在 macOS 上清理 Claude Code 与 Claude Desktop 留在本机的隐私痕迹。按目标选一档，档位逐级包含：

| 档位 | 效果 | 登录 |
| --- | --- | --- |
| 0 只清缓存 | 缓存、日志和崩溃报告移入废纸篓 | 保留 |
| 1 关上报 | 再关闭遥测、错误上报、问卷与 WebFetch 域名预检 | 保留 |
| 2 清设备标识 | 再删除设备标识、实验缓存、旧身份快照与输入历史 | 保留 |
| 3 登出并清会话 | 再退出登录，删除本地会话与钥匙串凭证 | 退出 |

- **先备份再动手**：第一个写操作是完整备份，逐文件校验；结束时打成 `Claude清理包-时间.tar.gz`，默认放在桌面，也可指定位置；位置在 iCloud“桌面与文稿”同步范围内时，确认前和完成后各提醒一次。
- **可撤回**：文件只移入废纸篓；档位 3 的会话清除与钥匙串删除例外，只能从清理包恢复。
- **个人资产保留**：技能、hooks、插件、`CLAUDE.md`、settings 中未选择的键、各项目目录与 Codex 数据始终保留；项目 memory 默认从备份恢复。
- **一次确认、完成提示**：展示完整清单后输入一次 `CONFIRM` 才写盘；结束时弹出“已完成清理”对话框，可在访达中显示清理包。
- **清理范围**：只作用于本机。已发给官方的对话内容和 claude.ai 上的云端记录不在范围内，网页端的隐私开关与令牌吊销需要本人登录处理。

清理后新开 Claude Code，确认正常后删除清理包并清空废纸篓，旧痕迹才真正离开本机。写操作要在 Codex 或普通终端里运行，正在使用 `~/.claude` 的 Claude Code 只做只读审计。开关含义与数据位置见 [隐私范围与数据地图](skills/claude-cleanup/references/privacy.md)。

## 🏗️ 二、搭建：proxy-setup

从没有服务器开始，得到一条可用的代理和固定出口；以后更换入口、协议或重做链路也用它。

- **按阶段推进**：需求与现场、可行性、云资源、部署协议、导入客户端、分流与固定出口、首次验收；每阶段记录实际状态，中断后从最后确认的阶段继续，不重复购买或导入。
- **多客户端**：覆盖 Clash Verge／Mihomo、Shadowrocket 与 Windows；其他客户端先核实能力再生成原生配置。
- **固定出口**：指定应用或域名经同一最终 IP 访问；受保护链路失败时拒绝连接，不退回直连或其他出口。
- **有据验收**：交付前核对最终 IP、规则命中、性能与 DNS／WebRTC 泄露，未测试的设备单列为未验收。

参考资料包括 [搭建流程](skills/proxy-setup/references/setup.md)、[DigitalOcean 创建](skills/proxy-setup/references/digitalocean-create.md)、[Hysteria2 部署](skills/proxy-setup/references/hysteria2.md) 与 [固定出口链路](skills/proxy-setup/references/egress-chain.md)。

## 🔧 三、维护：proxy-maintenance

处理已在使用的链路，让它继续按搭建时的约定工作；需要新建资源或重做链路时转回 proxy-setup。

| 场景 | 效果 |
| --- | --- |
| 订阅更新 | 更新节点与规则后连接与固定出口保持不变 |
| 连接慢或断开 | 按 DNS、规则、节点、协议、服务器、防火墙逐层定位原因 |
| 泄露检查 | 确认 DNS 与 WebRTC 没有绕过代理 |
| 用量卡片 | 在客户端订阅卡片上显示 VPS 月流量 |
| 续费与账单 | 核对 DigitalOcean、IPRoyal 的用量、续期与 SSH 来源 |
| 客户端升级 | 处理 Clash Verge 升级后的服务锁冲突 |

维护期间，Agent 自身依赖的代理或隧道不会在该链路内被停止；诊断只给原因与建议，修改需要明确要求。

## 🛠️ 运行条件

| 功能 | 依赖 |
| --- | --- |
| claude-cleanup | macOS、uv、Python ≥ 3.10；只用标准库 |
| proxy-setup、proxy-maintenance | 能读取 Markdown 的 Agent；客户端、VPS 与 SSH 按任务准备 |

proxy-setup 与 proxy-maintenance 互相引用对方的参考资料，需要一起安装；claude-cleanup 可单独安装。

## 🚀 设置方法

让 Agent 读取 [SETUP.md](SETUP.md) 完成安装，完成后开启新的 Agent 会话。清理与搭建中的付费、退出 Claude、登录网页账号等操作由本人完成。

| 设置项 | 位置 | 说明 |
| --- | --- | --- |
| 私有环境记录 | `skills/proxy-maintenance/references/environment.local.md` | 指向自己的运维文档，不入库，见 [项目入口](skills/proxy-maintenance/references/environment.md) |
| 清理包位置 | 运行清理时输入 | 默认桌面 |

## 📁 文档分工

| 文件 | 读者 | 内容 |
| --- | --- | --- |
| `README.md` | 使用者 | 各 Skill 的效果与选择 |
| [SETUP.md](SETUP.md) | Agent | 安装步骤与成功判据 |
| `skills/*/SKILL.md` | Agent | 执行规范、顺序与边界 |
| `skills/*/references/` | Agent | 按任务读取的细节，如 [搭建流程](skills/proxy-setup/references/setup.md) |
| [AGENTS.md](AGENTS.md) | 维护者与 Agent | 修改与验证规则 |

## 🧪 开发验证

claude-cleanup 的回归测试：

```sh
cd skills/claude-cleanup
PYTHONDONTWRITEBYTECODE=1 uv run --no-project python -m unittest discover -s tests -v
```

## 📄 许可证

[MIT](LICENSE)
