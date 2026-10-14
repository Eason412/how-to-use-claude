# 应用故障保护

## 范围与取舍

分别定义固定出口应用、普通代理应用和获准直连流量。整浏览器绑定固定代理会覆盖其中的国内网页和下载，非例外流量同受固定链故障影响；“其他流量正常”仅指范围外。独立 profile／无痕窗口不是系统进程隔离。Chrome 等浏览器 helper 名称随版本变化，helper、扩展、native host 和旁路需分别核实，不能用一个 helper 的证据覆盖全部。用户未确定时推荐影响相称的方案并解释代价，不自动全机断网。

TUN 规则随内核停止而消失。单一显式代理且无 DIRECT 后备，可让支持代理的请求在入口不可用时失败；它不自动约束 native host、任意工具子进程、MCP 或其他独立网络栈。需要整进程硬限制时按 [macOS 应用断线保护](macos-app-firewall.md) 加按程序的过滤器，不能把“允许整个 Chrome 联网”当成“只允许 Chrome 到本机代理”。macOS PF 的 user/group 匹配也不等于可执行文件匹配。系统级拦截需另定义范围并获得授权，链路维护授权不自动包括防火墙、守护进程或自动断网；静态规则核对不等于拒绝路径实测。

外部流传的“防封分流”域名清单只作线索：常见模板以 `FINAL,DIRECT` 兜底，照抄等于未匹配流量直连；`DOMAIN-KEYWORD` 会误伤无关网站；CNAME 落点域名不会被按请求域名匹配。应用顺带连接的风控、遥测、客服等第三方服务也要走同一出口，优先按进程或安装路径整体固定，不靠穷举域名；第三方公共服务域名不整段拉进固定出口。

## macOS Chrome 持久策略

已有固定 loopback HTTP 入站时优先复用，按现场确认端口和绑定目标。

- 用 `ProxySettings` 字典指定 `ProxyMode=fixed_servers`、唯一 `ProxyServer`，不包含 `direct://` 后备。`ProxyBypassList` 按获准例外设计；空字符串仍保留 Chromium 内置 loopback/link-local 例外。需要移除隐式例外时核对 `<-loopback>` 语义，再明确加入确需保留的本机地址。
- `WebRtcIPHandling=disable_non_proxied_udp` 限制非代理 UDP；按需要禁用 QUIC、网络预测，说明对通话与网页的影响。不把这些策略称为全机 kill switch，也不为通过检测随意禁用加密 DNS 或证书验证。
- 持久强制策略使用用户范围 `.mobileconfig` 的 `com.apple.ManagedClient.preferences → Forced → mcx_preference_settings →` Chrome 策略，生成独立标识和 UUID、允许移除。普通 `defaults write` 只适合 recommended 策略测试，不冒充 mandatory；不直接改系统生成的 Managed Preferences 缓存。
- 安装前检查既有相关策略，保留回退。说明作用范围及 Chrome 将显示受管理状态；本地自建策略不等于接入远程 MDM。
- 安装成功不等于运行进程已加载。以新请求的实际专口、chain 和出口验收；必要时在用户能保存网页工作时重启浏览器。
- 撤销只移除本次独立描述文件，并按需重启；不删除其他组织或用户的策略。

依据：[Chromium 代理行为](https://chromium.googlesource.com/chromium/src/+/HEAD/net/docs/proxy.md)、[Mac defaults 的限制](https://www.chromium.org/administrators/mac-quick-start/)、[Google 描述文件部署](https://support.google.com/chrome/a/answer/9020077)、[WebRTC 策略](https://github.com/chromium/chromium/blob/main/components/policy/resources/templates/policy_definitions/WebRtc/WebRtcIPHandling.yaml)。实施时核对当前版本支持。

## 命令行与故障验收

命令行在自身支持的配置中设置显式代理和最小 NO_PROXY；使用者要访问内网服务（如内部 Git）时，NO_PROXY 加上对应私网段。不要污染全局 shell，GUI 不一定遵循终端环境。检查大小写变量优先级与配置加载时机；被动关联本机 socket 与 inboundPort/sourcePort，不凭时间相邻判断应用命中。使用真实客户端二进制、隔离配置、假凭据及本地模拟服务验证主请求；若存在 bare／禁用非必要网络模式，先从该版本帮助确认。不能把 curl 通过当成目标客户端通过。

故障测试需要成功的对照请求和可观察的目标：模拟拒绝连接、认证失败、超时及入口故障，观察本可直连的目标是否实际收到请求。区分配置拒绝启动、运行时拒绝、请求超时与成功；HTTP 502 可能仍是 curl exit 0。空静态组启动失败不能替代运行时 provider 变空测试。

撤口条件见 [连接保护](connection-safety.md#当前连接保护)，优先用隔离实例测试。只撤专口不等于真正退出内核，测试故障层及普通／直连分支按 [验收矩阵](egress-validation.md#最小验收矩阵) 核对。

完整生命周期与泄露检查分别见 [验证与迁移](egress-validation.md) 和 [泄露验证](leak-check.md)。
