# 应用故障保护

## 范围与取舍

分别定义固定出口应用、普通代理应用和获准直连流量。问某应用如何使用，是为了定位入口，不代表忽略其他软件。整浏览器绑定固定代理会覆盖其中的国内网页和下载；独立 profile／无痕窗口不是系统进程隔离。用户未确定时推荐影响相称的方案并解释代价，不自动全机断网。

TUN 规则随内核停止而消失。单一显式代理且无 DIRECT 后备，可让支持代理的请求在入口不可用时失败；它不自动约束 native host、任意工具子进程、MCP 或其他独立网络栈。需要整进程硬限制时按 [macOS 应用断线保护](macos-app-firewall.md) 加按程序的过滤器，不能把“允许整个 Chrome 联网”当成“只允许 Chrome 到本机代理”。macOS PF 的 user/group 匹配也不等于可执行文件匹配。

外部流传的“防封分流”域名清单只作线索：常见模板以 `FINAL,DIRECT` 兜底，照抄等于未匹配流量直连；`DOMAIN-KEYWORD` 会误伤无关网站；CNAME 落点域名不会被按请求域名匹配。应用顺带连接的风控、遥测、客服等第三方服务也要走同一出口，优先按进程或安装路径整体固定，不靠穷举域名；第三方公共服务域名不整段拉进固定出口。

## macOS Chrome 持久策略

已有固定 loopback HTTP 入站时优先复用，按现场确认端口和绑定目标；不在技能固定本机端口或出口 IP。

- 用 `ProxySettings` 字典指定 `ProxyMode=fixed_servers`、唯一 `ProxyServer`，不包含 `direct://` 后备。`ProxyBypassList` 按获准例外设计；空字符串仍保留 Chromium 内置 loopback/link-local 例外。需要移除隐式例外时核对 `<-loopback>` 语义，再明确加入确需保留的本机地址。
- `WebRtcIPHandling=disable_non_proxied_udp` 限制非代理 UDP；按需要禁用 QUIC、网络预测，说明对通话与网页的影响。不把这些策略称为全机 kill switch，也不为通过检测随意禁用加密 DNS 或证书验证。
- 持久强制策略使用用户范围 `.mobileconfig` 的 `com.apple.ManagedClient.preferences → Forced → mcx_preference_settings →` Chrome 策略，生成独立标识和 UUID、允许移除。普通 `defaults write` 只适合 recommended 策略测试，不冒充 mandatory；不直接改系统生成的 Managed Preferences 缓存。
- 安装前检查既有相关策略，保留回退。说明作用范围及 Chrome 将显示受管理状态；本地自建策略不等于接入远程 MDM。当前明确授权有效，不因技能再重复审批。
- 安装成功不等于运行进程已加载。以新请求的实际专口、chain 和出口验收；必要时在用户能保存网页工作时重启浏览器。工具拒绝内部页面时不要绕过访问限制，使用允许的实际请求证据或用户提供的策略状态。
- 撤销只移除本次独立描述文件，并按需重启；不删除其他组织或用户的策略。

依据：[Chromium 代理行为](https://chromium.googlesource.com/chromium/src/+/HEAD/net/docs/proxy.md)、[Mac defaults 的限制](https://www.chromium.org/administrators/mac-quick-start/)、[Google 描述文件部署](https://support.google.com/chrome/a/answer/9020077)、[WebRTC 策略](https://github.com/chromium/chromium/blob/main/components/policy/resources/templates/policy_definitions/WebRtc/WebRtcIPHandling.yaml)。实施时核对当前版本支持。

## 命令行与故障验收

命令行在自身支持的配置中设置显式代理和最小 NO_PROXY；使用者要访问内网服务（如内部 Git）时，NO_PROXY 加上对应私网段。不要污染全局 shell。检查大小写变量优先级与配置加载时机。使用真实客户端二进制、隔离配置、假凭据及本地模拟服务验证主请求；若存在 bare／禁用非必要网络模式，先从该版本帮助确认。不能把 curl 通过当成目标客户端通过。

故障测试需要成功的对照请求和可观察的目标：模拟拒绝连接、认证失败、超时及入口故障，观察本可直连的目标是否实际收到请求。区分配置拒绝启动、运行时拒绝、请求超时与成功；HTTP 502 可能仍是 curl exit 0。空静态组启动失败不能替代运行时 provider 变空测试。

优先用隔离实例做入口故障测试。不得撤下承载当前助手或恢复通道的专口；其他实机撤口测试须有明确维护窗口、限时自动恢复并检查恢复结果；先确认无并发配置变化，避免用旧快照覆盖用户新设置。只撤专口不等于真正退出内核；报告测试实际覆盖的故障层。故障期间同时验证代表性的普通代理与直连分支，避免只测受保护应用。

完整内核退出／冷启动、IPv6、授权媒体设备后的 WebRTC 或独立过滤器生命周期，按目标与授权分别验收；未测就保留未验证项。具体步骤沿用 [验证与迁移](egress-validation.md)，泄露判据见 [泄露验证](../../proxy-maintenance/references/leak-check.md)。
