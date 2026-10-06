# Clash Verge 服务升级锁冲突（macOS）

遇到 `service owner lock is held`／`stop the service before stale-owner maintenance`，先保存应用日志及对应时段的 launchd unified log，区分 GUI、特权服务、Mihomo 内核三个进程。不能把“内核已停”当成系统服务已退出，也不能把窗口关闭当成停服。

按时间核对版本不匹配、安装动作、旧服务 bootout、锁失败、新服务 bootstrap、内核启动。若 bootout 后立即维护 owner 状态且非阻塞获取锁失败，需对照安装版本源码检查是否缺少退出／锁释放等待；没有当时的锁持有者证据时，将具体持锁 PID 标为推断。重试成功只证明恢复，不证明竞态已消除。

`owner.lock` 是进程互斥锁，不是删掉文件就能安全清理的标记。不要删锁、按名字批量杀进程或在服务已恢复时反复重装。需再次维护时，先具备独立恢复通道和维护窗口，再确认服务已退出、锁可用再安装；安装器的持久修复应是有超时的锁等待／重试，超时保存诊断并停止。

源码定位参考：[安装器](https://github.com/clash-verge-rev/clash-verge-service-ipc/blob/v2.7.6/src/bin/install_service.rs)、[维护锁](https://github.com/clash-verge-rev/clash-verge-service-ipc/blob/v2.7.6/src/core/maintenance.rs)。这是历史版本的机制证据；当前版本另查。恢复后核对运行服务与应用自带版本、服务模式、TUN、DNS 接管和固定出口；KeepAlive 不等于断线保护。
