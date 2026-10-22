# Changelog

All notable changes to this project are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Planned
- OS-native file events watcher (inotify/FSEvents) alongside polling
- Agent hook packs (Claude Code, OpenCode, Cursor, Aider)
- `ctrlz diff <id>` — file-level diff between snapshots

## [0.1.0] - 2026-10-22

### Added
- Filesystem-level snapshots: every file incl. untracked and git-ignored,
  symlinks, and executable bits
- Content-addressed blob store (SHA-256) with per-snapshot JSON manifests
- `init`, `snap`, `undo`, `redo`, `restore`, `log`, `status`, `watch`
- Pre-restore checkpointing — undo is itself undoable
- Polling watcher with debounce for automatic snapshots during agent runs
- Disaster-scenario test suite (rm -rf + overwrite + .env deletion + junk)
