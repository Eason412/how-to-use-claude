#!/usr/bin/env python3
"""在 macOS 上审计并分档清理 Claude Code / Claude Desktop 本机状态。

档位逐级包含：0 只清可再生缓存；1 关上报；2 再清设备标识（保留登录）；3 再登出并清本地会话。
"""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import hashlib
import json
import os
import pathlib
import re
import shutil
import sqlite3
import stat
import subprocess
import sys
import tarfile
import tempfile

BACKUP_NAME = "Claude清理包"  # 文件夹名，也是压缩包名前缀
LEVEL_NAMES = ("只清缓存日志", "关上报", "关上报 + 清设备标识（保留登录）", "关上报 + 清设备标识 + 登出并清本地会话")
# 用户级 settings.json 的隐私开关；总开关会连带停自动更新，单独询问
PRIVACY_ENV = {
    "DISABLE_TELEMETRY": "1",
    "DISABLE_ERROR_REPORTING": "1",
    "DISABLE_BUG_COMMAND": "1",
    "DO_NOT_TRACK": "1",
    "CLAUDE_CODE_DISABLE_OFFICIAL_MARKETPLACE_AUTOINSTALL": "1",
}
PRIVACY_SETTINGS = {"feedbackSurveyRate": 0, "skipWebFetchPreflight": True}
TOTAL_SWITCH = "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"
TELEMETRY_KEYS = ("DISABLE_TELEMETRY", "DISABLE_ERROR_REPORTING", TOTAL_SWITCH)
# 删除键（不是改成空值），下次启动由 Claude Code 重新生成
IDENTITY_KEYS = ("userID", "anonymousId", "machineID", "remoteControlMachineId", "firstStartTime", "claudeCodeFirstTokenDate")
CACHE_KEYS = (
    "additionalModelCostsCache", "additionalModelOptionsCache", "autoCompactWindowsCache",
    "cachedChromeExtensionInstalled", "cachedDynamicConfigs", "cachedExperimentData", "cachedExperimentFeatures",
    "cachedExtraUsageDisabledReason", "cachedGrowthBookFeatures", "cachedGrowthBookFeaturesAt", "cachedStatsigGates",
    "clientData", "clientDataCache", "clientDataCacheSlots", "feedbackSurveyState", "groveConfigCache",
    "metricsStatusCache", "modelAccessCache", "orgModelDefaultCache", "passesEligibilityCache", "s1mAccessCache",
)
ACCOUNT_KEYS = ("oauthAccount",)
# 始终受保护；档位 2、3 才放开会话边角料，项目会话与 tasks 只由 `claude purge` 处理
BASE_PROTECTED = {
    "CLAUDE.md", "agents", "backups", "commands", "hooks", "mcp-servers", "plans", "plugins", "projects",
    "scripts", "settings.json", "settings.local.json", "skills", "tasks", "todos",
}
SESSION_SIDECARS = (
    "debug", "file-history", "history.jsonl", "paste-cache", "session-env", "sessions", "shell-snapshots", "statsig",
)
PURGED = {"projects", "tasks", "debug", "file-history"}
LOGOUT_FILES = (".credentials.json", "mcp-needs-auth-cache.json")
CLI_CACHE = ("cache", "stats-cache.json", "telemetry", "usage-data", "usage.jsonl", "usage.with-fix.jsonl")
SAFE_RELATIVE = ("Library/Caches/claude-cli-nodejs", "Library/Logs/Claude")
SAFE_GLOBS = (
    "Library/Caches/com.anthropic.claudefordesktop*", "Library/Logs/DiagnosticReports/Claude*",
    "Library/Application Support/CrashReporter/Claude*",
)
DESKTOP_RELATIVE = (
    "Library/Application Support/Claude", "Library/Application Support/Claude-3p",
    "Library/Application Support/com.anthropic.claudefordesktop",
    "Library/HTTPStorages/com.anthropic.claudefordesktop",
    "Library/Preferences/com.anthropic.claudefordesktop.plist",
    "Library/Saved Application State/com.anthropic.claudefordesktop.savedState",
    "Library/WebKit/com.anthropic.claudefordesktop",
)
DESKTOP_GLOBS = ("Library/Preferences/ByHost/com.anthropic.claudefordesktop*.plist",)
APP = pathlib.Path("/Applications/Claude.app")
KEYCHAIN_SERVICE = re.compile(r"^(Claude Code-credentials.*|claude-code(-credentials)?)$")
# CC Switch 中由本机会话日志解析出的 Claude 用量；供应商、Key 与其他产品的表不动
CCSWITCH_DELETES = (
    ("proxy_request_logs", "app_type", "app_type = 'claude'"),
    ("usage_daily_rollups", "app_type", "app_type = 'claude'"),
    ("session_log_sync", "file_path", "file_path LIKE '%/.claude/%' OR file_path LIKE '%\\.claude\\%'"),
)


def config_paths(home: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
    """返回 (Claude 配置根, 身份文件)；设置了 CLAUDE_CONFIG_DIR 时身份文件也在该目录内。"""
    custom = os.environ.get("CLAUDE_CONFIG_DIR")
    if custom:
        root = pathlib.Path(custom).expanduser()
        return root, root / ".claude.json"
    return home / ".claude", home / ".claude.json"


def read_json(path: pathlib.Path, default: object | None = None) -> object:
    if not path.exists() and default is not None:
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: pathlib.Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp = pathlib.Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp, mode)
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def settings_env(data: object) -> dict[str, object]:
    if not isinstance(data, dict) or not isinstance(data.get("env", {}), dict):
        raise ValueError("settings.json 的顶层或 env 结构异常，拒绝修改")
    return data.get("env", {})


def telemetry(data: object) -> dict[str, object | None]:
    env = settings_env(data)
    return {key: env.get(key) for key in TELEMETRY_KEYS}


def discover(home: pathlib.Path, claude: pathlib.Path) -> tuple[list[pathlib.Path], list[pathlib.Path]]:
    safe = [claude / name for name in CLI_CACHE]
    safe += [home / name for name in SAFE_RELATIVE]
    desktop = [home / name for name in DESKTOP_RELATIVE]
    for pattern in SAFE_GLOBS:
        safe += map(pathlib.Path, glob.glob(str(home / pattern)))
    for pattern in DESKTOP_GLOBS:
        desktop += map(pathlib.Path, glob.glob(str(home / pattern)))
    return existing(safe), existing(desktop)


def existing(paths) -> list[pathlib.Path]:
    return sorted({p for p in paths if p.exists() or p.is_symlink()}, key=str)


def identity_snapshots(claude: pathlib.Path) -> list[pathlib.Path]:
    backups = claude / "backups"
    return sorted(p for p in backups.glob(".claude.json.backup*") if p.is_file() or p.is_symlink()) if backups.is_dir() else []


class ProcessCheckError(RuntimeError):
    """无法确认 Claude 进程状态；写流程必须在此停止。"""


def run_ps(args: list[str]) -> str:
    try:
        result = subprocess.run(args, capture_output=True, text=True, errors="replace", check=False)
    except OSError as error:
        raise ProcessCheckError(f"无法确认 Claude 进程状态：{error}") from error
    if result.returncode != 0 or not result.stdout.strip():
        detail = result.stderr.strip() or f"ps 退出码 {result.returncode}"
        raise ProcessCheckError(f"无法确认 Claude 进程状态：{detail}")
    return result.stdout


def claude_processes() -> list[str]:
    found = []
    for line in run_ps(["ps", "-axo", "pid=,comm=,args="]).splitlines():
        parts = line.strip().split(maxsplit=2)
        if len(parts) < 2 or parts[0] == str(os.getpid()):
            continue
        command = pathlib.Path(parts[1]).name.lower()
        args = parts[2] if len(parts) == 3 else ""
        first = pathlib.Path(args.split(maxsplit=1)[0]).name.lower() if args else ""
        if command in {"claude", "claude-code"} or first in {"claude", "claude-code"} or "/Claude.app/" in args:
            found.append(line.strip())
    return found


def ccswitch_processes() -> list[str]:
    return [line.strip() for line in run_ps(["ps", "-axo", "pid=,args="]).splitlines()
            if "CC Switch.app" in line or re.search(r"/cc-switch(\s|$)", line)]


def running_under_claude() -> bool:
    pid = os.getppid()
    for _ in range(12):
        parts = run_ps(["ps", "-p", str(pid), "-o", "ppid=,comm=,args="]).strip().split(maxsplit=2)
        if len(parts) < 2 or not parts[0].isdigit():
            raise ProcessCheckError("无法确认 Claude 进程状态：ps 输出无法解析")
        command = pathlib.Path(parts[1]).name.lower()
        first = pathlib.Path(parts[2].split(maxsplit=1)[0]).name.lower() if len(parts) == 3 else ""
        if command in {"claude", "claude-code"} or first in {"claude", "claude-code"}:
            return True
        next_pid = int(parts[0])
        if next_pid <= 1 or next_pid == pid:
            return False
        pid = next_pid
    return False


def file_digest(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _raise(error: OSError) -> None:
    raise error


def snapshot(root: pathlib.Path) -> dict[str, tuple]:
    """逐相对路径记录类型、大小、sha256 或符号链接目标；不跟随符号链接，读取失败即抛错。"""
    entries: dict[str, tuple] = {}
    for current, dirs, files in os.walk(root, followlinks=False, onerror=_raise):
        base = pathlib.Path(current)
        for name in dirs + files:
            path = base / name
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                entry = ("symlink", os.readlink(path))
            elif stat.S_ISDIR(mode):
                entry = ("dir",)
            elif stat.S_ISREG(mode):
                entry = ("file", path.stat().st_size, file_digest(path))
            else:
                entry = ("other", stat.S_IFMT(mode))
            entries[path.relative_to(root).as_posix()] = entry
    return entries


def verify_copy(source: pathlib.Path, copy: pathlib.Path, label: str, partial: pathlib.Path) -> dict[str, tuple]:
    before, after = snapshot(source), snapshot(copy)
    bad = sorted(key for key in before.keys() | after.keys() if before.get(key) != after.get(key))
    if bad:
        raise RuntimeError(f"{label} 备份校验失败，{len(bad)} 项不一致（如 {bad[0]}），保留未完成副本：{partial}")
    return before


def backup_destination(value: str, home: pathlib.Path, forbidden: list[pathlib.Path]) -> pathlib.Path:
    """备份放在用户指定目录（默认桌面）下；不能落进本次会被清理的位置或废纸篓。"""
    path = pathlib.Path(os.path.expanduser(value.strip() or str(home / "Desktop")))
    if not path.is_absolute():
        raise ValueError("备份位置必须是绝对路径或以 ~ 开头，已停止且未修改")
    if not path.is_dir():
        raise ValueError(f"备份位置不存在或不是目录：{path}，已停止且未修改")
    real = path.resolve()
    for blocked in forbidden + [home / ".Trash"]:
        blocked_real = real_location(blocked)
        if real == blocked_real or blocked_real in real.parents:
            raise ValueError(f"备份位置落在会被清理的位置内：{path}，已停止且未修改")
    return path


def icloud_synced(path: pathlib.Path, home: pathlib.Path) -> bool:
    """开启“桌面与文稿”iCloud 同步时，放在桌面或文稿里的备份会被上传。"""
    real = path.resolve()
    for name in ("Desktop", "Documents"):
        folder = (home / name).resolve()
        if (real == folder or folder in real.parents) and (home / "Library/Mobile Documents/com~apple~CloudDocs" / name).exists():
            return True
    return False


def create_backup(home: pathlib.Path, ccswitch_db: pathlib.Path | None = None, dest: pathlib.Path | None = None) -> pathlib.Path:
    claude, identity = config_paths(home)
    folder = (dest or home / "Desktop") / BACKUP_NAME
    folder.mkdir(mode=0o700, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    name, n = f"{BACKUP_NAME}-{stamp}", 1
    while any((folder / f"{name}{suffix}").exists() for suffix in ("", ".partial", ".tar.gz")):
        n += 1
        name = f"{BACKUP_NAME}-{stamp}-{n}"
    partial = folder / f"{name}.partial"
    final = partial.with_suffix("")
    partial.mkdir(mode=0o700)
    files = bytes_ = 0
    copied_claude = claude.is_dir()
    if copied_claude:
        shutil.copytree(claude, partial / "dot-claude", symlinks=True)
        entries = verify_copy(claude, partial / "dot-claude", "Claude 配置目录", partial)
        regular = [entry for entry in entries.values() if entry[0] == "file"]
        files, bytes_ = len(regular), sum(entry[1] for entry in regular)
    copied_identity = identity.is_file()
    if copied_identity:
        shutil.copy2(identity, partial / "claude.json")
        if (identity.stat().st_size, file_digest(identity)) != (
            (partial / "claude.json").stat().st_size, file_digest(partial / "claude.json")
        ):
            raise RuntimeError(f".claude.json 备份校验失败，保留未完成副本：{partial}")
    if ccswitch_db is not None:
        with sqlite3.connect(f"file:{ccswitch_db}?mode=ro", uri=True) as source, sqlite3.connect(partial / "cc-switch.db") as copy:
            source.backup(copy)
    write_json(
        partial / "manifest.json",
        {
            "files": files, "regularFileBytes": bytes_, "verification": "relative path, type, size, sha256, symlink target",
            "claudeDirCopied": copied_claude, "claudeJsonCopied": copied_identity, "ccSwitchCopied": ccswitch_db is not None,
        },
    )
    partial.rename(final)
    return final


def archive_entries(archive: pathlib.Path) -> dict[str, tuple]:
    """按 snapshot() 的格式读回压缩包内容，便于逐项比对。"""
    special = {tarfile.FIFOTYPE: stat.S_IFIFO, tarfile.CHRTYPE: stat.S_IFCHR, tarfile.BLKTYPE: stat.S_IFBLK}
    entries: dict[str, tuple] = {}
    with tarfile.open(archive, "r:gz") as tar:
        for member in tar:
            relative = member.name.partition("/")[2]
            if not relative:
                continue
            if member.issym():
                entries[relative] = ("symlink", member.linkname)
            elif member.isdir():
                entries[relative] = ("dir",)
            elif member.isfile():
                digest, handle = hashlib.sha256(), tar.extractfile(member)
                for chunk in iter(lambda: handle.read(1 << 20), b""):
                    digest.update(chunk)
                entries[relative] = ("file", member.size, digest.hexdigest())
            else:
                entries[relative] = ("other", special.get(member.type, member.type))
    return entries


def archive_backup(backup: pathlib.Path) -> pathlib.Path:
    """把已校验的备份目录打成 tar.gz（保留符号链接），读回逐项比对一致后才删除目录。"""
    archive = backup.with_name(backup.name + ".tar.gz")
    expected = snapshot(backup)
    with os.fdopen(os.open(archive, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as raw:
        with tarfile.open(fileobj=raw, mode="w:gz") as tar:
            tar.add(backup, arcname=backup.name)
    found = archive_entries(archive)
    bad = sorted(key for key in expected.keys() | found.keys() if expected.get(key) != found.get(key))
    if bad:
        raise RuntimeError(f"备份压缩包校验失败，{len(bad)} 项不一致（如 {bad[0]}），备份目录保留：{backup}")
    shutil.rmtree(backup)
    return archive


ICLOUD_NOTE = "清理包在 iCloud“桌面与文稿”同步范围内，已上传到 iCloud；删除后还要到 iCloud.com 云盘的“最近删除”中彻底删除。"


def notify_done(archive: pathlib.Path, level: int, icloud: bool = False) -> None:
    """弹出“已完成清理”对话框，可在访达中显示清理包；没有图形界面（如 SSH）时静默跳过。"""
    text = (f"已完成清理（档位 {level}：{LEVEL_NAMES[level]}）。\n\n清理包：{archive.name}\n\n"
            "新开 Claude Code 确认一切正常后，删除清理包并清空废纸篓，清理才算彻底。"
            + (f"\n\n{ICLOUD_NOTE}" if icloud else ""))
    script = ['on run argv', 'display dialog (item 1 of argv) with title "Claude 清理" buttons {"在访达中显示清理包", "好"} '
              'default button "好" with icon note giving up after 600', 'end run']
    try:
        result = subprocess.run(["osascript", *sum((["-e", line] for line in script), []), text],
                                capture_output=True, text=True, timeout=660)
        if "在访达中显示清理包" in result.stdout:
            subprocess.run(["open", "-R", str(archive)], capture_output=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        pass


def real_location(path: pathlib.Path) -> pathlib.Path:
    """解析所有父目录的符号链接；末级若是符号链接则保留链接本身。"""
    return path.absolute().parent.resolve() / path.name


def protected_names(level: int) -> set[str]:
    return set(BASE_PROTECTED) | (set() if level >= 2 else set(SESSION_SIDECARS))


def move_to_trash(
    target: pathlib.Path, allowed: set[pathlib.Path], claude: pathlib.Path, batch: pathlib.Path, level: int = 0
) -> pathlib.Path:
    absolute = target.absolute()
    protected = {claude / name for name in protected_names(level)}
    # 档位 2 起允许移走 backups/ 里带旧身份的 .claude.json 快照，backups 目录本身仍受保护
    is_snapshot = level >= 2 and absolute.parent == (claude / "backups").absolute() and absolute.name.startswith(".claude.json.backup")
    inside = [p for p in protected if absolute == p.absolute() or p.absolute() in absolute.parents]
    if absolute == claude.absolute() or (inside and not is_snapshot):
        raise RuntimeError(f"拒绝触碰受保护路径：{target}")
    if absolute not in {path.absolute() for path in allowed}:
        raise RuntimeError(f"目标不在删除白名单：{target}")
    real, claude_real = real_location(target), claude.resolve()
    protected_real = {real_location(p) for p in protected} | {p.resolve() for p in protected}
    if is_snapshot:
        protected_real -= {(claude / "backups").resolve(), real_location(claude / "backups")}
        if real.parent != (claude / "backups").resolve():
            raise RuntimeError(f"身份快照解析后不在 backups 目录：{target} -> {real}")
    if real == claude_real or real in claude_real.parents or any(
        real == p or p in real.parents or real in p.parents for p in protected_real
    ):
        raise RuntimeError(f"拒绝触碰受保护路径（符号链接解析后）：{target} -> {real}")
    batch.mkdir(parents=True, exist_ok=True)
    destination = batch / f"{len(list(batch.iterdir())):02d}-{target.name}"
    shutil.move(str(target), str(destination))
    return destination


def apply_privacy(claude: pathlib.Path, total_switch: bool, cleanup_days: int | None) -> None:
    """合并写入用户级 settings.json；其他键、hooks、权限和秘密保持原样。"""
    path = claude / "settings.json"
    data = read_json(path, {})
    if not isinstance(data, dict):
        raise ValueError("settings.json 顶层必须是 JSON object")
    updated, env = dict(data), dict(settings_env(data))
    env.update(PRIVACY_ENV)
    if total_switch:
        env[TOTAL_SWITCH] = "1"
    updated["env"] = env
    updated.update(PRIVACY_SETTINGS)
    if cleanup_days is not None:
        updated["cleanupPeriodDays"] = cleanup_days
    if updated != data:
        write_json(path, updated)


def privacy_applied(data: object) -> bool:
    env = settings_env(data)
    return all(str(env.get(key, "")) == value for key, value in PRIVACY_ENV.items())


def strip_identity(identity: pathlib.Path, level: int, project_stats: bool) -> int:
    """删除身份与缓存键（档位 3 再删账号块）；返回删除的键数。"""
    if not identity.is_file():
        return 0
    data = read_json(identity)
    if not isinstance(data, dict):
        raise ValueError(f"身份文件不是 JSON object：{identity}")
    keys = IDENTITY_KEYS + CACHE_KEYS + (ACCOUNT_KEYS if level >= 3 else ())
    updated = {key: value for key, value in data.items() if key not in keys}
    removed = len(data) - len(updated)
    if project_stats and isinstance(updated.get("projects"), dict):
        projects = {}
        for name, entry in updated["projects"].items():
            if isinstance(entry, dict):
                kept = {key: value for key, value in entry.items() if not key.startswith("last")}
                removed += len(entry) - len(kept)
                entry = kept
            projects[name] = entry
        updated["projects"] = projects
    if updated != data:
        write_json(identity, updated)
    return removed


def identity_keys_left(identity: pathlib.Path, level: int) -> list[str]:
    data = read_json(identity, {})
    keys = IDENTITY_KEYS + (ACCOUNT_KEYS if level >= 3 else ())
    return [key for key in keys if isinstance(data, dict) and key in data]


def keychain_services() -> list[str]:
    """只返回 Claude Code 凭证条目的 service 名，不读取口令。"""
    result = subprocess.run(["security", "dump-keychain"], capture_output=True, text=True, errors="replace", check=False)
    if result.returncode != 0:
        raise RuntimeError(f"无法读取钥匙串条目列表：{result.stderr.strip() or result.returncode}")
    names = set(re.findall(r'"svce"<blob>="([^"]*)"', result.stdout))
    return sorted(name for name in names if KEYCHAIN_SERVICE.match(name))


def delete_keychain(services: list[str]) -> int:
    deleted = 0
    for service in services:
        for _ in range(10):  # 同名条目可能有多条，删到 44（不存在）为止
            result = subprocess.run(["security", "delete-generic-password", "-s", service], capture_output=True, text=True, check=False)
            if result.returncode == 44:
                break
            if result.returncode != 0:
                raise RuntimeError(f"钥匙串条目删除失败：{service}")
            deleted += 1
    return deleted


def claude_cli() -> str | None:
    return shutil.which("claude")


def run_claude(args: list[str]) -> subprocess.CompletedProcess:
    binary = claude_cli()
    if binary is None:
        raise RuntimeError("找不到 claude 命令，无法执行官方登出与 purge")
    return subprocess.run([binary, *args], capture_output=True, text=True, errors="replace", check=False, timeout=180)


def auth_state() -> dict[str, object] | None:
    """只取 loggedIn / authMethod 两项；完整输出可能含邮箱，不保留不打印。"""
    if claude_cli() is None:
        return None
    try:
        result = run_claude(["auth", "status", "--json"])
        data = json.loads(result.stdout)
    except (OSError, ValueError, subprocess.SubprocessError, RuntimeError):
        return None
    return {key: data.get(key) for key in ("loggedIn", "authMethod")} if isinstance(data, dict) else None


def describe_auth(state: dict[str, object] | None) -> str:
    return "无法读取" if state is None else f"loggedIn={state['loggedIn']}，authMethod={state['authMethod']}"


def purge_sessions(claude: pathlib.Path, backup: pathlib.Path, keep_memory: bool) -> int:
    """`claude purge --all -y`，再从已校验备份恢复各项目的 memory/；返回恢复的目录数。"""
    command = ["purge", "--all", "-y"]
    if run_claude(["purge", "--help"]).returncode != 0:
        command = ["project", "purge", "--all", "-y"]
    result = run_claude(command)
    if result.returncode != 0:
        raise RuntimeError(f"claude purge 失败（退出码 {result.returncode}）")
    restored = 0
    if keep_memory:
        for memory in sorted((backup / "dot-claude" / "projects").glob("*/memory")):
            if memory.is_dir() and not memory.is_symlink():
                destination = claude / "projects" / memory.parent.name / "memory"
                if not destination.exists():
                    shutil.copytree(memory, destination, symlinks=True)
                    restored += 1
    return restored


def clear_ccswitch(db: pathlib.Path) -> dict[str, int]:
    """删除 CC Switch 中本机 Claude 会话解析出的用量行；表或列不存在就跳过。"""
    counts = {}
    with sqlite3.connect(db) as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for table, column, where in CCSWITCH_DELETES:
            if table not in tables or column not in {row[1] for row in conn.execute(f'PRAGMA table_info("{table}")')}:
                continue
            counts[table] = conn.execute(f'DELETE FROM "{table}" WHERE {where}').rowcount
    return counts


def update_simple(claude: pathlib.Path, mode: int) -> None:
    path = claude / "settings.json"
    if mode == 2 and not path.exists():
        return
    data = read_json(path, {})
    if not isinstance(data, dict):
        raise ValueError("settings.json 顶层必须是 JSON object")
    before, updated, env = telemetry(data), dict(data), dict(settings_env(data))
    if mode == 1:
        env["CLAUDE_CODE_SIMPLE"] = "1"
    else:
        env.pop("CLAUDE_CODE_SIMPLE", None)
    updated["env"] = env
    if telemetry(updated) != before:
        raise RuntimeError("精简模式修改触碰了遥测设置")
    if updated != data:
        write_json(path, updated)


def ask_yes(prompt: str, default: bool = False) -> bool:
    value = input(f"{prompt} [{'Y/n' if default else 'y/N'}]：").strip().lower()
    return default if not value else value == "y"


def ask_choice(prompt: str, allowed: set[int]) -> int:
    value = input(prompt).strip() or "0"
    if not value.isdigit() or int(value) not in allowed:
        raise ValueError("输入不在允许范围内，已停止且未修改")
    return int(value)


def ask_days(prompt: str) -> int | None:
    value = input(prompt).strip()
    if not value:
        return None
    if not value.isdigit() or int(value) < 1:
        raise ValueError("保留天数必须是不小于 1 的整数，已停止且未修改")
    return int(value)


def yes_no(flag: bool) -> str:
    return "有" if flag else "无"


def print_audit(home, claude, identity, env, safe, desktop, processes, process_error, ccswitch_db) -> None:
    data = read_json(identity, {}) if identity.is_file() else {}
    present = [key for key in IDENTITY_KEYS if isinstance(data, dict) and key in data]
    try:
        services, keychain_note = keychain_services(), ""
    except (OSError, RuntimeError) as error:
        services, keychain_note = [], f"（无法读取：{error}）"
    state = auth_state()
    privacy = [key for key in PRIVACY_ENV if str(env.get(key, "")) == PRIVACY_ENV[key]]
    print("只读审计（只报告是否存在，不输出任何值）：")
    print(f"- 配置根：{claude}{'（来自 CLAUDE_CONFIG_DIR）' if os.environ.get('CLAUDE_CONFIG_DIR') else ''}；存在：{yes_no(claude.is_dir())}；身份文件：{yes_no(identity.is_file())}")
    print(f"- 设备标识键：{', '.join(present) if present else '无'}；账号块 oauthAccount：{yes_no(isinstance(data, dict) and 'oauthAccount' in data)}")
    print(f"- 带旧身份的 backups 快照：{len(identity_snapshots(claude))} 份；凭证文件 .credentials.json：{yes_no((claude / '.credentials.json').exists())}；钥匙串凭证条目：{len(services)} 条{keychain_note}")
    print(f"- 登录状态：{describe_auth(state)}")
    print(f"- 隐私开关：{len(privacy)}/{len(PRIVACY_ENV)} 已开启；总开关 {TOTAL_SWITCH}：{yes_no(bool(env.get(TOTAL_SWITCH)))}（开启会停自动更新）")
    print(f"- 可自动清理缓存/日志：{len(safe)} 项；Claude Desktop 持久数据：{len(desktop)} 项；Claude.app：{yes_no(APP.exists())}")
    print(f"- 相关进程：{f'无法确认（{process_error}）' if process_error else f'{len(processes)} 个'}；CC Switch 数据库：{yes_no(ccswitch_db.is_file())}")
    print(f"- 精简模式：{'已启用' if str(env.get('CLAUDE_CODE_SIMPLE', '')).lower() in {'1', 'true'} else '未启用'}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="分档审计和清理 Claude 本机状态")
    parser.add_argument("--audit", action="store_true", help="只读审计")
    args = parser.parse_args(argv)
    home, app = pathlib.Path.home(), APP
    claude, identity = config_paths(home)
    settings, ccswitch_db = claude / "settings.json", home / ".cc-switch" / "cc-switch.db"
    if not args.audit:
        try:
            if running_under_claude():
                print("拒绝执行：当前脚本由 Claude Code 启动。请改用 Codex 或普通终端；这里只允许 --audit。", file=sys.stderr)
                return 2
        except ProcessCheckError as error:
            print(f"停止：{error}。未修改任何内容。", file=sys.stderr)
            return 2
    try:
        env = settings_env(read_json(settings, {}))
        safe, desktop = discover(home, claude)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"审计失败：{error}", file=sys.stderr)
        return 2
    process_error = None
    try:
        processes = claude_processes()
    except ProcessCheckError as error:
        if not args.audit:
            print(f"停止：{error}。未修改任何内容。", file=sys.stderr)
            return 2
        processes, process_error = [], str(error)
    print("Claude Cleanup 分四档，逐级包含：" + "；".join(f"{i} {name}" for i, name in enumerate(LEVEL_NAMES)) + "。")
    print("输入最终 CONFIRM 前不会写盘；文件只移入废纸篓，claude purge 与钥匙串删除除外。\n")
    print_audit(home, claude, identity, env, safe, desktop, processes, process_error, ccswitch_db)
    if args.audit:
        return 0
    if not sys.stdin.isatty():
        print("拒绝执行：需要真实 TTY 完成知情确认。", file=sys.stderr)
        return 2

    backup = None
    try:
        print("\n可再生缓存和日志自动纳入清单，不逐项询问。")
        level = ask_choice("档位：0 只清缓存；1 关上报；2 再清设备标识（保留登录）；3 再登出并清本地会话。选择 [0]：", {0, 1, 2, 3})
        total_switch = cleanup_days = None
        project_stats = keep_memory = clear_switch = False
        if level >= 1:
            total_switch = ask_yes(f"同时开启总开关 {TOTAL_SWITCH}？会一并停掉自动更新和安全补丁")
            cleanup_days = ask_days("本地会话保留天数（回车保持现状，手册建议 7，最小 1）：")
        if level >= 2:
            project_stats = ask_yes("清除各项目的上次用量统计（last* 字段；信任与工具授权保留）？")
        if level >= 3:
            keep_memory = ask_yes("purge 会删除各项目 memory/；从备份恢复回来？", default=True)
            if ccswitch_db.is_file():
                clear_switch = ask_yes("删除 CC Switch 中本机 Claude 会话的用量行（不动供应商与 Key）？")
        desktop_mode = ask_choice("Claude Desktop：0 保留；1 清登录态/持久数据；2 再移除应用。选择 [0]：", {0, 1, 2})
        simple_mode = ask_choice("精简模式：0 保持；1 启用 CLAUDE_CODE_SIMPLE；2 移除该设置。选择 [0]：", {0, 1, 2})
        risky = level or desktop_mode or simple_mode
        clean_safe = not processes
        if processes and risky:
            print("\n所选操作要求由你正常退出所有 Claude Code / Claude Desktop；脚本不会 kill 进程。")
            input("退出后按 Enter 重新检查：")
            if claude_processes():
                print("仍检测到 Claude 进程，已取消且未写盘。", file=sys.stderr)
                return 2
            clean_safe = True
        if clear_switch and ccswitch_processes():
            print("CC Switch 正在运行，请先退出再清它的用量行；已取消且未写盘。", file=sys.stderr)
            return 2

        sidecars = existing(claude / name for name in SESSION_SIDECARS) if level >= 2 else []
        snapshots = identity_snapshots(claude) if level >= 2 else []
        logout_files = existing(claude / name for name in LOGOUT_FILES) if level >= 3 else []
        targets = (safe if clean_safe else []) + sidecars + snapshots + logout_files + (desktop if desktop_mode else [])
        if desktop_mode == 2 and app.exists():
            targets.append(app)

        dest = backup_destination(
            input(f"备份位置：在其下建“{BACKUP_NAME}”文件夹，结束时打成压缩包（回车用桌面）："), home, [claude, identity, *targets]
        )
        print("\n最终执行清单：")
        print(f"1. 第一个写操作：完整备份 Claude 配置目录与 .claude.json 到 {dest / BACKUP_NAME} 并逐项校验"
              + ("，另备份 CC Switch 数据库" if clear_switch else "") + f"；全部完成后打成“{BACKUP_NAME}-时间.tar.gz”并读回比对。"
              + "清理包里仍有旧身份、账号和会话，确认无误后由你自行删除。")
        if icloud_synced(dest, home):
            print("   注意：该位置在 iCloud“桌面与文稿”同步范围内，压缩包会上传到 iCloud；不想上传就取消后换个位置。")
        if level >= 1:
            print(f"2. 合并写入隐私开关：{', '.join(PRIVACY_ENV)}、feedbackSurveyRate=0、skipWebFetchPreflight；总开关：{'开' if total_switch else '不动'}；会话保留天数：{cleanup_days or '不动'}")
        if level >= 3:
            print("3. claude auth logout，再 claude purge --all（删除全部项目会话、tasks、debug、file-history 与项目信任项）" + ("，然后从备份恢复各项目 memory/" if keep_memory else "，memory/ 不恢复"))
            print("   删除钥匙串中的 Claude Code 凭证条目")
        if level >= 2:
            print(f"4. 从 .claude.json 删除设备标识与实验缓存键{'及 oauthAccount' if level >= 3 else '（保留 oauthAccount 与登录）'}；项目用量统计：{'清除' if project_stats else '保留'}")
        action = "移入废纸篓" if clean_safe else "因 Claude 正在运行，缓存/日志跳过；其余移入废纸篓"
        print(f"5. {action}（{len(targets)} 项）：")
        for target in targets:
            print(f"   - {target}")
        if clear_switch:
            print("6. 删除 CC Switch 中 app_type=claude 的请求与日用量行，以及指向 .claude 的会话同步记录")
        print(f"7. 精简模式：{('保持', '启用', '移除')[simple_mode]}")
        print("始终不动：skills、plugins、hooks、commands、agents、MCP、CLAUDE.md、settings 中的其他键、任何项目/Git/Codex 数据、CC Switch 的供应商与 Key。")
        if input("完全理解后输入 CONFIRM 开始；其他输入取消：").strip() != "CONFIRM":
            print("已取消，没有修改任何内容。")
            return 1

        before_telemetry = telemetry(read_json(settings, {}))
        kept = protected_names(level) - (PURGED if level >= 3 else set())
        protected_before = [claude / name for name in kept if (claude / name).exists() or (claude / name).is_symlink()]
        backup = create_backup(home, ccswitch_db if clear_switch else None, dest)  # 第一个写操作
        print(f"\n[1/7] 全量备份已校验：{backup}")
        if level >= 1:
            apply_privacy(claude, bool(total_switch), cleanup_days)
        print(f"[2/7] 隐私开关：{'已写入' if level >= 1 else '保持不变'}")
        if level >= 3:
            if run_claude(["auth", "logout"]).returncode != 0:
                raise RuntimeError("claude auth logout 失败")
            restored = purge_sessions(claude, backup, keep_memory)
            deleted = delete_keychain(keychain_services())
            print(f"[3/7] 已登出并 purge；恢复 memory {restored} 个；删除钥匙串条目 {deleted} 条")
        else:
            print("[3/7] 登录与会话保持不变")
        removed = strip_identity(identity, level, project_stats) if level >= 2 else 0
        print(f"[4/7] 身份文件：删除 {removed} 个键" if level >= 2 else "[4/7] 身份保持不变")
        batch = home / ".Trash" / f"claude-cleanup-{dt.datetime.now().strftime('%Y%m%d-%H%M%S-%f')}"
        moved = [move_to_trash(target, set(targets), claude, batch, level) for target in targets]
        print(f"[5/7] 已移入废纸篓：{len(moved)} 项")
        if clear_switch:
            print(f"[6/7] CC Switch 删除：{clear_ccswitch(ccswitch_db)}")
        else:
            print("[6/7] CC Switch 未改动")
        if simple_mode:
            update_simple(claude, simple_mode)
        print(f"[7/7] 精简模式：{('保持', '启用', '移除')[simple_mode]}")

        final_settings = read_json(settings, {})
        if level == 0 and telemetry(final_settings) != before_telemetry:
            raise RuntimeError("遥测设置发生变化，已停止")
        if level >= 1 and not privacy_applied(final_settings):
            raise RuntimeError("隐私开关写入后读回不一致")
        missing = [path for path in protected_before if not (path.exists() or path.is_symlink())]
        if missing:
            raise RuntimeError("受保护路径丢失：" + ", ".join(map(str, missing)))
        left = identity_keys_left(identity, level) if level >= 2 else []
        if left:
            raise RuntimeError("身份键仍在（可能有 Claude 进程写回）：" + ", ".join(left))
        archive = archive_backup(backup)
        backup = None
        print("\n==== 已完成清理 ====")
        print(f"清理包：{archive}")
        if moved:
            print(f"废纸篓批次：{batch}")
        if level >= 3:
            state = auth_state()
            print(f"复查登录：{describe_auth(state)}")
        if level >= 1:
            print("下一步：新开 Claude Code 让开关生效；到 claude.ai 设置关闭 Help Improve our AI models，"
                  + ("并在 Settings > Claude Code 吊销本机 token、按需登出全部会话。" if level >= 3 else "按需吊销不用的 Claude Code token。"))
        print("要彻底去掉旧痕迹：新开 Claude Code 确认正常后，删除上面的清理包并清空废纸篓（脚本没有清空废纸篓）"
              + ("；删除后，purge 掉的会话和钥匙串凭证就无法再恢复。" if level >= 3 else "。"))
        icloud = icloud_synced(archive.parent, home)
        if icloud:
            print(ICLOUD_NOTE)
        notify_done(archive, level, icloud)
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError, json.JSONDecodeError, sqlite3.Error,
            tarfile.TarError) as error:
        print(f"停止：{error}", file=sys.stderr)
        if backup is not None:
            print(f"备份目录（未打包，可用于恢复）：{backup}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
