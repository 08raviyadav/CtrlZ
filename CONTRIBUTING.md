# Contributing to CtrlZ

CtrlZ's promise is narrow and absolute: **if it changed on disk, one
command brings it back.** Contributions that protect that promise are
the most valuable ones here.

## High-value contributions

- **Agent hook packs** — tested recipes that auto-snapshot around agent
  sessions (Claude Code, OpenCode, Cursor, Aider, Codex, custom loops).
- **Watcher improvements** — OS-native file events (inotify / FSEvents /
  ReadDirectoryChangesW) to replace or back the polling watcher.
- **Restore edge cases** — permissions, ownership, xattrs, hardlinks,
  weird filenames, huge trees. Every edge case needs a test.
- **Performance** — snapshotting a 100k-file monorepo should still feel
  instant. Profiles + fixes welcome.

## Ground rules

- **Zero dependencies, forever.** One stdlib-only Python file is the
  product's whole charm. PRs adding dependencies will be declined.
- **Undo must never lose data.** Any change to restore/undo logic must
  preserve the invariant: before a restore, the current state is
  checkpointed. Tests must prove it.
- Every behaviour change ships with a test in `tests/` (plain asserts,
  `python3 tests/test_ctrlz.py`).

## Workflow

Branch from `main`, keep PRs single-purpose, and include before/after
output of the disaster test (`tests/test_ctrlz.py`) when you touch the
snapshot/restore engine.
