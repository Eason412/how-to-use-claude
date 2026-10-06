# Windows 管理端与客户端

Windows 可以管理 Linux VPS，也可以作为代理客户端；VPS 无需改为 Windows。先辨认 Windows 版本、CPU 架构、现有客户端、是否受公司策略管理及是否允许管理员授权。Windows、macOS、WSL 是不同执行环境，命令必须注明在哪一端运行。

## 1. 本机 OpenSSH

PowerShell 先运行 `Get-Command ssh, ssh-keygen, scp` 与 `ssh -V`。已有可用客户端不重复安装。缺失时按微软可选功能安装 **OpenSSH Client**；若用命令，需要管理员 PowerShell：

```powershell
Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH.Client*'
Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0
```

只在确认未安装、获准安装时执行第二行。仅管理云 VPS 不需要启用本机 sshd、安装 OpenSSH Server 或开放本机 TCP22。[微软安装说明](https://learn.microsoft.com/en-us/windows-server/administration/openssh/openssh_install_firstuse)。

在普通用户 PowerShell 创建独立密钥，先确认路径不存在；有同名文件就换名字，不覆盖：

```powershell
$proxyKeyPath = Join-Path $env:USERPROFILE '.ssh\id_vps'
$proxyKeyDirectory = Split-Path -Parent $proxyKeyPath
if (-not (Test-Path $proxyKeyDirectory)) {
    New-Item -ItemType Directory -Path $proxyKeyDirectory | Out-Null
}
if ((Test-Path $proxyKeyPath) -or (Test-Path ($proxyKeyPath + '.pub'))) {
    throw '目标密钥文件已存在；先选择新的文件名，不覆盖。'
}
ssh-keygen -t ed25519 -f $proxyKeyPath -C 'vps-admin'
if ($LASTEXITCODE -ne 0) { throw '密钥生成失败，停止上传。' }
Get-Content ($proxyKeyPath + '.pub')
```

交互设置口令，最后一行只显示公钥，用于云平台录入；不显示私钥。连接时将 SERVER_IP 替换为现场地址：

```powershell
ssh -i $proxyKeyPath root@SERVER_IP
```

核对 SSH 主机指纹后才接受。Linux 系统命令仅在登录 VPS 后运行；不在 PowerShell 执行 apt／systemctl／chmod。私钥及含认证配置需要限定本用户与确有需要的系统／服务身份访问，使用当前 NTFS ACL 检查，不把 Unix 0600字面搬过来，也不批量重写用户目录 ACL。[密钥说明](https://learn.microsoft.com/en-us/windows-server/administration/openssh/openssh_keymanagement)、[私钥 ACL](https://github.com/PowerShell/Win32-OpenSSH/wiki/Security-protection-of-various-files-in-win32-openssh)。

## 2. 安装与导入客户端

优先沿用用户已选且确实支持目标协议／分流／证书验证的客户端；没有客户端时提出一个满足目标的选择，不假设所有 VPN App 都能导入自建节点。Clash Verge Rev 有 Windows 安装包，但它不是唯一选择。

从项目官方发布页按 x64／ARM64、系统版本选包，核对来源与签名／校验信息；不要使用搜索结果中的仿冒下载站。需要 WebView2 等依赖时按官方方式处理，不绕过系统安全限制。[Clash Verge Rev Releases](https://github.com/clash-verge-rev/clash-verge-rev/releases)。

用客户端“打开配置目录”或实际设置定位目录，不套用 Mac /Users/... 或 Unix socket。文件保持 UTF-8，检查隐藏扩展名没有把 .yaml 保存成 .yaml.txt；PowerShell 不同版本默认编码可能不同，写入时明确编码。导入按 [通用流程](import-export.md)，先读回节点、TLS、策略及持久来源。

## 3. 系统代理与 TUN

系统代理不覆盖所有程序。需要 TUN 时，按客户端官方服务模式／管理员安装流程完成系统组件，核对服务运行、虚拟网卡、路由、DNS、mode 和真实新连接；不是按钮打开就通过。

Clash Verge 的服务模式与 GUI 是不同进程。多个 VPN／虚拟网卡可能抢路由，先识别现有连接，用户要求不中断时不试着全关。Mihomo 部分 Linux 参数不适用 Windows，不复制 include-uid、auto-redirect 或 macOS 网卡名。Windows 防火墙只按必要程序和网络范围放行，不关闭整机防火墙；strict-route 等选项可能影响虚拟机，应按实际版本和现有业务验证。[Mihomo TUN](https://wiki.metacubex.one/config/inbound/tun/)、[服务模式说明](https://www.clashverge.dev/guide/term.html)。

控制器使用该 Windows 客户端实际支持的本机接口（如命名管道或认证 loopback）；不得为复用 Mac 命令开放公网控制端口。查连接时按实际 Windows 可执行文件名／路径判断，不照搬 macOS Helper 规则。

## 4. 有界验证与 WSL

Windows 的 `Test-NetConnection SERVER_IP -Port 22` 只测 TCP，不证明 HY2 UDP443通。TLS／UDP通过对应协议客户端测试。在允许的公共目标上可用 `curl.exe` 避免旧 PowerShell 的 curl 别名混淆；显式代理、TUN 和物理直连分开判断，不使用 -k 关闭验证。

普通 Windows GUI 代理不要求安装 WSL。已有 WSL 则单独确认 NAT／mirrored、DNS、HTTP proxy 环境及程序遵循性；Windows 浏览器、PowerShell 与 WSL 各自验收。localhost 与宿主地址关系依网络模式变化，不默认把监听扩大为 0.0.0.0 来解决互通。[微软 WSL 网络](https://learn.microsoft.com/en-us/windows/wsl/networking)。

## 5. 完成条件

实际 Windows 应用的新请求连通、命中期望规则、出口符合要求；TUN需求另确认接管与 DNS／IPv6；固定出口按 [专链验收](../../fixed-egress/references/validation.md)。经授权验证重启客户端或登录恢复后持久性，但不为写文档而重启当前链路。

没有 Windows 现场时，明确标为“官方资料核对，Windows 实机未验收”；不能用 Mac 的结果替代。
