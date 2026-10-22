# Launch Kit — CtrlZ

## Positioning (one line)
**Ctrl+Z for AI agents** — undo *everything* your agent did, including the
bash commands its own checkpoint never saw.

## The demo (recorded — `demo.gif`, ~13.5 seconds)
Terminal, large font:
1. `ctrlz init` → baseline
2. Open a small project; show `src/` and `.env`
3. Simulate the agent: `rm -rf src && rm .env`
4. Beat. `ctrlz undo`
5. `ls src` — everything back. End card: repo URL.

GIF goes at the very top of the README and in every launch post.

## Show HN
**Title:** `Show HN: CtrlZ – Ctrl+Z for AI agents (undoes bash rm, subagent edits, everything on disk)`

**Body sketch:** Anthropic's docs admit /rewind doesn't track bash
rm/mv/cp or subagent edits and snapshots expire in ~30 days; git-based
snapshots miss untracked/ignored files like .env. CtrlZ snapshots the
filesystem itself into a content-addressed store — one zero-dependency
Python file. Agent deletes src/, one `ctrlz undo`, byte-for-byte back.
Undo checkpoints first, so it's undoable itself. Limitations stated
(polling watcher, working-tree only). Disaster test in the repo.

Post Tue–Thu ~13:00–16:00 UTC (8–9am ET window). First comment: the
/rewind documentation quote + link, invite people to share their worst
agent-destruction story (every dev has one — that's the thread fuel).

## Reddit
- r/ClaudeAI, r/ChatGPTCoding, r/programming — title:
  `Claude Code's /rewind doesn't track bash deletions. So I built Ctrl+Z for agents.`
  Lead with the demo GIF, tool second, limitations up front.
- r/LocalLLaMA — agent-safety angle.

## X thread
1. `Your agent's undo button has a blind spot: bash. rm -rf isn't tracked. .env isn't tracked. I fixed that 🧵`
2. Demo GIF.
3. `Filesystem-level snapshots. Content-addressed. One file, zero deps. Undo itself is undoable.`
4. `Works with every agent because it watches files, not APIs.` + repo link.

## Repo setup checklist
- [ ] Topics: `ai-agents`, `claude-code`, `developer-tools`, `backup`,
      `undo`, `python`, `cli`
- [ ] Pin on profile, star it
- [ ] Social preview image: the undo terminal shot
- [ ] Reply to everything in the first 48h
