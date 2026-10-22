<div align="center">

# ⌨️ CtrlZ

**Ctrl+Z for AI agents.**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org)
[![Dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen)](#)

Your coding agent just ran `rm -rf src`. Its built-in checkpoint didn't see it.
**CtrlZ did.**

![CtrlZ demo — rm -rf src, then ctrlz undo brings everything back](demo.gif)

</div>

---

## The 10-second demo

```bash
$ ctrlz init                  # start protecting this folder
📸 s0001 — baseline: 4 file(s) protected
✅ CtrlZ is protecting this folder. Run `ctrlz watch` while your agent works, or `ctrlz snap` before risky operations.

# …your agent works. Then it has a moment:
$ rm -rf src && rm .env       # or the agent does. same thing.

$ ctrlz undo
⏪ Undone to s0001 (baseline, 2026-10-22T09:35:04). 4 file(s) restored.

# src/ is back. .env is back. Byte for byte.
```

## Why built-in checkpoints aren't enough

Agent checkpoints are scoped to what the agent's *file tools* did. Real
agents have bash. Per Anthropic's own documentation, Claude Code's
`/rewind` does **not** track files changed by bash commands (`rm`, `mv`,
`cp`), subagent edits, or external tools — and its snapshots expire after
~30 days. Git-based snapshots (OpenCode and friends) only see what's
tracked: your `.env`, your untracked drafts, and your git-ignored files
are invisible to them.

CtrlZ works at the **filesystem level**. If it changed on disk, CtrlZ saw
it — no matter which tool, subagent, or shell command changed it.

| | CtrlZ | Agent checkpoints (`/rewind`) | git stash / reset |
|---|---|---|---|
| Bash `rm`/`mv`/`cp` damage | ✅ | ❌ | partial |
| Subagent / external edits | ✅ | ❌ | partial |
| Untracked + git-ignored files (`.env`) | ✅ | ❌ | ❌ |
| Needs a git repo | ❌ | ❌ | ✅ |
| Snapshots expire | never | ~30 days | n/a |
| Undo the undo (redo) | ✅ | ❌ | ❌ |

## Install

One file. Zero dependencies. Python 3.9+.

```bash
curl -O https://raw.githubusercontent.com/08raviyadav/ctrlz/main/ctrlz.py
chmod +x ctrlz.py
sudo ln -s "$PWD/ctrlz.py" /usr/local/bin/ctrlz    # or any PATH dir
```

## Usage

```bash
cd your-project
ctrlz init            # baseline snapshot — 1 second
ctrlz watch           # auto-snapshot on every change while your agent works
```

Then, whatever happens:

```bash
ctrlz undo            # restore the previous snapshot
ctrlz redo            # go forward again
ctrlz log             # timeline: every snapshot + what changed (+/−/~)
ctrlz restore s0003   # jump to a specific snapshot
ctrlz status          # unsnapshotted changes right now
ctrlz snap -m "before the big refactor"   # manual snapshot
```

**Undo is safe by design:** before restoring, CtrlZ checkpoints your
current state — so an undo is itself undoable with `ctrlz redo`.

## How it works

- Snapshots are **manifests** (path → SHA-256 + mode) over a
  **content-addressed blob store** in `.ctrlz/` inside your project.
  Unchanged files are stored once, so snapshots are cheap.
- `watch` polls the tree and snapshots after changes settle (debounced),
  which is why bash operations and subagent edits are captured — nothing
  integrates with the agent at all.
- Restore deletes files that shouldn't exist, rewrites changed/deleted
  files from blobs, restores symlinks and executable bits, and prunes
  directories left empty.
- Files over 50 MB are listed as skipped (not stored). `.git`,
  `node_modules`, and virtualenvs are skipped. Everything stays on your
  disk — CtrlZ makes zero network calls.

Full details: [docs/USAGE.md](docs/USAGE.md) · [docs/FAQ.md](docs/FAQ.md)

## Works with every agent

CtrlZ doesn't care which agent you run — Claude Code, OpenCode, Cursor,
Aider, a hand-rolled LangChain loop, or a human having a bad day. If it
touches files, CtrlZ can undo it. Agent-specific hook recipes are in the
[usage guide](docs/USAGE.md#agent-recipes).

## Honest limitations

- It's a safety net for your **working tree**, not a backup system: if
  the disk dies, `.ctrlz/` dies with it. Push your code somewhere.
- Polling watcher (1s default) — a file created and deleted inside the
  debounce window between polls may never be snapshotted. Manual
  `ctrlz snap` before risky operations removes all doubt.
- Not a replacement for git. It's the thing that saves you in the 30
  seconds *before* you'd think to commit.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The roadmap's big items:
OS-native file events (no polling), per-agent hook packs, snapshot
diffing/blame, and optional encrypted off-site blob sync.

## License

[MIT](LICENSE) © 2026 Ravi Yadav
