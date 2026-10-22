# FAQ

### How is this different from git?
Git tracks what you *commit*. CtrlZ tracks what *exists* — every file,
tracked or not, committed or not, including `.env` and other ignored
files, and including changes made by bash commands and other programs.
Think of git as the archive and CtrlZ as the undo button. They compose:
most people will gitignore `.ctrlz/` and use both.

### How is this different from my agent's /rewind or checkpoints?
Those are scoped to the agent's own file-editing tools and (per the
vendors' docs) don't cover bash-driven changes, subagents, or external
editors — and they expire. CtrlZ sees the filesystem itself, so the
*source* of a change doesn't matter, and snapshots never expire.

### My agent deleted a file between watch polls. Can CtrlZ save me?
If the file existed in any earlier snapshot, yes — restore brings it
back. If it was created *and* deleted entirely inside one poll+debounce
window (~3s by default) without ever being snapshotted, no tool at this
level could have seen it. Tighten `--interval`/`--debounce`, or
`ctrlz snap` before risky steps.

### Does CtrlZ upload anything?
No. Zero network calls, zero dependencies, everything in `.ctrlz/` on
your disk. Read the one file it ships as and check.

### How much disk does it use?
Each unique file *content* is stored once (content-addressed by
SHA-256). Ten snapshots of a project where 3 files changed = the project
plus 3 small deltas, roughly. Manifests are tiny JSON.

### What about huge files / databases / build artifacts?
Files over 50 MB are skipped and reported. `.git`, `node_modules`, and
virtualenvs are skipped by design. For databases, use your database's
own backup tooling — CtrlZ protects source trees, not live data files.

### Can I undo an undo?
Yes. `ctrlz redo`. And before any undo/restore, CtrlZ checkpoints your
current state, so even an accidental undo is recoverable.

### Which agents does it work with?
All of them, and also with no agent at all. It watches files, not APIs.
