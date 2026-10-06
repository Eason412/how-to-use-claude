from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import pathlib
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SCRIPT = pathlib.Path(__file__).parents[1] / "scripts" / "claude_cleanup.py"
SPEC = importlib.util.spec_from_file_location("claude_cleanup", SCRIPT)
assert SPEC and SPEC.loader
cleanup = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = cleanup
SPEC.loader.exec_module(cleanup)
BACKUPS = "Desktop/Claude清理包"


class CleanupTests(unittest.TestCase):
    def home(self) -> pathlib.Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        home = pathlib.Path(temp.name)
        (home / ".claude").mkdir()
        (home / ".Trash").mkdir()
        (home / "Desktop").mkdir()
        return home

    def seed_protected(self, home: pathlib.Path) -> dict[str, str]:
        files = {
            "projects/session.jsonl": "session",
            "skills/demo/SKILL.md": "skill",
            "plugins/demo.json": "plugin",
            "hooks/guard.sh": "hook",
        }
        for relative, content in files.items():
            target = home / ".claude" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        return files

    def test_backup_contains_all_claude_data_and_identity(self):
        home = self.home()
        files = self.seed_protected(home)
        (home / ".claude.json").write_text('{"userID":"old"}', encoding="utf-8")
        backup = cleanup.create_backup(home)
        for relative, content in files.items():
            self.assertEqual((backup / "dot-claude" / relative).read_text(), content)
        self.assertEqual((backup / "claude.json").read_text(), '{"userID":"old"}')
        manifest = json.loads((backup / "manifest.json").read_text())
        self.assertGreaterEqual(manifest["files"], len(files))
        self.assertTrue(manifest["claudeJsonCopied"])

    def test_deletion_gate_rejects_protected_and_unknown_paths(self):
        home = self.home()
        claude, batch = home / ".claude", home / ".Trash/run"
        for level in range(4):
            for name in cleanup.protected_names(level):
                with self.subTest(level=level, name=name), self.assertRaises(RuntimeError):
                    cleanup.move_to_trash(claude / name, {claude / name}, claude, batch, level)
        with self.assertRaises(RuntimeError):
            cleanup.move_to_trash(home / "Documents", set(), claude, batch)

    def test_safe_cache_moves_without_touching_project(self):
        home = self.home()
        project = home / ".claude/projects/session.jsonl"
        project.parent.mkdir()
        project.write_text("keep")
        cache = home / ".claude/cache"
        cache.mkdir()
        (cache / "entry").write_text("cache")
        destination = cleanup.move_to_trash(cache, {cache}, home / ".claude", home / ".Trash/run")
        self.assertFalse(cache.exists())
        self.assertEqual((destination / "entry").read_text(), "cache")
        self.assertEqual(project.read_text(), "keep")

    def test_level2_strips_identity_but_keeps_login_and_trust(self):
        home = self.home()
        identity = home / ".claude.json"
        projects = {"/repo": {"hasTrustDialogAccepted": True, "allowedTools": ["Bash"], "lastCost": 1, "lastSessionId": "s"}}
        cleanup.write_json(identity, {"userID": "u", "machineID": "m", "firstStartTime": "t", "cachedGrowthBookFeatures": {},
                                      "oauthAccount": {"email": "x"}, "projects": projects, "theme": "dark"})
        self.assertEqual(cleanup.strip_identity(identity, 2, project_stats=True), 6)
        data = cleanup.read_json(identity)
        self.assertEqual(set(data), {"oauthAccount", "projects", "theme"})
        self.assertEqual(data["projects"]["/repo"], {"hasTrustDialogAccepted": True, "allowedTools": ["Bash"]})
        cleanup.strip_identity(identity, 3, project_stats=False)
        self.assertNotIn("oauthAccount", cleanup.read_json(identity))

    def test_identity_snapshot_trash_needs_level2_and_stays_in_backups(self):
        home = self.home()
        claude, batch = home / ".claude", home / ".Trash/run"
        snap = claude / "backups/.claude.json.backup.1"
        other = claude / "backups/settings.json.bak"
        snap.parent.mkdir()
        snap.write_text("{}")
        other.write_text("{}")
        with self.assertRaises(RuntimeError):
            cleanup.move_to_trash(snap, {snap}, claude, batch, 1)
        with self.assertRaises(RuntimeError):
            cleanup.move_to_trash(other, {other}, claude, batch, 2)
        cleanup.move_to_trash(snap, {snap}, claude, batch, 2)
        self.assertFalse(snap.exists())
        self.assertTrue(other.exists() and (claude / "backups").is_dir())

    def test_privacy_merge_keeps_other_settings_and_secrets(self):
        home = self.home()
        path = home / ".claude/settings.json"
        cleanup.write_json(path, {"env": {"TOKEN": "secret", "DISABLE_TELEMETRY": "0"}, "hooks": {"x": ["keep"]}, "model": "m"})
        cleanup.apply_privacy(home / ".claude", total_switch=False, cleanup_days=7)
        data = cleanup.read_json(path)
        self.assertTrue(cleanup.privacy_applied(data))
        self.assertEqual((data["env"]["TOKEN"], data["hooks"], data["model"]), ("secret", {"x": ["keep"]}, "m"))
        self.assertNotIn(cleanup.TOTAL_SWITCH, data["env"])
        self.assertEqual((data["cleanupPeriodDays"], data["feedbackSurveyRate"], data["skipWebFetchPreflight"]), (7, 0, True))
        cleanup.apply_privacy(home / ".claude", total_switch=True, cleanup_days=None)
        data = cleanup.read_json(path)
        self.assertEqual((data["env"][cleanup.TOTAL_SWITCH], data["cleanupPeriodDays"]), ("1", 7))

    def test_ccswitch_clears_only_claude_usage(self):
        home = self.home()
        db = home / "cc-switch.db"
        with sqlite3.connect(db) as conn:
            conn.execute("CREATE TABLE providers (id TEXT, settings_config TEXT)")
            conn.execute("CREATE TABLE proxy_request_logs (app_type TEXT)")
            conn.execute("CREATE TABLE session_log_sync (file_path TEXT)")
            conn.executemany("INSERT INTO proxy_request_logs VALUES (?)", [("claude",), ("codex",)])
            conn.executemany("INSERT INTO session_log_sync VALUES (?)", [("/u/.claude/projects/a.jsonl",), ("/u/.codex/s.jsonl",)])
            conn.execute("INSERT INTO providers VALUES ('p', 'key')")
        self.assertEqual(cleanup.clear_ccswitch(db), {"proxy_request_logs": 1, "session_log_sync": 1})
        with sqlite3.connect(db) as conn:
            self.assertEqual(conn.execute("SELECT app_type FROM proxy_request_logs").fetchall(), [("codex",)])
            self.assertEqual(conn.execute("SELECT count(*) FROM providers").fetchone(), (1,))
            self.assertEqual(conn.execute("SELECT file_path FROM session_log_sync").fetchall(), [("/u/.codex/s.jsonl",)])

    def test_claude_config_dir_moves_identity_file(self):
        home = self.home()
        with mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(home / "alt")}):
            self.assertEqual(cleanup.config_paths(home), (home / "alt", home / "alt/.claude.json"))
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(cleanup.config_paths(home), (home / ".claude", home / ".claude.json"))

    def test_simple_mode_preserves_telemetry_and_other_settings(self):
        home = self.home()
        path = home / ".claude/settings.json"
        original = {"env": {"DISABLE_TELEMETRY": "1", "TOKEN": "secret"}, "hooks": {"x": ["keep"]}}
        cleanup.write_json(path, original)
        cleanup.update_simple(home / ".claude", 1)
        updated = cleanup.read_json(path)
        self.assertEqual(updated["env"]["CLAUDE_CODE_SIMPLE"], "1")
        self.assertEqual(cleanup.telemetry(updated), cleanup.telemetry(original))
        self.assertEqual(updated["hooks"], original["hooks"])

    def run_main(self, home: pathlib.Path, answers: list[str], processes: list[str] | None = None,
                 extra: list | None = None) -> tuple[int, list[str]]:
        prompts, iterator = [], iter(answers)

        def answer(prompt=""):
            prompts.append(prompt)
            return "" if prompt.startswith("备份位置") else next(iterator)  # 默认桌面

        with contextlib.ExitStack() as stack:
            for patch in [
                mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": ""}),
                mock.patch.object(pathlib.Path, "home", return_value=home),
                mock.patch.object(cleanup, "running_under_claude", return_value=False),
                mock.patch.object(cleanup, "claude_processes", return_value=processes or []),
                mock.patch.object(cleanup, "keychain_services", return_value=[]),
                mock.patch.object(cleanup, "auth_state", return_value=None),
                mock.patch.object(cleanup, "notify_done"),
                mock.patch.object(sys.stdin, "isatty", return_value=True),
                mock.patch("builtins.input", side_effect=answer),
                *(extra or []),
            ]:
                stack.enter_context(patch)
            return cleanup.main([]), prompts

    def test_safe_cleanup_is_not_a_question_and_cancel_writes_nothing(self):
        home = self.home()
        (home / ".claude/cache").mkdir()
        result, prompts = self.run_main(home, ["0", "0", "0", "NO"])
        self.assertEqual(result, 1)
        self.assertFalse((home / BACKUPS).exists())
        self.assertTrue((home / ".claude/cache").exists())
        self.assertFalse(any("自动清理" in prompt or "可再生缓存" in prompt for prompt in prompts))

    def test_running_claude_skips_safe_cleanup_without_exit_prompt(self):
        home = self.home()
        cache = home / ".claude/cache"
        cache.mkdir()
        result, prompts = self.run_main(home, ["0", "0", "0", "CONFIRM"], ["123 claude"])
        self.assertEqual(result, 0)
        self.assertTrue(cache.exists())
        self.assertFalse(any("退出后按 Enter" in prompt for prompt in prompts))

    def test_symlinked_parent_cannot_reach_protected_data(self):
        home = self.home()
        claude, batch = home / ".claude", home / ".Trash/run"
        victim = claude / "projects/Claude/session.jsonl"
        victim.parent.mkdir(parents=True)
        victim.write_text("keep")
        (home / "Library").mkdir()
        (home / "Library/Logs").symlink_to(claude / "projects")
        target = home / "Library/Logs/Claude"
        with self.assertRaises(RuntimeError):
            cleanup.move_to_trash(target, {target}, claude, batch)
        self.assertEqual(victim.read_text(), "keep")
        self.assertTrue((home / "Library/Logs").is_symlink())
        self.assertFalse(batch.exists())

    def test_symlink_resolving_to_claude_dir_is_rejected(self):
        home = self.home()
        claude, batch = home / ".claude", home / ".Trash/run"
        (home / "Library").mkdir()
        (home / "Library/Logs").symlink_to(home)
        target = home / "Library/Logs/.claude"
        with self.assertRaises(RuntimeError):
            cleanup.move_to_trash(target, {target}, claude, batch)
        self.assertTrue(claude.is_dir())

    def test_final_symlink_moves_only_the_link(self):
        home = self.home()
        claude, batch = home / ".claude", home / ".Trash/run"
        victim = claude / "projects/session.jsonl"
        victim.parent.mkdir(parents=True)
        victim.write_text("keep")
        (home / "Library/Logs").mkdir(parents=True)
        link = home / "Library/Logs/Claude"
        link.symlink_to(claude / "projects")
        destination = cleanup.move_to_trash(link, {link}, claude, batch)
        self.assertFalse(link.is_symlink())
        self.assertTrue(destination.is_symlink())
        self.assertEqual(victim.read_text(), "keep")

    def test_backup_without_claude_dir_only_copies_what_exists(self):
        home = self.home()
        (home / ".claude").rmdir()
        backup = cleanup.create_backup(home)
        self.assertFalse((backup / "dot-claude").exists())
        self.assertFalse((backup / "claude.json").exists())
        manifest = json.loads((backup / "manifest.json").read_text())
        self.assertFalse(manifest["claudeDirCopied"] or manifest["claudeJsonCopied"])
        (home / ".claude.json").write_text("{}", encoding="utf-8")
        backup = cleanup.create_backup(home)
        self.assertEqual((backup / "claude.json").read_text(), "{}")
        self.assertFalse((backup / "dot-claude").exists())

    def test_desktop_only_run_is_not_blocked_by_backup(self):
        home = self.home()
        (home / ".claude").rmdir()
        data = home / "Library/Application Support/Claude"
        data.mkdir(parents=True)
        (data / "state").write_text("desktop")
        result, _ = self.run_main(home, ["0", "1", "0", "CONFIRM"])
        self.assertEqual(result, 0)
        self.assertFalse(data.exists())
        self.assertEqual(len(list((home / ".Trash").glob("claude-cleanup-*/*Claude"))), 1)

    def finished_backups(self, home: pathlib.Path) -> list[pathlib.Path]:
        return [p for p in (home / BACKUPS).glob("Claude清理包-*") if p.suffix != ".partial"]

    def backup_with_corruption(self, home: pathlib.Path, corrupt) -> pathlib.Path:
        real_copytree = cleanup.shutil.copytree

        def copytree(src, dst, *args, **kwargs):
            result = real_copytree(src, dst, *args, **kwargs)
            if pathlib.Path(dst).name == "dot-claude":  # copytree 递归时也会经过这里
                corrupt(pathlib.Path(dst))
            return result

        with mock.patch.object(cleanup.shutil, "copytree", side_effect=copytree):
            with self.assertRaises(RuntimeError):
                cleanup.create_backup(home)
        self.assertEqual(self.finished_backups(home), [])
        return next((home / BACKUPS).glob("Claude清理包-*.partial"))

    def test_backup_verification_detects_same_size_content_change(self):
        home = self.home()
        self.seed_protected(home)
        self.backup_with_corruption(home, lambda root: (root / "projects/session.jsonl").write_text("sessiom"))

    def test_backup_verification_detects_missing_file_and_changed_symlink(self):
        home = self.home()
        self.seed_protected(home)
        (home / ".claude/link").symlink_to("projects")
        self.backup_with_corruption(home, lambda root: (root / "plugins/demo.json").unlink())
        for partial in (home / BACKUPS).glob("*.partial"):
            cleanup.shutil.rmtree(partial)

        def retarget(root):
            (root / "link").unlink()
            (root / "link").symlink_to("skills")

        self.backup_with_corruption(home, retarget)

    def test_backup_verification_detects_identity_content_change(self):
        home = self.home()
        (home / ".claude.json").write_text('{"userID":"old"}', encoding="utf-8")
        real_copy2 = cleanup.shutil.copy2

        def copy2(src, dst, *args, **kwargs):
            result = real_copy2(src, dst, *args, **kwargs)
            pathlib.Path(dst).write_text('{"userID":"0ld"}', encoding="utf-8")
            return result

        with mock.patch.object(cleanup.shutil, "copy2", side_effect=copy2), self.assertRaises(RuntimeError):
            cleanup.create_backup(home)
        self.assertEqual(self.finished_backups(home), [])

    def failing_ps(self):
        return mock.patch.object(
            cleanup.subprocess, "run", return_value=subprocess.CompletedProcess([], 1, stdout="", stderr="ps: denied")
        )

    def test_process_scan_failure_stops_before_any_write(self):
        home = self.home()
        cache = home / ".claude/cache"
        cache.mkdir()
        cleanup.write_json(home / ".claude/settings.json", {"env": {}})
        before = (home / ".claude/settings.json").read_bytes()
        for under_claude_fails in (True, False):
            with self.subTest(under_claude_fails=under_claude_fails):
                patches = [
                    mock.patch.object(pathlib.Path, "home", return_value=home),
                    mock.patch.object(sys.stdin, "isatty", return_value=True),
                    mock.patch("builtins.input", side_effect=AssertionError("不应提问")),
                    self.failing_ps(),
                ]
                if not under_claude_fails:
                    patches.append(mock.patch.object(cleanup, "running_under_claude", return_value=False))
                with contextlib.ExitStack() as stack:
                    for patch in patches:
                        stack.enter_context(patch)
                    stderr = io.StringIO()
                    with contextlib.redirect_stderr(stderr):
                        self.assertEqual(cleanup.main([]), 2)
                self.assertIn("无法确认", stderr.getvalue())
                self.assertFalse((home / BACKUPS).exists())
                self.assertEqual(list((home / ".Trash").iterdir()), [])
                self.assertTrue(cache.exists())
                self.assertEqual((home / ".claude/settings.json").read_bytes(), before)

    def test_process_scan_failure_only_runs_ps(self):
        home = self.home()
        with (
            mock.patch.object(pathlib.Path, "home", return_value=home),
            mock.patch.object(sys.stdin, "isatty", return_value=True),
            mock.patch("builtins.input", side_effect=AssertionError("不应提问")),
            self.failing_ps() as run,
            contextlib.redirect_stderr(io.StringIO()),
        ):
            self.assertEqual(cleanup.main([]), 2)
        self.assertTrue(run.call_args_list)
        self.assertTrue(all(call.args[0][0] == "ps" for call in run.call_args_list))

    def test_audit_reports_unconfirmed_when_process_scan_fails(self):
        home = self.home()
        out = io.StringIO()
        with (
            mock.patch.object(pathlib.Path, "home", return_value=home),
            self.failing_ps(),
            contextlib.redirect_stdout(out),
        ):
            self.assertEqual(cleanup.main(["--audit"]), 0)
        self.assertIn("无法确认", out.getvalue())

    def test_claude_agent_allows_audit_only(self):
        home = self.home()
        with (
            mock.patch.object(pathlib.Path, "home", return_value=home),
            mock.patch.object(cleanup, "running_under_claude", return_value=True),
            mock.patch.object(cleanup, "claude_processes", return_value=[]),
        ):
            self.assertEqual(cleanup.main([]), 2)
            self.assertEqual(cleanup.main(["--audit"]), 0)

    def test_isolated_full_run_preserves_protected_data_and_telemetry(self):
        home = self.home()
        protected = self.seed_protected(home)
        settings = {"env": {"CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1"}, "hooks": {"x": ["keep"]}}
        cleanup.write_json(home / ".claude/settings.json", settings)
        cleanup.write_json(home / ".claude.json", {"userID": "old", "machineID": "old", "oauthAccount": {}, "keep": True})
        internal = home / ".claude/backups/.claude.json.backup.1"
        internal.parent.mkdir()
        cleanup.write_json(internal, {"userID": "old", "machineID": "old", "backupKeep": True})
        cache = home / ".claude/cache"
        cache.mkdir()
        (cache / "entry").write_text("cache")
        result, _ = self.run_main(home, ["0", "0", "1", "CONFIRM"])
        self.assertEqual(result, 0)
        backups = list((home / BACKUPS).iterdir())
        self.assertEqual([p.name.endswith(".tar.gz") for p in backups], [True])
        self.assertEqual(backups[0].stat().st_mode & 0o777, 0o600)
        entries = cleanup.archive_entries(backups[0])
        self.assertEqual(entries["dot-claude/projects/session.jsonl"][:2], ("file", len("session")))
        self.assertIn("userID", (cleanup.tarfile.open(backups[0]).extractfile(backups[0].name[:-7] + "/claude.json").read().decode()))
        self.assertFalse(cache.exists())
        for relative, content in protected.items():
            self.assertEqual((home / ".claude" / relative).read_text(), content)
        final = cleanup.read_json(home / ".claude/settings.json")
        self.assertEqual(cleanup.telemetry(final), cleanup.telemetry(settings))
        self.assertEqual(final["hooks"], settings["hooks"])
        self.assertEqual(cleanup.read_json(home / ".claude.json")["userID"], "old")
        self.assertTrue(internal.exists())
        self.assertEqual(final["env"]["CLAUDE_CODE_SIMPLE"], "1")

    def seed_level_home(self) -> pathlib.Path:
        home = self.home()
        self.seed_protected(home)
        claude = home / ".claude"
        cleanup.write_json(claude / "settings.json", {"env": {"TOKEN": "secret"}, "hooks": {"x": ["keep"]}})
        cleanup.write_json(home / ".claude.json", {"userID": "old", "machineID": "old", "oauthAccount": {"e": 1}, "keep": True})
        (claude / "backups").mkdir()
        cleanup.write_json(claude / "backups/.claude.json.backup.1", {"userID": "old"})
        (claude / "history.jsonl").write_text("prompt")
        (claude / "projects/demo/memory").mkdir(parents=True)
        (claude / "projects/demo/memory/note.md").write_text("remember")
        (claude / ".credentials.json").write_text("{}")
        return home

    def test_level2_run_keeps_login_and_clears_identity_traces(self):
        home = self.seed_level_home()
        claude = home / ".claude"
        result, _ = self.run_main(home, ["2", "n", "", "y", "0", "0", "CONFIRM"])
        self.assertEqual(result, 0)
        self.assertTrue(cleanup.privacy_applied(cleanup.read_json(claude / "settings.json")))
        identity = cleanup.read_json(home / ".claude.json")
        self.assertNotIn("userID", identity)
        self.assertEqual((identity["oauthAccount"], identity["keep"]), ({"e": 1}, True))
        self.assertFalse((claude / "backups/.claude.json.backup.1").exists() or (claude / "history.jsonl").exists())
        self.assertTrue((claude / "projects/session.jsonl").exists() and (claude / ".credentials.json").exists())
        self.assertTrue((claude / "skills/demo/SKILL.md").exists() and (claude / "backups").is_dir())

    def test_level3_run_logs_out_purges_and_restores_memory(self):
        home = self.seed_level_home()
        claude, calls = home / ".claude", []

        def fake_claude(args):
            calls.append(args)
            if args[:2] == ["purge", "--all"]:
                cleanup.shutil.rmtree(claude / "projects")
            if args == ["auth", "logout"]:
                data = cleanup.read_json(home / ".claude.json")
                data.pop("oauthAccount")
                cleanup.write_json(home / ".claude.json", data)
            return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

        extra = [
            mock.patch.object(cleanup, "run_claude", side_effect=fake_claude),
            mock.patch.object(cleanup, "delete_keychain", return_value=1),
        ]
        result, _ = self.run_main(home, ["3", "n", "7", "n", "y", "0", "0", "CONFIRM"], extra=extra)
        self.assertEqual(result, 0)
        self.assertIn(["auth", "logout"], calls)
        self.assertIn(["purge", "--all", "-y"], calls)
        self.assertEqual((claude / "projects/demo/memory/note.md").read_text(), "remember")
        self.assertFalse((claude / "projects/session.jsonl").exists())
        self.assertFalse((claude / ".credentials.json").exists())
        identity = cleanup.read_json(home / ".claude.json")
        self.assertEqual(identity, {"keep": True})
        self.assertEqual(cleanup.read_json(claude / "settings.json")["cleanupPeriodDays"], 7)
        self.assertTrue((claude / "skills/demo/SKILL.md").exists() and (claude / "hooks/guard.sh").exists())


    def test_archive_keeps_symlinks_and_mismatch_keeps_directory(self):
        home = self.home()
        self.seed_protected(home)
        (home / ".claude/link").symlink_to("skills")
        archive = cleanup.archive_backup(cleanup.create_backup(home))
        self.assertEqual(cleanup.archive_entries(archive)["dot-claude/link"], ("symlink", "skills"))
        self.assertEqual(list((home / BACKUPS).iterdir()), [archive])
        backup = cleanup.create_backup(home)
        real_add = cleanup.tarfile.TarFile.add

        def lossy_add(tar, name, arcname=None, recursive=True, *, filter=None):
            return real_add(tar, name, arcname, recursive, filter=lambda m: None if m.name.endswith("session.jsonl") else m)

        with mock.patch.object(cleanup.tarfile.TarFile, "add", lossy_add), self.assertRaises(RuntimeError):
            cleanup.archive_backup(backup)
        self.assertTrue((backup / "dot-claude/projects/session.jsonl").exists())

    def test_backup_destination_rejects_cleanup_targets_and_relative_paths(self):
        home = self.home()
        claude = home / ".claude"
        (claude / "cache").mkdir()
        self.assertEqual(cleanup.backup_destination("", home, [claude]), home / "Desktop")
        for value in ("relative", str(claude), str(claude / "cache"), str(home / ".Trash"), str(home / "missing")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                cleanup.backup_destination(value, home, [claude])


    def test_archive_named_cleanup_pack_and_done_dialog_reveals_it(self):
        home = self.home()
        archives = [cleanup.archive_backup(cleanup.create_backup(home)) for _ in range(2)]
        self.assertTrue(all(a.name.startswith("Claude清理包-") and a.name.endswith(".tar.gz") for a in archives))
        self.assertEqual(len(set(archives)), 2)
        calls = []

        def run(cmd, **kwargs):
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, stdout="reveal\n", stderr="")

        with mock.patch.object(cleanup.subprocess, "run", side_effect=run):
            cleanup.notify_done(archives[0], 2)
        self.assertEqual(calls[0][:3], ["osascript", "-l", "JavaScript"])
        self.assertIn(str(archives[0].parent), calls[0])
        self.assertEqual(calls[1], ["open", "-R", str(archives[0])])
        calls.clear()
        with mock.patch.object(cleanup.subprocess, "run", side_effect=run):
            cleanup.notify_done(archives[0], 2, icloud=True)
        self.assertIn(cleanup.ICLOUD_NOTE, calls[0])
        self.assertTrue(cleanup.icloud_synced(home / "Desktop", home) is False)
        (home / "Library/Mobile Documents/com~apple~CloudDocs/Desktop").mkdir(parents=True)
        self.assertTrue(cleanup.icloud_synced(archives[0].parent, home))
        with mock.patch.object(cleanup.subprocess, "run", side_effect=OSError("no gui")):
            cleanup.notify_done(archives[0], 2)


if __name__ == "__main__":
    unittest.main()
