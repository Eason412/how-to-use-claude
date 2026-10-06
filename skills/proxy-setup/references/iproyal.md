# IPRoyal 适配

仅在实际最终代理供应商为 IPRoyal 时读取；其他供应商按其产品文档和订单检查，不照搬条款。当前订单、IP、端口与凭证定位留 [项目入口](environment.md)，使用前现场核实。

## 认证与协议

代理 IP／端口／用户名／密码不是供应商网站登录账号。读取凭证仅用于授权操作，密码不重复展示；重置凭证需要同步所有受影响客户端，不能作为默认排错。

HTTP／HTTPS 标签可能表示 HTTP 代理能访问 HTTPS 网站，不足以证明客户端到代理已有 TLS。SOCKS5 不自带加密，协议支持 UDP 不等于产品开放 UDP。链式加密边界见 [链路说明](../../fixed-egress/references/chain-policy.md)。

IP 白名单、密码认证、并发和设备许可按当前产品确认。设备都经一个 VPS可能呈现相同来源，但不由此推导供应商多设备授权；历史客服答复不能变成所有订单的规则。

“Residential”／“Hosting”及风险分属于数据库分类，不证明物理住宅线路或平台账号结果。在线检测器只证明其检测路径；提交凭证前确认官方域名和用户授权，不把 OK／200 当成本机整链通过。

## 续期与流量

保持 IP 时核对原订单的续期方式，区分续订、额外购买与每次续费换新 IP。现场读取有效期、余额、金额和自动续费状态；“充值成功”不等于续订成功，过期能否恢复按当前政策确认。

计费与云 VPS 分开；剩余流量、合理使用阈值和服务器额度不能混用。unlimited 的限制与超限处理查当前条款，不推断一定断网或降速。查看、解释不授权付款、换凭证或改变续订设置。

## 官方入口

- [订阅管理](https://help.iproyal.com/en/articles/7827110-how-to-turn-on-subscription-for-isp-proxies)
- [同一 IP 使用期](https://help.iproyal.com/en/articles/7222107-how-long-can-you-use-the-same-ip-address)
- [会话限制](https://help.iproyal.com/en/articles/7222629-how-many-sessions-can-i-use-at-once)
- [ISP 使用说明](https://help.iproyal.com/en/articles/7955587-how-to-use-isp-proxies)
- [合理使用](https://help.iproyal.com/en/articles/12094903-what-is-the-fair-usage-policy)

引用是检索入口，不是当前条款已核实的证明。
