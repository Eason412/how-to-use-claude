# Hysteria2 从空服务器到客户端

这是已选定 HY2 后的具体部署分支，不意味着它适合所有网络。前提：有可管理的 Linux VPS、目标客户端支持 HY2、计划使用的 UDP 入口可达；Windows／macOS 只是客户端平台，Linux 服务端步骤相同。入口 UDP 被网络阻断时不要宣称换 TCP443规则就能修复，转回 [分层排查](troubleshooting.md) 选择兼容结构。

## 1. 记录安装范围

在已认证的 VPS shell 中核对系统、架构、现有监听和服务，确认没有现用 HY2 需要保留。记录新版本、二进制、配置路径、运行用户、unit 和防火墙条目；不沿用其他机器的 hysteria.service 等名称。

新建轻量 VPS 可采用 [官方 Linux 安装器](https://v2.hysteria.network/docs/getting-started/Server-Installation-Script/)。它安装程序与 systemd 单元，**只生成示例配置，不会完成你的认证与证书配置**。执行前把官方脚本下载到私有临时目录，检查内容和版本选项，按批准版本运行；不要把未知第三方一键脚本作为默认。已有服务先确认升级影响，不能直接重跑安装器覆盖。

官方安装器通常使用 /etc/hysteria/config.yaml 与 hysteria-server.service；安装后以 `systemctl cat hysteria-server.service` 的 ExecStart、User、能力及实际配置路径为准。443低端口需要适当绑定权限，不因权限错误把所有服务改为 root。下载受阻时可按官方 --local 方式私下传输经过来源核验的同架构二进制，不默认部署 Docker。

## 2. 先选证书方式

**有自己控制的域名**：DNS 指向实际入口，检查错误 AAAA 和代理/CDN状态；HY2普通 UDP 不能假设通过普通 HTTP CDN。可采用 ACME，但需按所选挑战开放必要端口或准备 DNS API，不能只有 UDP443 就认为签发条件满足。DNS API凭证留私有配置，避免额外复制；证书续期也是部署验收内容。

**没有域名**：可用自有证书与客户端信任／指纹固定，但须先核实每个客户端支持的验证语义；不为了导入方便永久开启“跳过证书验证”。若客户端不能可靠验证该证书，改用其支持的证书方式，而不是关校验。

此分支在购买前先确认：电脑Mihomo支持证书指纹固定；手机若用Shadowrocket，其HY2的TLS设置中需有SHA256指纹固定并可保持“允许不安全／跳过验证”关闭。没有这些字段的客户端不沿用此配方。仅字段存在尚不是运行通过，后面必须做正确及错误指纹对照。

生成自签 RSA 证书的示例在 **VPS 私有证书目录**执行；文件已存在时不覆盖。名称 vpn.internal 是示例身份，客户端 SNI应一致，不是要求它能公网解析：

```sh
openssl req -x509 -newkey rsa:3072 -nodes -sha256 -days 365 \
  -keyout server.key -out server.crt \
  -subj "/CN=vpn.internal" -addext "subjectAltName=DNS:vpn.internal"
openssl x509 -in server.crt -noout -fingerprint -sha256
```

私钥不离开服务器。按 unit 运行用户设置最小读取权限并确保父目录可穿越，不把证书私钥 chmod 777。自签方案记录到期和更换流程；换证书后需要同步信任／指纹，不能突然破坏已有设备。参数依据 [服务端 TLS](https://v2.hysteria.network/docs/advanced/Full-Server-Config/) 和 [客户端 TLS](https://v2.hysteria.network/docs/advanced/Full-Client-Config/) 核对。

## 3. 写最小服务端配置

使用安全随机生成的密码，不使用示例文本，不回显到聊天／命令历史。用文件编辑工具写入实际 ExecStart 指向的路径；下例只是自有证书方案骨架，路径与密码必须替换：

```yaml
listen: 0.0.0.0:443
tls:
  cert: /etc/hysteria/server.crt
  key: /etc/hysteria/server.key
auth:
  type: password
  password: "REPLACE_WITH_PRIVATE_RANDOM_PASSWORD"
```

如果选 ACME，则以当前官方格式用 acme 段替换 tls 段，填自己控制的域名与联系邮箱；不能同时照抄两套冲突方式。首版不加入未经需要的端口跳跃、QUIC窗口、带宽上限和伪装反代。仅普通代理不需要打开 Linux IP转发/NAT。

[官方服务端入门](https://v2.hysteria.network/docs/getting-started/Server/)说明自有证书和 ACME两种方式。先做 YAML解析、占位符清除、路径/权限/身份对应检查；解析通过不代表服务能够启动。

## 4. 放行与启动

云防火墙与主机防火墙只放本次批准的 UDP端口与来源范围。电脑公网来源固定可限单来源；手机蜂窝与换网需要另定可用来源政策，不能沿用SSH单来源导致只能家里使用，也不能擅自扩大范围。SSH22保持独立管理规则。

确认是新建且未占用服务后，以下命令在 **Linux VPS**运行，服务名须与刚安装的 unit一致：

```sh
sudo systemctl enable --now hysteria-server.service
sudo systemctl is-active hysteria-server.service
sudo systemctl is-enabled hysteria-server.service
sudo ss -lnup
sudo journalctl -u hysteria-server.service --no-pager -n 40
```

过滤日志中的认证信息，只保留启动、绑定和错误。失败先分配置、权限、证书和端口冲突，不反复重启整台服务器。用对应协议客户端验证真实握手；TCP端口测试不能验收 UDP HY2。

## 5. 生成客户端文件

为每个设备生成其原生格式；同一组连接参数不能直接把服务端 YAML 导入客户端。保持 server／port、auth、SNI、证书信任、可选 obfs 两端一致。

Mihomo 节点示例（**不是包含 DNS、TUN、分流的完整配置**）：

```yaml
proxies:
  - name: VPS
    type: hysteria2
    server: "REPLACE_WITH_SERVER_IP_OR_HOST"
    port: 443
    password: "REPLACE_WITH_PRIVATE_RANDOM_PASSWORD"
    sni: "REPLACE_WITH_CERTIFICATE_NAME"
    skip-cert-verify: false
    alpn:
      - h3
```

可信 CA证书按名称验证；上面骨架不能原样用于自签证书。自签方案使用第2步从**实际服务端证书**取得的SHA256，不把SSH主机指纹或其他网站证书混进来。通过已认证SSH获取后，去掉“SHA256 Fingerprint=”前缀与冒号，得到64位十六进制证书摘要，安全传到设备：

- Mihomo：在该节点添加 \`fingerprint: "实际64位证书摘要"\`，SNI填证书名称，保持 \`skip-cert-verify: false\`；指纹不是浏览器指纹／client-fingerprint。按 [Mihomo HY2字段说明](https://wiki.metacubex.one/config/proxies/hysteria2/)核对当前版本。
- Shadowrocket：在HY2节点TLS设置填同一SNI和SHA256证书摘要，保持允许不安全关闭；保存后重新打开核对未丢字段。若版本不接受此格式，按当前UI要求转换冒号格式，不更换摘要值、不关闭验证。
- 原生HY2客户端或其他客户端：使用其文档规定的证书信任机制，不能把Mihomo字段名直接复制。原生配置参见 [客户端TLS](https://v2.hysteria.network/docs/advanced/Full-Client-Config/)。

在不承载生产流量的临时节点做对照：正确指纹的认证及公共请求成功，将指纹改一个字符后同类新请求必须失败，再删除临时错误节点。每个设备分别执行；如果正确指纹仍失败，停止并检查该版本固定指纹与系统CA验证的组合语义，选自定义CA或受信证书，不设置 insecure=true“修好”。这项未完成就不能声称无域名方案已安全可用。

桌面按 [Clash Verge](clash-verge.md) 或实际客户端添加原生策略、DNS与接管配置，Windows另读 [平台适配](windows.md)。iPhone且使用Shadowrocket时按 [手机适配](shadowrocket.md) 导入；Android或其他客户端先核实其HY2与证书信任能力，再生成原生配置并读回，不默认使用小火箭。没有要固定 ISP 的请求就到此为止；需要时进入 [固定出口](../../fixed-egress/SKILL.md)，不将 VPS裸出口称为静态 ISP。

## 6. 验收、维护和撤回

验收至少记录：服务在运行与开机启用、正确证书和认证可连、错误认证／证书被拒绝、实际设备的新公共请求出口正确、规则与 DNS／IPv6符合目标、小流量测速及CPU／可用内存。计划的重启／睡眠恢复只在允许中断时测试，否则明确未测；启用自启动不是已经做过重启验证。

长用配置需记录证书到期与续期方式、版本与原配置备份、流量查看入口，不默认启用不受控自动升级。连接成功不证明长期稳定或所有网络可用。

撤回先停本次独立 unit，核对其监听消失，再按身份清理本次云规则与文件；已有共享服务不能运行通用 --remove 卸载。整台新 VPS若不用，只有获删除授权才销毁，并检查仍收费的依附资源。保留当前可用方案后清理转换文件和下载的安装器，不制造多份正式配置。

本页是依据官方文档整理的操作分支；在具体机器完成启动与客户端验收前，不得记录“部署已通过”。
