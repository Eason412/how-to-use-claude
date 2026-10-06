---
name: proxy-setup
description: "从零搭建自建代理与固定出口：选购 VPS、部署协议、导入客户端、设计分流与固定最终出口链路、接入指定应用并完成首次验收；也用于更换入口或重做链路。已在使用的链路做日常维护和排障用 proxy-maintenance。"
---

# 搭建 VPS 与固定出口

三步中的第二步：先按 claude-cleanup 清理，再在本技能搭建，交付后进入 proxy-maintenance 维护。本技能只管“从无到可用”和结构性改动（新建、换入口、换协议、重做链路）；订阅更新、排障、泄露检查、用量与续费等日常事务归 proxy-maintenance。

机场是提供节点的订阅服务，VPS 是自建服务器，固定出口是目标网站看到的最终 IP，客户端负责接入与分流；这些角色不绑定品牌，也不必全部存在。固定的是最终出口，不是中间节点名称；固定 IP 不等于平台观察到的一切不变，也不保证账号结果。

## 阶段

按任务进入对应阶段，已完成的不重走；每个阶段留“已选择／已创建／已部署／已验收”的实际状态与证据位置，中断后从最后确认的阶段继续，不重复购买或导入。

1. **需求与现场**：确定设备与客户端、要固定出口的应用或域名、期望出口、直连例外、是否必须保留现有连接、预算。读取当前订阅、模式、TUN／系统代理与实际请求路径；复用已有资源前先查使用者的环境记录（[项目入口](../proxy-maintenance/references/environment.md)）。
2. **可行性**：读 [固定出口链路](references/egress-chain.md)，判断客户端能否表达所需链、协议和失败拒绝；不能同时满足全部要求时说明冲突并改结构，不继续试参数。
3. **云资源**：没有服务器时按 [DigitalOcean 创建](references/digitalocean-create.md) 或所选云的官方流程；防火墙按 [防火墙边界](references/firewall.md)。
4. **部署协议**：按 [搭建流程](references/setup.md)；选定 HY2 时按 [Hysteria2 分支](references/hysteria2.md)。
5. **导入客户端**：按 [导入流程](references/import-export.md)，客户端差异读 [Clash Verge／Mihomo](references/clash-verge.md)、[Shadowrocket](references/shadowrocket.md)、[Windows](references/windows.md)；其他客户端先核实能力与原生配置方式。
6. **分流与固定出口**：普通分流按 [分流规则](references/routing.md)；固定出口按 [链路与边界](references/egress-chain.md)，浏览器／命令行入口与失效保护按 [应用故障保护](references/egress-app-protection.md)，多设备按 [跨客户端适配](references/egress-clients.md)。
7. **首次验收与交付**：按 [验证与迁移](references/egress-validation.md) 选验收项；泄露检查用 [泄露验证](../proxy-maintenance/references/leak-check.md)。交付服务定位、私有客户端配置、使用方式、已测设备、恢复方式与未验证项，之后的变化交给 proxy-maintenance。

## 施工纪律

- 任何改名、重载、服务操作前，按 [连接保护](../proxy-maintenance/references/connection-safety.md) 识别当前会话依赖；当前助手依赖的桥接、代理或隧道不能在该链路内停止。
- 备份受影响源配置、扩展和引用映射；Unix 含凭证文件 0600、目录 0700，Windows 用最小 NTFS 访问权限。改受支持的源配置或扩展，不只改运行时文件，也不改会被订阅更新覆盖的下载原文。
- 临时测试授权不自动包含正式激活或新增云资源；超预算、新付费资源或无法安全验证证书时停止，等用户决定。
- 收尾只清理本次临时进程、规则与文件，保留一份合格回退与最小脱敏证据。

## 固定出口不变量

受保护链失败时拒绝，不自动转到裸机场、VPS 裸出口、DIRECT 或不合格旧链。用户明确接受出口变化时，那是重新定义保护范围，不再称其始终固定。仅域名规则覆盖不了全部未知域名、raw-IP、helper 与共享 CDN；TUN 不是 kill switch。真实公网、隔离模拟、静态读取是不同证据，未测试的客户端不算通过。

## 边界

凭证、完整订阅 URL、控制器 secret 和私人配置不进入 Skill、报告、Git 或公共转换网站。链路测试默认公共诊断目标或本地模拟，不以“测试代理”为由访问 Claude／Anthropic 或其他账号服务；明确禁测时直连与代理均不访问。不顺带清登录状态、改指纹、付款或开放服务。
