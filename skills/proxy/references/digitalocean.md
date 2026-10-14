# DigitalOcean 创建与维护

## 创建与首次登录

适用于尚无 VPS 的新建任务。已有服务器直接回 [搭建流程](deploy.md)，不重复购买。实际创建前重新核对 [官方创建说明](https://docs.digitalocean.com/products/droplets/how-to/create/) 与控制台。

### 1. 定预算与用途

先确认月预算、所在网络、同时使用设备、预计流量、其他服务与固定 ISP 需求。个人代理可先评估共享 CPU 的小规格，按内存和流量需求选够用的一档；升 CPU 不保证改善跨境路由。

明确区域、系统、架构、CPU／RAM／磁盘、计费形式、流量额度及额外项目的选择与理由。地区靠近只是候选依据，不保证线路好或大陆优化。

购买前确认每台目标设备及客户端支持所选协议和证书验证方式。无域名且选 HY2 时先读 [自有证书分支](hysteria2.md#2-先选证书方式)；不能安全验证证书时先确定替代客户端／证书方案，不靠关闭校验迁就。

### 2. 账号与费用授权

复用用户已登录的官方控制台，确认正确团队／项目和可用支付状态。登录验证码、付款信息由用户在官方界面处理；不收集银行卡或把创建授权扩展为预充值／自动扣费修改。

向用户确认总成本口径：实例、出站超额、选用的固定代理／域名和收费附加资源分别计算。信用额度不是永久免费，关机不等于资源已删除或账单停止；生命周期计费按 [当前价格](https://docs.digitalocean.com/products/droplets/details/pricing/) 核实。预算已明确且创建已授权，不再重复询问同一选择；超预算或出现新的付费资源才暂停。

### 3. 填创建表单

在控制台 Create → Droplet（Linux 云服务器）填写。用户的电脑是 Windows 不影响 VPS 选择 Linux。

首次还没有公钥时先完成下节“准备 SSH 密钥”，再填写 Authentication；不能先提交创建再补选密钥。

| 项目 | 执行判断 |
|---|---|
| Region | 按用户、上游位置与候选线路选择可用区域；不把同一区域等同于同样网络质量 |
| Image | 选择所用代理支持且仍维护的 Ubuntu／Debian 稳定版本与架构，个人代理不额外装数据库／AI 镜像 |
| Configuration／Size | 逐项确认共享或独享 CPU、RAM、磁盘及实际价格；若出现不同计费系列，核对月上限而非只比小时价 |
| Storage／Backups | 无需要不加独立磁盘、自动备份；需要则计入预算，不把默认推荐当已授权 |
| Network | 需要公网入口；不误建只能私网访问的实例。IPv6 按方案决定，启用就单独规划规则和验收 |
| Authentication | 选择本次管理端持有的 SSH 公钥，不能上传私钥 |
| Monitoring／Other | 按需要选监控；不填未知启动脚本，不顺带买托管数据库或其他产品 |
| Finalize | 确认数量通常为一台，短主机名、正确项目与完整价格摘要 |

点击 Create 前最后核对全部选择与授权。点击后记录资源 ID、区域、系统、入口地址和创建状态在项目；若超时，先查询是否已创建，禁止连点导致多买。

### 4. 准备 SSH 密钥

Windows 见 [Windows 适配](windows.md) 的 PowerShell 步骤；macOS／Linux 在本机终端使用 OpenSSH。复用合适现有密钥时先确认归属；新密钥用独立文件名，发现重名不覆盖。示例在本机运行，路径按实际用户设置：

```sh
ssh-keygen -t ed25519 -f /absolute/private/path/id_vps -C "vps-admin"
```

交互设置密钥口令，私钥只留管理端；云表单粘贴对应 .pub 的完整单行。macOS／Linux 私有目录 0700、私钥 0600；Windows 用 NTFS ACL，不执行 chmod。参考 [SSH 密钥创建](https://docs.digitalocean.com/products/droplets/how-to/add-ssh-keys/create-with-openssh/)。

### 5. 防火墙与首次登录

按 [防火墙边界](firewall.md#安全修改与验证) 为目标实例绑定云规则并核对管理来源与代理端口范围。

从密钥对应管理端连接，示例 SERVER_IP、路径由现场替换：

```sh
ssh -i /absolute/private/path/id_vps root@SERVER_IP
```

首次 SSH host key 提示与独立可信控制台中的主机公钥指纹核对，不使用 StrictHostKeyChecking=no；重建后变更也先核实身份，不直接抹掉全部 known_hosts。

登录后在 **Linux VPS** 检查：`id`、`uname -m`、`cat /etc/os-release`、`cloud-init status`、`free -h`、`df -h /`、`ss -lntup`。确认初始化结束、系统和资源符合订单、现有监听无冲突。新建主机按系统维护流程更新必要包，已有主机不擅自整机升级或重启。

默认登录用户按镜像实际说明确认；需要普通管理用户时先添加其公钥与 sudo 权限并独立验证，再考虑收紧旧登录方式，不先禁用唯一入口。

### 6. 创建阶段完成条件

确认批准数量、费用选择、独立新 SSH 连接、防火墙绑定和初始化结果，再进入协议部署。

然后进入 [Hysteria2 部署](hysteria2.md) 或按实际客户端支持选择其他协议。不要自动购买 Reserved IP；只有需要改变入口且已核实费用、授权时才操作。失败资源是否删除由本次授权决定；关机不能作为停止收费的替代，删除前核对 ID、数据及依附资源。

## 既有资源维护

仅用于 DigitalOcean。

### 来源变化与失联

SSH 来源变化按 [防火墙流程](firewall.md#安全修改与验证) 核对。

Cloud Firewall 控制挂载资源流量，不控制云官网登录。目标链路损坏时，管理入口不能只依赖那条坏链。普通 Droplet Console 与 Recovery Console 的网络、账户要求不同，按当前文档核实，不承诺普通控制台必然绕过 SSH 防火墙；没有账户密码时不擅自重置 root。

新增管理来源及旧来源收紧按 [防火墙流程](firewall.md#安全修改与验证) 执行。无需仅为动态 IP 默认部署持云 token 的自动白名单服务，也不把私有管理页面暴露公网作为救援。

### 地址与资源

Reserved IP 是可选入口，不等于服务器默认出站 IP；需要改变出站时另查路由、影响范围与官方方式。新增、解绑及闲置费用现场核对，不能把替换入口当免费只读诊断，也不为速度测试直接删除旧地址。

CPU、内存、进程与服务检查见 [分层排查](troubleshooting.md)。Insights 带宽图通常是速率，不能直接当累计 GB；单次 CPU 峰值不证明持续占满。

### 流量和费用

先读取所选日期范围、套餐、资源存在时间、团队额度、累计出站、超额项、抵扣来源和账单状态，再核对 [官方带宽计费](https://docs.digitalocean.com/platform/billing/bandwidth/) 的当前单位、额度累积和费率。

用户下载时互联网→VPS 是入站，VPS→设备是出站；上传时设备→VPS 是入站，VPS→互联网又是出站。转发协议有开销，不能一律说双倍收费，也不能把入站免费理解成转发上传不计出站。

超额量不是总用量；credits 是抵扣，不自动证明“超额费被退回”。按官方核实的规则和可用数据分别计算资源费、可计费出站与有效抵扣。1 GiB = 1.073741824 GB，图表速率与累计流量、预估与结算分开。

月末新建资源可能按存在时间累积额度，不假定立刻有整月配额；页面数据可能延迟，跨月重置与最终结算另核对。缺累计出站不能凭超额行推算精确总量。预测标明观察天数与代表性，不自动充值、升配或改扣款。

### 官方入口

- [配置云防火墙](https://docs.digitalocean.com/products/networking/firewalls/how-to/configure-rules/)
- [Droplet Console](https://docs.digitalocean.com/products/droplets/how-to/connect-with-console/)
- [Recovery Console](https://docs.digitalocean.com/products/droplets/how-to/recovery/recovery-console/)
- [Reserved IP 出站](https://docs.digitalocean.com/products/networking/reserved-ips/how-to/outbound-traffic/)
- [Reserved IP 计费](https://docs.digitalocean.com/products/networking/reserved-ips/details/pricing/)
