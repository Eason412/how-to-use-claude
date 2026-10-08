# How to Use Claude

```mermaid
flowchart LR
    A["① claude-cleanup"] --> B["② proxy-setup"] --> C["③ proxy-maintenance"]
```

> ⚠️ 这些 Skill 不用于规避封禁、支付检查、设备或 IP 信誉、浏览器指纹或任何平台风控；固定出口也不保证账号结果。

- **固定出口**：目标网站看到的最终 IP。指定应用或域名始终经同一个出口访问，出口失效时拒绝连接，而不是悄悄换成其他 IP。
- **VPS**：自己租用的云服务器，用来部署代理服务。

## 🧹 一、清理：claude-cleanup

处理 Claude Code 与 Claude Desktop 留在 Mac 上的隐私痕迹。

**主要作用**

1. **停止上报**：关闭遥测、错误上报、问卷与 WebFetch 域名预检，Claude 不再发送非必要数据。
2. **清除本机身份**：删除设备标识、实验缓存、旧身份快照与输入历史，下次启动生成新的设备身份。
3. **退出并清空会话**：退出登录，删除本地会话与钥匙串凭证，本机不再留有账号信息。

三项按档位递进，推荐直接选最高档（档位 3）：

| 档位 | 包含 | 登录 |
| --- | --- | --- |
| 0 只清缓存 | 缓存、日志与崩溃报告 | 保留 |
| 1 关上报 | 档位 0 + 作用 1 | 保留 |
| 2 清设备标识 | 档位 1 + 作用 2 | 保留 |
| 3 登出并清会话 | 档位 2 + 作用 3 | 退出 |

动手前先完整备份旧数据，结束时打包成 `Claude清理包-时间.tar.gz`（默认放在桌面）；文件只移入废纸篓，技能、hooks、插件与项目 memory 始终保留。完成时弹出“已完成清理”提示，确认 Claude Code 正常后删除清理包并清空废纸篓即可。详见 [隐私范围与数据地图](skills/claude-cleanup/references/privacy.md)。

## 🏗️ 二、搭建：proxy-setup

搭建代理并使用固定 IP。VPS、协议、客户端与固定出口服务由使用者自行选择，这里不做推荐。

**主要作用**

1. **搭好自己的代理**：购买 VPS、部署代理协议并导入各设备的客户端；现成资料按作者自用的环境整理，换用其他 VPS 与客户端同样可行。
2. **固定出口 IP**：指定的应用或网站始终经同一个 IP 访问；这条线路失效时直接断开，不会悄悄换成别的 IP。在 macOS 上还可以给这些应用加按程序的防火墙，代理软件退出时也不会改成直连。
3. **验收后交付**：核对最终 IP、分流规则、速度与 DNS／WebRTC 泄露，写明哪些设备已测、哪些未测。

## 🔧 三、维护：proxy-maintenance

照看已经在用的代理，让它继续按搭建时的约定工作；需要新建资源或重做链路时转回 proxy-setup。

**主要作用**

1. **更新订阅与客户端**：更新完成后，连接照常可用，固定 IP 保持不变。
2. **定位故障**：连接变慢、断开或疑似泄露时，按 DNS、规则、节点、协议、服务器、防火墙逐层查明原因并给出修复建议。
3. **维护 VPS 与固定 IP**：在客户端里查看 VPS 月流量，核对 VPS 与固定 IP 服务的用量、续费与账单。

## 🛠️ 运行条件

| 功能 | 依赖 |
| --- | --- |
| claude-cleanup | macOS、uv、Python ≥ 3.10；只用标准库 |
| proxy-setup、proxy-maintenance | 能读取 Markdown 的 Agent；客户端、VPS 与 SSH 按任务准备 |

proxy-setup 与 proxy-maintenance 互相引用对方的参考资料，需要一起安装；claude-cleanup 可单独安装。

## 🚀 设置方法

让 Agent 读取 [SETUP.md](SETUP.md) 完成安装，完成后开启新的 Agent 会话。清理与搭建中的付费、退出 Claude、登录网页账号等操作由本人完成。

- **私有环境记录**：维护自己的现有链路时，在 `skills/proxy-maintenance/references/environment.local.md` 写入指向自己运维文档的链接；该文件不入库，写法见 [项目入口](skills/proxy-maintenance/references/environment.md)。
- **清理包位置**：运行清理时输入，默认桌面。

## 📄 许可证

[MIT](LICENSE)
