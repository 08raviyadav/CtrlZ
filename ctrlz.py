#!/usr/bin/env python3
"""
CtrlZ — Ctrl+Z for AI agents.

Coding agents delete, overwrite, and move files — including via bash
(`rm`, `mv`, `cp`), subagents, and tools that built-in checkpoints don't
track. CtrlZ snapshots your whole project at the FILESYSTEM level
(untracked and git-ignored files included) into a content-addressed
store, so one command brings everything back:

    ctrlz init            # start protecting this folder
    ctrlz watch           # auto-snapshot while your agent works
    ctrlz snap -m "pre-refactor"
    ctrlz undo            # restore the previous snapshot
    ctrlz redo            # go forward again
    ctrlz log             # timeline of snapshots + what changed

Zero dependencies. Python 3.9+. One file. Your files never leave disk:
blobs live in .ctrlz/ inside the project.
"""

import argparse
import hashlib
import json
import os
import shutil
import stat
import sys
import time
from datetime import datetime

VERSION = "0.1.0"
STORE_DIR = ".ctrlz"
MAX_FILE_BYTES = 50 * 1024 * 1024  # files larger than this are listed, not stored
SKIP_DIRS = {STORE_DIR, ".git", "__pycache__", "node_modules", ".venv", "venv"}


# ------------------------------------------------------------------ store

def store_paths(root):
    store = os.path.join(root, STORE_DIR)
    return {
        "store": store,
        "blobs": os.path.join(store, "blobs"),
        "snaps": os.path.join(store, "snaps"),
        "state": os.path.join(store, "state.json"),
    }


def load_state(root):
    p = store_paths(root)["state"]
    if not os.path.exists(p):
        return None
    with open(p, "r", encoding="utf-8") as fh:
        return json.load(fh)


def save_state(root, state):
    p = store_paths(root)["state"]
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2)
    os.replace(tmp, p)


def require_init(root):
    state = load_state(root)
    if state is None:
        print("error: CtrlZ is not protecting this folder yet. Run: ctrlz init",
              file=sys.stderr)
        sys.exit(2)
    return state


def blob_path(root, sha):
    return os.path.join(store_paths(root)["blobs"], sha[:2], sha)


def store_blob(root, data):
    sha = hashlib.sha256(data).hexdigest()
    path = blob_path(root, sha)
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "wb") as fh:
            fh.write(data)
        os.replace(tmp, path)
    return sha


# ------------------------------------------------------------------ scan

def collect(root):
    """Map relpath -> entry for every file/symlink under root."""
    entries = {}
    skipped_big = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root)
            try:
                st = os.lstat(full)
            except OSError:
                continue
            if stat.S_ISLNK(st.st_mode):
                entries[rel] = {"type": "link", "target": os.readlink(full)}
            elif stat.S_ISREG(st.st_mode):
                if st.st_size > MAX_FILE_BYTES:
                    skipped_big.append(rel)
                    continue
                with open(full, "rb") as fh:
                    data = fh.read()
                sha = store_blob(root, data)
                entries[rel] = {
                    "type": "file",
                    "sha": sha,
                    "size": st.st_size,
                    "exec": bool(st.st_mode & stat.S_IXUSR),
                }
    return entries, skipped_big


def diff(a, b):
    """What changed going from manifest a to manifest b."""
    added = sorted(set(b) - set(a))
    removed = sorted(set(a) - set(b))
    changed = sorted(k for k in set(a) & set(b) if a[k] != b[k])
    return added, removed, changed


# ------------------------------------------------------------------ snaps

def snap_path(root, snap_id):
    return os.path.join(store_paths(root)["snaps"], snap_id + ".json")


def write_snapshot(root, state, label, quiet=False):
    entries, skipped = collect(root)
    # Truncate any "future" snapshots (we snapshotted, then undid, now act)
    state["snaps"] = state["snaps"][: state["at"] + 1]
    prev = load_manifest(root, state)
    snap_id = f"s{len(state['snaps']) + 1:04d}"
    # ids must stay unique even after truncation
    while os.path.exists(snap_path(root, snap_id)):
        snap_id = f"s{int(snap_id[1:]) + 1:04d}"
    manifest = {
        "id": snap_id,
        "label": label,
        "at": datetime.now().isoformat(timespec="seconds"),
        "files": entries,
    }
    with open(snap_path(root, snap_id), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh)
    state["snaps"].append(snap_id)
    state["at"] = len(state["snaps"]) - 1
    save_state(root, state)
    if not quiet:
        if prev is None:
            print(f"📸 {snap_id} — baseline: {len(entries)} file(s) protected")
        else:
            added, removed, changed = diff(prev["files"], entries)
            print(f"📸 {snap_id} — {label}: "
                  f"+{len(added)} −{len(removed)} ~{len(changed)} changed")
    if skipped:
        print(f"   ⚠ skipped {len(skipped)} file(s) over "
              f"{MAX_FILE_BYTES // (1024 * 1024)}MB: {', '.join(skipped[:3])}"
              f"{'…' if len(skipped) > 3 else ''}")
    return manifest


def load_manifest(root, state, index=None):
    if not state["snaps"]:
        return None
    idx = state["at"] if index is None else index
    if idx < 0 or idx >= len(state["snaps"]):
        return None
    with open(snap_path(root, state["snaps"][idx]), "r", encoding="utf-8") as fh:
        return json.load(fh)


def restore(root, manifest):
    """Make the working tree exactly match the manifest."""
    current, _ = collect(root)
    target = manifest["files"]
    # Delete files that should not exist
    for rel in sorted(set(current) - set(target)):
        full = os.path.join(root, rel)
        try:
            os.remove(full)
        except OSError:
            pass
    # Restore / update target files
    for rel, entry in target.items():
        full = os.path.join(root, rel)
        cur = current.get(rel)
        if cur == entry:
            continue
        os.makedirs(os.path.dirname(full) or root, exist_ok=True)
        if os.path.islink(full) or os.path.exists(full):
            os.remove(full)
        if entry["type"] == "link":
            os.symlink(entry["target"], full)
        else:
            with open(blob_path(root, entry["sha"]), "rb") as fh:
                data = fh.read()
            with open(full, "wb") as out:
                out.write(data)
            if entry.get("exec"):
                os.chmod(full, os.stat(full).st_mode | stat.S_IXUSR)
    # Prune directories left empty by deletions (deepest first)
    for dirpath, dirnames, _ in os.walk(root, topdown=False):
        if os.path.abspath(dirpath) == os.path.abspath(root):
            continue
        if os.path.basename(dirpath) in SKIP_DIRS:
            continue
        try:
            if not os.listdir(dirpath):
                os.rmdir(dirpath)
        except OSError:
            pass


# ------------------------------------------------------------------ commands

def cmd_init(root, _args):
    paths = store_paths(root)
    if load_state(root) is not None:
        print("CtrlZ already protects this folder.")
        return 0
    os.makedirs(paths["blobs"], exist_ok=True)
    os.makedirs(paths["snaps"], exist_ok=True)
    state = {"snaps": [], "at": -1}
    save_state(root, state)
    write_snapshot(root, state, "baseline")
    print("✅ CtrlZ is protecting this folder. Run `ctrlz watch` while your "
          "agent works, or `ctrlz snap` before risky operations.")
    return 0


def cmd_snap(root, args):
    state = require_init(root)
    write_snapshot(root, state, args.message or "manual snapshot")
    return 0


def _checkpoint_if_dirty(root, state):
    """Before undo/redo, preserve any unsnapshotted current state."""
    manifest = load_manifest(root, state)
    current, _ = collect(root)
    if manifest is not None and current != manifest["files"]:
        write_snapshot(root, state, "auto-checkpoint", quiet=True)


def cmd_undo(root, _args):
    state = require_init(root)
    _checkpoint_if_dirty(root, state)
    if state["at"] <= 0:
        print("Nothing to undo — you're at the earliest snapshot.")
        return 0
    state["at"] -= 1
    save_state(root, state)
    manifest = load_manifest(root, state)
    restore(root, manifest)
    print(f"⏪ Undone to {manifest['id']} ({manifest['label']}, "
          f"{manifest['at']}). {len(manifest['files'])} file(s) restored.")
    return 0


def cmd_redo(root, _args):
    state = require_init(root)
    if state["at"] >= len(state["snaps"]) - 1:
        print("Nothing to redo — you're at the latest snapshot.")
        return 0
    state["at"] += 1
    save_state(root, state)
    manifest = load_manifest(root, state)
    restore(root, manifest)
    print(f"⏩ Redone to {manifest['id']} ({manifest['label']}, "
          f"{manifest['at']}).")
    return 0


def cmd_restore(root, args):
    state = require_init(root)
    if args.snapshot not in state["snaps"]:
        print(f"error: no snapshot {args.snapshot}. See: ctrlz log",
              file=sys.stderr)
        return 2
    _checkpoint_if_dirty(root, state)
    state["at"] = state["snaps"].index(args.snapshot)
    save_state(root, state)
    manifest = load_manifest(root, state)
    restore(root, manifest)
    print(f"🎯 Restored {manifest['id']} ({manifest['label']}).")
    return 0


def cmd_log(root, _args):
    state = require_init(root)
    if not state["snaps"]:
        print("No snapshots yet.")
        return 0
    prev = None
    for i, snap_id in enumerate(state["snaps"]):
        with open(snap_path(root, snap_id), "r", encoding="utf-8") as fh:
            m = json.load(fh)
        marker = " ← you are here" if i == state["at"] else ""
        if prev is None:
            delta = f"{len(m['files'])} files"
        else:
            a, r, c = diff(prev["files"], m["files"])
            delta = f"+{len(a)} −{len(r)} ~{len(c)}"
        print(f"{m['id']}  {m['at']}  {m['label']:22} {delta}{marker}")
        prev = m
    return 0


def cmd_status(root, _args):
    state = require_init(root)
    manifest = load_manifest(root, state)
    current, _ = collect(root)
    if manifest and current == manifest["files"]:
        print(f"Clean — working tree matches {manifest['id']} "
              f"({manifest['label']}).")
    else:
        base = manifest["files"] if manifest else {}
        a, r, c = diff(base, current)
        print(f"Unsnapshotted changes: +{len(a)} −{len(r)} ~{len(c)}. "
              f"Run `ctrlz snap` to save them.")
    return 0


def _fingerprint(root):
    fp = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            full = os.path.join(dirpath, name)
            try:
                st = os.lstat(full)
                fp[os.path.relpath(full, root)] = (st.st_mtime_ns, st.st_size)
            except OSError:
                pass
    return fp


def cmd_watch(root, args):
    state = require_init(root)
    print(f"👀 CtrlZ watching {root} — auto-snapshot on change "
          f"(Ctrl+C to stop). Your agent can do its worst.")
    last_fp = _fingerprint(root)
    pending_since = None
    try:
        while True:
            time.sleep(args.interval)
            fp = _fingerprint(root)
            if fp != last_fp:
                last_fp = fp
                pending_since = time.time()
            elif pending_since and time.time() - pending_since >= args.debounce:
                state = load_state(root)  # refresh (may have snapped manually)
                write_snapshot(root, state, "auto (watch)")
                pending_since = None
    except KeyboardInterrupt:
        print("\nStopped watching. Snapshots are in .ctrlz/ — "
              "`ctrlz undo` still works.")
    return 0


# ------------------------------------------------------------------ main

def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="ctrlz",
        description="Ctrl+Z for AI agents — filesystem-level undo for "
                    "everything your agent touches.")
    ap.add_argument("--version", action="version",
                    version=f"ctrlz {VERSION}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="Start protecting this folder")
    p_snap = sub.add_parser("snap", help="Take a snapshot now")
    p_snap.add_argument("-m", "--message", default=None)
    sub.add_parser("undo", help="Restore the previous snapshot")
    sub.add_parser("redo", help="Go forward again after an undo")
    p_restore = sub.add_parser("restore", help="Restore a specific snapshot")
    p_restore.add_argument("snapshot", help="Snapshot id, e.g. s0003")
    sub.add_parser("log", help="Show the snapshot timeline")
    sub.add_parser("status", help="Show unsnapshotted changes")
    p_watch = sub.add_parser("watch", help="Auto-snapshot while you work")
    p_watch.add_argument("--interval", type=float, default=1.0,
                         help="Poll interval in seconds (default 1.0)")
    p_watch.add_argument("--debounce", type=float, default=2.0,
                         help="Quiet seconds before snapshotting (default 2.0)")

    args = ap.parse_args(argv)
    root = os.getcwd()
    handlers = {
        "init": cmd_init, "snap": cmd_snap, "undo": cmd_undo,
        "redo": cmd_redo, "restore": cmd_restore, "log": cmd_log,
        "status": cmd_status, "watch": cmd_watch,
    }
    return handlers[args.cmd](root, args)


if __name__ == "__main__":
    sys.exit(main())
