# 安装手册

本手册给 Agent 执行：把本仓库的三个 Skill 安装到 Codex 与 Claude Code 的个人 Skill 目录，并确认可用。各 Skill 的使用规范在其 `SKILL.md`，本手册不重复。

## 步骤

1. **定位仓库**：已有本仓库就进入其根目录；没有时先征得用户同意再克隆。

   ```sh
   git clone https://github.com/Eason412/how-to-use-claude.git
   cd how-to-use-claude
   ```

   成功判据：根目录下有 `skills/claude-cleanup`、`skills/proxy-setup`、`skills/proxy-maintenance` 与 `scripts/link-skills.sh`。

2. **预览链接**：只读，不写盘。

   ```sh
   scripts/link-skills.sh --dry-run
   ```

   成功判据：每个 Skill 在 `~/.codex/skills`（或 `$CODEX_HOME/skills`）与 `~/.claude/skills` 下各有一行 `ok` 或 `would:`。出现 `mv` 表示目标位置已有同名的真实目录，会被移到同级 `skills-backup/`；把这些路径告诉用户。

3. **建立链接**：会写入上述两个个人 Skill 目录，先征得用户同意。

   ```sh
   scripts/link-skills.sh
   ```

   成功判据：输出只有 `ok`、`linked`、`relink`、`backup` 或 `pruned`；`readlink ~/.claude/skills/claude-cleanup` 等指向本仓库 `skills/` 下的对应目录。proxy-setup 与 proxy-maintenance 必须同时存在。

4. **检查清理脚本环境**（仅 macOS 且需要 claude-cleanup 时）：

   ```sh
   uv --version
   cd skills/claude-cleanup
   PYTHONDONTWRITEBYTECODE=1 uv run --no-project python -m unittest discover -s tests
   ```

   成功判据：`uv` 可用，测试输出 `OK`。缺 uv 时按其官方安装方式安装，先征得用户同意。不在此步运行清理；清理按 claude-cleanup 的 `SKILL.md` 另行进行。

5. **私有环境记录**（可选，仅当用户要维护自己的现有链路时）：在 `skills/proxy-maintenance/references/environment.local.md` 写指向用户私有运维文档的链接，内容要求见同目录的 `environment.md`。成功判据：`git check-ignore` 确认该文件被忽略。

   ```sh
   git check-ignore skills/proxy-maintenance/references/environment.local.md
   ```

6. **交付**：告诉用户开启新的 Agent 会话让 Skill 生效，并报告实际链接结果、被移到 `skills-backup/` 的路径（若有）和未执行的步骤。

## 卸载

删除两个个人 Skill 目录下指向本仓库的三个链接即可，仓库与 `skills-backup/` 中的内容不受影响。
