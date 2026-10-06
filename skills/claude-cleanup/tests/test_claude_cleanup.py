from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import pathlib
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


class CleanupTests(unittest.TestCase):
    def home(self) -> pathlib.Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        home = pathlib.Path(temp.name)
        (home / ".claude").mkdir()
        (home / ".Trash").mkdir()
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
        for name in cleanup.PROTECTED:
            with self.subTest(name=name), self.assertRaises(RuntimeError):
                cleanup.move_to_trash(claude / name, {claude / name}, claude, batch)
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

    def test_identity_rotation_syncs_internal_backups(self):
        home = self.home()
        cleanup.write_json(home / ".claude.json", {"userID": "old", "machineID": "old", "oauthAccount": {}, "keep": 1})
        internal = home / ".claude/backups/.claude.json.backup.1"
        internal.parent.mkdir()
        cleanup.write_json(internal, {"userID": "old", "machineID": "old", "oauthAccount": {}, "keepBackup": 1})
        self.assertEqual(cleanup.rotate_identity(home), 1)
        main, backup = cleanup.read_json(home / ".claude.json"), cleanup.read_json(internal)
        self.assertEqual((main["userID"], main["machineID"]), (backup["userID"], backup["machineID"]))
        self.assertNotIn("oauthAccount", main)
        self.assertNotIn("oauthAccount", backup)
        self.assertEqual((main["keep"], backup["keepBackup"]), (1, 1))

    def test_simple_mode_preserves_telemetry_and_other_settings(self):
        home = self.home()
        path = home / ".claude/settings.json"
        original = {"env": {"DISABLE_TELEMETRY": "1", "TOKEN": "secret"}, "hooks": {"x": ["keep"]}}
        cleanup.write_json(path, original)
        cleanup.update_simple(home, 1)
        updated = cleanup.read_json(path)
        self.assertEqual(updated["env"]["CLAUDE_CODE_SIMPLE"], "1")
        self.assertEqual(cleanup.telemetry(updated), cleanup.telemetry(original))
        self.assertEqual(updated["hooks"], original["hooks"])

    def run_main(self, home: pathlib.Path, answers: list[str], processes: list[str] | None = None) -> tuple[int, list[str]]:
        prompts, iterator = [], iter(answers)

        def answer(prompt=""):
            prompts.append(prompt)
            return next(iterator)

        with (
            mock.patch.object(pathlib.Path, "home", return_value=home),
            mock.patch.object(cleanup, "running_under_claude", return_value=False),
            mock.patch.object(cleanup, "claude_processes", return_value=processes or []),
            mock.patch.object(sys.stdin, "isatty", return_value=True),
            mock.patch("builtins.input", side_effect=answer),
        ):
            return cleanup.main([]), prompts

    def test_safe_cleanup_is_not_a_question_and_cancel_writes_nothing(self):
        home = self.home()
        (home / ".claude/cache").mkdir()
        result, prompts = self.run_main(home, ["n", "n", "0", "0", "NO"])
        self.assertEqual(result, 1)
        self.assertFalse((home / "ClaudeBackups").exists())
        self.assertTrue((home / ".claude/cache").exists())
        self.assertFalse(any("自动清理" in prompt or "可再生缓存" in prompt for prompt in prompts))

    def test_running_claude_skips_safe_cleanup_without_exit_prompt(self):
        home = self.home()
        cache = home / ".claude/cache"
        cache.mkdir()
        result, prompts = self.run_main(home, ["n", "n", "0", "0", "CONFIRM"], ["123 claude"])
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
        result, _ = self.run_main(home, ["n", "n", "1", "0", "CONFIRM"])
        self.assertEqual(result, 0)
        self.assertFalse(data.exists())
        self.assertEqual(len(list((home / ".Trash").glob("claude-cleanup-*/*Claude"))), 1)

    def finished_backups(self, home: pathlib.Path) -> list[pathlib.Path]:
        return [p for p in (home / "ClaudeBackups").glob("claude-cleanup-*") if p.suffix != ".partial"]

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
        return next((home / "ClaudeBackups").glob("claude-cleanup-*.partial"))

    def test_backup_verification_detects_same_size_content_change(self):
        home = self.home()
        self.seed_protected(home)
        self.backup_with_corruption(home, lambda root: (root / "projects/session.jsonl").write_text("sessiom"))

    def test_backup_verification_detects_missing_file_and_changed_symlink(self):
        home = self.home()
        self.seed_protected(home)
        (home / ".claude/link").symlink_to("projects")
        self.backup_with_corruption(home, lambda root: (root / "plugins/demo.json").unlink())
        for partial in (home / "ClaudeBackups").glob("*.partial"):
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
                self.assertFalse((home / "ClaudeBackups").exists())
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
        result, _ = self.run_main(home, ["y", "n", "0", "1", "CONFIRM"])
        self.assertEqual(result, 0)
        backups = list((home / "ClaudeBackups").glob("claude-cleanup-*"))
        self.assertEqual(len(backups), 1)
        self.assertTrue((backups[0] / "dot-claude/projects/session.jsonl").exists())
        self.assertFalse(cache.exists())
        for relative, content in protected.items():
            self.assertEqual((home / ".claude" / relative).read_text(), content)
        final = cleanup.read_json(home / ".claude/settings.json")
        self.assertEqual(cleanup.telemetry(final), cleanup.telemetry(settings))
        self.assertEqual(final["hooks"], settings["hooks"])
        identity, saved = cleanup.read_json(home / ".claude.json"), cleanup.read_json(internal)
        self.assertEqual(identity["userID"], saved["userID"])
        self.assertTrue(identity["keep"] and saved["backupKeep"])


if __name__ == "__main__":
    unittest.main()
