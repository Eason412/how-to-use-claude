---
name: proxy
description: "搭建与维护代理及固定出口：搭建 VPS、协议、客户端、分流与固定出口，更换入口或重做链路；更新订阅，排查连接、速度、DNS／WebRTC 泄露，处理 VPS 用量卡片、续费账单、SSH 来源变化与客户端升级故障。"
---

# 代理与固定出口

机场是提供节点的订阅服务，VPS 是自建服务器，固定出口是目标网站看到的最终 IP，客户端负责接入与分流；这些角色不绑定品牌，也不必全部存在。固定的是最终出口，不是中间节点名称；固定 IP 不等于平台观察到的一切不变，也不保证账号结果。

先说明实际路径及影响范围，再完成用户要求的诊断或修改。诊断保持只读，到原因与建议为止，不自行修复。

## 先做

1. 读 [连接保护](references/connection-safety.md)，识别当前会话依赖；任何改名、重载、服务操作前，当前助手依赖的桥接、代理或隧道不能在该链路内停止、重启或撤口，这项约束不以用户另说“保持连接”为前提。
2. 按下文环境记录定位使用者的资料，再读取本次涉及的实际配置与运行态。
3. 按症状定位故障层：DNS、规则、节点、协议、服务器、防火墙和上游。规则模式、系统代理和 TUN 是不同层；首页 IP、HTTP 200、节点延迟和浏览器错误都不能单独证明应用路径。

### 环境记录

本节说明去哪里找使用者自己的环境记录，本身不保存任何 IP、订单、节点、UID、版本或完成状态。

使用者的私有记录写在 `references/environment.local.md`（不入库），内容只放指向私有交接文档、运维记录和回退位置的链接。该文件存在时先读它；不存在时向用户确认记录位置，或从其指定的客户端和已登录控制台现场定位，不遍历无关私有资料。

先查记录，再读取本次涉及的实际配置与运行态。记录冲突时不盲目恢复旧地址、供应商或协议；当前现场和当次指令优先。记录里的路径缺失只表示记录不可用，不表示服务已经删除。

模型路由、账号清理等不属于代理维护；共享 VPS 上的其他服务不因本次代理调整成为写集。

## 按任务读取

### 搭建与改造

| 任务 | 参考 |
|---|---|
| 新建 VPS、协议部署 | [部署流程](references/deploy.md)、[DigitalOcean 创建](references/digitalocean.md#创建与首次登录)、[Hysteria2](references/hysteria2.md)、[防火墙边界](references/firewall.md) |
| 导入、迁移与跨客户端适配 | [导入与迁移](references/import-export.md)、[Clash Verge／Mihomo](references/clash-verge.md)、[Shadowrocket](references/shadowrocket.md)、[Windows](references/windows.md) |
| 分流、固定出口与应用保护 | [分流规则](references/routing.md)、[链路与边界](references/egress-chain.md)、[应用故障保护](references/egress-app-protection.md)、[macOS 应用断线保护](references/macos-app-firewall.md) |
| 首次验收、迁移与交付 | [验证与迁移](references/egress-validation.md)、[泄露验证](references/leak-check.md) |

### 维护与排障

| 任务 | 参考 |
|---|---|
| 切订阅后断网、更新节点或规则 | [订阅更新](references/config-loading.md#订阅更新) |
| 给应用加入固定出口、保存后未生效、内核缺少规则 | [配置加载与应用验收](references/config-loading.md) |
| 超时、慢、某协议或地址失败、资源占用 | [分层排查](references/troubleshooting.md)（含性能对照） |
| DNS／WebRTC 是否绕过代理 | [泄露验证](references/leak-check.md)；要求代理停止后也不直连时读 [应用故障保护](references/egress-app-protection.md) |
| 在订阅卡片显示 VPS 月用量 | [月用量卡片](references/quota-card.md) |
| DigitalOcean：SSH 来源变化、失联、流量与账单 | [既有资源维护](references/digitalocean.md#既有资源维护) |
| IPRoyal：认证、续期与流量 | [IPRoyal 维护](references/iproyal.md) |
| Clash Verge 升级后服务锁冲突 | [服务升级锁冲突](references/clash-verge.md#服务升级锁冲突macos) |
| 改名、清缓存、卸载、启动项整理 | [连接保护](references/connection-safety.md) |

云端端口与 SSH 来源规则沿用 [防火墙边界](references/firewall.md)；固定出口相关检查沿用 [验证与迁移](references/egress-validation.md)，按本次改动选最小相关项，不每次重跑全套。

## 搭建阶段

按任务进入对应阶段，已完成的不重走；每个阶段留“已选择／已创建／已部署／已验收”的实际状态与证据位置，中断后从最后确认的阶段继续，不重复购买或导入。

1. **需求与现场**：确定设备与客户端、要固定出口的应用或域名、期望出口、直连例外、是否必须保留现有连接、预算。读取当前订阅、模式、TUN／系统代理与实际请求路径，区分设备连接的地址、服务器对外来源和网站所见出口；普通连接能用时不重搭全部环境。复用已有资源前先查使用者的 [环境记录](#环境记录)。
2. **可行性**：读 [固定出口链路](references/egress-chain.md)，判断客户端能否表达所需链、协议和失败拒绝；不能同时满足全部要求时说明冲突并改结构，不继续试参数。
3. **云资源**：没有服务器时按 [DigitalOcean 创建](references/digitalocean.md#创建与首次登录) 或所选云的官方流程；防火墙按 [防火墙边界](references/firewall.md)。
4. **部署协议**：按 [部署流程](references/deploy.md)；选定 HY2 时按 [Hysteria2 分支](references/hysteria2.md)。
5. **导入客户端**：按 [导入流程](references/import-export.md)，客户端差异读 [Clash Verge／Mihomo](references/clash-verge.md)、[Shadowrocket](references/shadowrocket.md)、[Windows](references/windows.md)；其他客户端先核实能力与原生配置方式，不套用这些客户端的语法。
6. **分流与固定出口**：普通分流按 [分流规则](references/routing.md)；固定出口按 [链路与边界](references/egress-chain.md)，浏览器／命令行入口与失效保护按 [应用故障保护](references/egress-app-protection.md)，macOS 内核退出后的按程序兜底按 [应用断线保护](references/macos-app-firewall.md)，多设备按 [跨客户端适配](references/import-export.md#跨客户端适配)。
7. **首次验收与交付**：生成后读回运行态，分别确认连接、规则命中和性能，跨设备单独验收；按 [验证与迁移](references/egress-validation.md) 选验收项，核对最终 IP、实际路径与规则、故障时不换出口；缺少设备或禁测实际服务时写明未验收范围，不用另一端代替；泄露检查用 [泄露验证](references/leak-check.md)。交付服务定位、私有客户端配置、使用方式、已测设备、恢复方式与未验证项。

## 纪律与不变量

- 实施已有授权内的改动，不重复索取已明确的许可；会影响用户要求保持的连接时暂停。
- 备份受影响源配置、扩展和引用映射；Unix 含凭证文件 0600、目录 0700，Windows 用最小 NTFS 访问权限。只改受支持的持久源配置或扩展，不只改运行时文件，也不改会被订阅更新覆盖的下载原文；生成后读回运行态，控制 API 的临时加载不代表下次启动仍有效。只筛选本次相关连接，旧连接不默认断开。
- 临时测试授权不自动包含正式激活或新增云资源；超预算、新付费资源或无法安全验证证书时停止，等用户决定。
- 维护与订阅切换同时核对应用显式入口和候选配置的监听、绑定目标。缺少固定入口导致应用拒绝连接时，不据此认定远端出口故障，也不撤销断线保护来修配置不匹配。
- 受保护链失败时拒绝，不自动转到裸机场、VPS 裸出口、DIRECT 或不合格旧链；普通订阅不自动当作固定出口备用，不擅自改用户命名。用户明确接受出口变化时，那是重新定义保护范围，不再称其始终固定。
- 仅域名规则覆盖不了全部未知域名、raw-IP、helper 与共享 CDN；TUN 不是 kill switch；规则模式、全局模式和绕开代理入口分别核实，不靠配置名字承诺硬保证。真实公网、隔离模拟、静态读取是不同证据，未测试的客户端不算通过。
- 同一目标连续两次失败先停下排查：哪条假设被证伪、哪个决定引入问题、能否同时满足要求；结构性冲突按搭建阶段改结构，不继续调参。
- 收尾只清理本次临时进程、规则与文件，保留一份合格回退与最小脱敏证据。

## 边界

凭证、完整订阅 URL、控制器 secret 和私人配置不进入 Skill、报告、Git 或公共转换网站；控制器保持本地认证访问，不输出全部浏览活动。链路测试默认公共诊断目标或本地模拟，不以“测试代理”为由访问 Claude／Anthropic 或其他账号服务；明确禁测时直连与代理均不访问。不顺带清登录状态、改指纹、付款或开放服务；查看账单与续期不等于授权付款、换凭证或改自动续费。共享 VPS 上的其他服务、模型路由与账号清理不属于本技能写集。模型桥接的内部配置由其专用技能处理，这里只把它当连接依赖保护，不扩展写集。报告实际结果、未验证项和回退位置，不展示流水账。
