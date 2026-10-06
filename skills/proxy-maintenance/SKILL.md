---
name: proxy-maintenance
description: "维护已在使用的代理与固定出口：订阅更新、连接或速度排障、DNS／WebRTC 泄露检查、VPS 用量卡片、续费与账单、SSH 来源变化、客户端升级故障。新建 VPS、换入口或重做链路用 proxy-setup。"
---

# 日常维护与排障

三步中的第三步：清理（claude-cleanup）→ 搭建（proxy-setup）→ 维护（本技能）。本技能面对的是已经在用的链路，目标是让它继续按搭建时的约定工作；需要新建资源、更换入口、协议或重做固定出口链路时，转 proxy-setup。

先说明实际路径及影响范围，再完成用户要求的诊断或修改。诊断保持只读，到原因与建议为止，不自行修复。

## 先做

1. 读 [连接保护](references/connection-safety.md)，识别当前会话依赖；当前助手依赖的桥接、代理或隧道不能在该链路内停止、重启或撤口。
2. 查使用者的环境记录：[项目入口](references/environment.md)，再读取本次涉及的实际配置与运行态；记录与现场冲突时以现场为准。

## 按任务读取

| 任务 | 参考 |
|---|---|
| 切订阅后断网、更新节点或规则 | [订阅更新](references/subscription-update.md) |
| 超时、慢、某协议或地址失败、资源占用 | [分层排查](references/troubleshooting.md)（含性能对照） |
| DNS／WebRTC 是否绕过代理 | [泄露验证](references/leak-check.md) |
| 在订阅卡片显示 VPS 月用量 | [月用量卡片](references/quota-card.md) |
| DigitalOcean：SSH 来源变化、失联、流量与账单 | [DigitalOcean 维护](references/digitalocean.md) |
| IPRoyal：认证、续期与流量 | [IPRoyal 维护](references/iproyal.md) |
| Clash Verge 升级后服务锁冲突 | [服务升级锁冲突](references/client-upgrade.md) |
| 改名、清缓存、卸载、启动项整理 | [连接保护](references/connection-safety.md) |

云端端口与 SSH 来源规则沿用搭建时的 [防火墙边界](../proxy-setup/references/firewall.md)；固定出口相关的检查项沿用 [验证与迁移](../proxy-setup/references/egress-validation.md)，按本次改动选最小相关项，不每次重跑全套。

## 维护不变量

- 维护与订阅切换同时核对应用显式入口和候选配置的监听、绑定目标。缺少固定入口导致应用拒绝连接时，不据此认定远端出口故障，也不撤销断线保护来修配置不匹配。
- 受保护范围失败时拒绝，不降级到 DIRECT、裸机场或不合格旧链；普通订阅不自动当作固定出口备用，不擅自改用户命名。
- 只改受支持的持久源，生成后读回运行态；控制 API 的临时加载不代表下次启动仍有效。只筛选本次相关连接，旧连接不默认断开。
- 同一目标连续两次失败先停下排查：哪条假设被证伪、哪个决定引入问题、能否同时满足要求；结构性冲突转 proxy-setup 改结构，不继续调参。

## 边界

凭证、完整订阅 URL、控制器 secret 和私人配置不进入 Skill、报告或 Git；控制器保持本地认证访问，不输出全部浏览活动。查看账单与续期不等于授权付款、换凭证或改自动续费。共享 VPS 上的其他服务、模型路由与账号清理不属于本技能写集。报告实际结果、未验证项和回退位置，不展示流水账。
