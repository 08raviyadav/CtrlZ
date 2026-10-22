# CtrlZ Usage Guide

## Commands

| Command | What it does |
|---|---|
| `ctrlz init` | Creates `.ctrlz/` in the current folder and takes a baseline snapshot |
| `ctrlz watch [--interval 1.0] [--debounce 2.0]` | Polls the tree; snapshots after changes settle for `--debounce` seconds |
| `ctrlz snap [-m "label"]` | Takes a snapshot immediately |
| `ctrlz undo` | Checkpoints current state, then restores the previous snapshot |
| `ctrlz redo` | Moves one snapshot forward again |
| `ctrlz restore <id>` | Jumps to a specific snapshot (ids from `ctrlz log`) |
| `ctrlz log` | Timeline of snapshots with +added / −removed / ~changed counts |
| `ctrlz status` | Shows unsnapshotted changes vs the current snapshot |
| `ctrlz --version` | Prints the version |

## A typical agent session

```bash
cd my-app
ctrlz init
ctrlz watch &            # or in a second terminal

# start your agent, let it work…
# something went sideways:

ctrlz log                # find the last good snapshot
ctrlz undo               # or: ctrlz restore s0007
```

## Agent recipes

CtrlZ needs **no integration** — it watches the filesystem. But you can
make it automatic:

**Any agent with a shell:** tell it (or your wrapper script) to run
`ctrlz snap -m "pre-task"` before each task and keep `ctrlz watch`
running during the session.

**Claude Code:** add a `SessionStart` hook in `.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      { "hooks": [{ "type": "command",
                    "command": "ctrlz snap -m session-start || true" }] }
    ]
  }
}
```

**CI / scripts:** snapshot before codegen steps in your pipeline:

```yaml
- run: python3 ctrlz.py init && python3 ctrlz.py snap -m pre-codegen
- run: ./run-codegen.sh
# on failure, a later step can run: python3 ctrlz.py undo
```

## What gets snapshotted

- Regular files up to 50 MB each, symlinks, and executable bits
- **Including** untracked and git-ignored files (`.env`, local configs)

Skipped: `.ctrlz/` itself, `.git/`, `node_modules/`, `__pycache__`,
`.venv/`/`venv/`, and files over 50 MB (listed as skipped in output).

## Storage

`.ctrlz/blobs/` — file contents, named by SHA-256, stored once each.
`.ctrlz/snaps/` — one small JSON manifest per snapshot.
`.ctrlz/state.json` — the snapshot list and your position in it.

Snapshots-after-undo behaviour: if you undo and then take a new snapshot,
the "future" branch is truncated (linear history, like most undo systems)
— but undo/redo never destroy the checkpoint of the state you undid from.

To stop protecting a folder, just delete `.ctrlz/`. Add `.ctrlz/` to your
`.gitignore` — it's a local safety net, not source.
