# DigitalOcean 适配

仅在实际云服务商为 DigitalOcean 时读取。当前 Droplet、IP、防火墙 ID、账单与服务状态从项目记录定位并现场复核，不在技能固定快照。

从购买／创建新服务器开始时先读 [创建与首次登录](../../proxy-setup/references/digitalocean-create.md)；本页负责既有资源维护与费用判断。

## 来源变化与失联

先区分设备出口、机场出口、ISP 出口和服务器入口地址；SSH 白名单匹配新 SSH 连接实际来源，不一定等于浏览器检测出口。

Cloud Firewall 控制挂载资源流量，不控制云官网登录。目标链路损坏时，管理入口不能只依赖那条坏链。普通 Droplet Console 与 Recovery Console 的网络、账户要求不同，按当前文档核实，不承诺普通控制台必然绕过 SSH 防火墙；没有账户密码时不擅自重置 root。

按 [防火墙流程](../../proxy-setup/references/firewall.md) 添加本次批准的新管理单来源、验证独立新连接后再收紧旧来源。无需仅为动态 IP 默认部署持云 token 的自动白名单服务，也不把私有管理页面暴露公网作为救援。

## 地址与资源

Reserved IP 是可选入口，不等于服务器默认出站 IP；需要改变出站时另查路由、影响范围与官方方式。新增、解绑及闲置费用现场核对，不能把替换入口当免费只读诊断，也不为速度测试直接删除旧地址。

CPU、内存、进程与服务检查见 [分层排查](troubleshooting.md)。Insights 带宽图通常是速率，不能直接当累计 GB；单次 CPU 峰值不证明持续占满。

## 流量和费用

先读取所选日期范围、套餐、资源存在时间、团队额度、累计出站、超额项、抵扣来源和账单状态，再核对 [官方带宽计费](https://docs.digitalocean.com/platform/billing/bandwidth/) 的当前单位、额度累积和费率。

用户下载时互联网→VPS 是入站，VPS→设备是出站；上传时设备→VPS 是入站，VPS→互联网又是出站。转发协议有开销，不能一律说双倍收费，也不能把入站免费理解成转发上传不计出站。

超额量不是总用量；credits 是抵扣，不自动证明“超额费被退回”。按官方核实的规则和可用数据分别计算资源费、可计费出站与有效抵扣。1 GiB = 1.073741824 GB，图表速率与累计流量、预估与结算分开。

月末新建资源可能按存在时间累积额度，不假定立刻有整月配额；页面数据可能延迟，跨月重置与最终结算另核对。缺累计出站不能凭超额行推算精确总量。预测标明观察天数与代表性，不自动充值、升配或改扣款。

## 官方入口

- [配置云防火墙](https://docs.digitalocean.com/products/networking/firewalls/how-to/configure-rules/)
- [Droplet Console](https://docs.digitalocean.com/products/droplets/how-to/connect-with-console/)
- [Recovery Console](https://docs.digitalocean.com/products/droplets/how-to/recovery/recovery-console/)
- [Reserved IP 出站](https://docs.digitalocean.com/products/networking/reserved-ips/how-to/outbound-traffic/)
- [Reserved IP 计费](https://docs.digitalocean.com/products/networking/reserved-ips/details/pricing/)
