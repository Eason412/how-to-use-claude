# Clash Verge／Mihomo 适配

仅在实际客户端为 Clash Verge 或内核为 Mihomo 时使用。本页不是其他 VPN 客户端的通用语法；按安装版本核对官方资料。

Windows额外读 [Windows适配](windows.md)：原生SSH、NTFS权限、服务模式与TUN、命名管道／本地控制器及WSL差异；不要照抄Mac路径和Helper进程名。

## 定位与持久化

从应用配置目录的 profiles.yaml 查当前 UID 与专属 merge／script／rules／proxies／groups；核对全局扩展和生成的运行配置。UID、socket、版本和组选择留项目记录，不固定在技能。

读取控制器前确认当前本地 Unix socket／loopback 返回有效 JSON，secret 在进程内使用，不放 URL 或日志。只读优先 GET /configs、/rules、/providers/rules；/connections 仅筛选本次目标。连接失败不扩大监听范围或更换密钥。

Clash Verge 扩展顺序及列表／DNS 合并语义依版本变化，按 [官方扩展说明](https://www.clashverge.dev/guide/extend.html)与最终生成结果核对，不只检查某一层脚本。共同规则放合适的共享扩展，专属链放实际 profile 的扩展或自有主配置；应用可能最终回写 mode、tun 等字段。

重新激活／切换前先核对该版本是否关闭现有连接，并按 [运行维护](../../proxy-maintenance/references/connection-safety.md) 判断能否实施。经授权从应用重新激活订阅可生成持久配置；API 热加载只证明当前运行态，不代表下次仍在。不得用扩展写 mode=rule 冒充锁住 GUI 全局模式。

## 节点与引用

机场只是节点来源。自有主配置可用受支持 provider 接入；选择 file／http／inline 时核对格式、加载路径与更新机制。源订阅更新不等于 inline 副本更新；file provider 也要确认内核已重新加载当前缓存，不仅文件改变。

依次核对：源订阅 → provider／节点 → 入口组 → dialer-proxy → 最终策略组 → 规则 → 运行态。检查精确引用、成员非空、循环、来源限制和解析错误。节点显示名会变，业务规则用稳定的自有策略名。空组、缓存坏、引用丢失和解析失败分开测试；加载失败可能保留旧运行配置。

当前 Mihomo 链式代理通常用 dialer-proxy，而非旧 relay。ISP 节点引用中转，中转可引用机场入口；电脑直连 VPS 时不要保留机场 dialer-proxy。不是链中的每个节点都需要一个可选组；只暴露用户确实要切换的策略，不能删除仍被链引用的内部节点。

## 固定出口特殊行为

- 标准 HTTP CONNECT 出口不提供目标 UDP。不能仅靠节点 udp=false 或组 disable-udp 宣称拒绝；需要针对保护范围的 NETWORK=UDP 拒绝并验证命中，不全局禁 UDP 误伤 HY2 隧道。
- 普通规则可能被 global／direct 模式绕过；支持绑定固定 proxy 的 loopback 入站可限定实际进入该入口的请求，但不保护绕口 socket。
- empty-fallback 需要确认版本支持及运行行为，缺省行为不能假设为拒绝。v1.19.31 [解析器](https://github.com/MetaCubeX/mihomo/blob/v1.19.31/adapter/outboundgroup/parser.go)存在 COMPATIBLE 默认路径；这只是该版本源码证据，不代替当前空组测试。
- 固定入站行为可参考相应版本的 [路由实现](https://github.com/MetaCubeX/mihomo/blob/v1.19.31/tunnel/tunnel.go)及 [入站实现](https://github.com/MetaCubeX/mihomo/blob/v1.19.31/listener/inbound/base.go)，当前内核另行核对。
- CLI 显式代理在其自身受支持的设置内配置，不污染全局 shell；GUI 不一定遵循终端环境。被动关联本机 socket 与 inboundPort/sourcePort，不凭时间相邻就宣布某应用已命中。
- Chrome 等浏览器 helper 名称随版本变化，整浏览器固定范围会涵盖其中其他网站和下载。不能用一个 helper 的证据覆盖所有扩展、native host 或旁路。

规则源与语法参考：[Mihomo 规则](https://wiki.metacubex.one/config/rules/)、[节点集合](https://wiki.metacubex.one/config/proxy-providers/)、[规则集合](https://wiki.metacubex.one/config/rule-providers/)。实际测试的范围按 [固定出口验收](egress-validation.md)执行。

