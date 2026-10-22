"""CtrlZ tests — run with: python3 tests/test_ctrlz.py
Plain asserts, no pytest needed (pytest-compatible too).
Simulates the canonical disaster: an agent runs rm -rf, overwrites a file,
deletes a git-ignored .env, and drops junk — then one undo must fix all.
"""
import os
import subprocess
import sys
import tempfile

CTRLZ = os.path.join(os.path.dirname(__file__), "..", "ctrlz.py")


def run(cwd, *argv, expect=0):
    r = subprocess.run([sys.executable, CTRLZ, *argv], cwd=cwd,
                       capture_output=True, text=True)
    assert r.returncode == expect, f"{argv} -> {r.returncode}\n{r.stdout}{r.stderr}"
    return r.stdout


def read(p):
    with open(p, "r", encoding="utf-8") as fh:
        return fh.read()


def test_agent_disaster_and_undo():
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "src"))
        with open(os.path.join(d, "src", "app.py"), "w") as fh:
            fh.write('print("hello")\n')
        with open(os.path.join(d, "README.md"), "w") as fh:
            fh.write("# My Project\n")
        with open(os.path.join(d, ".env"), "w") as fh:  # git-ignored file
            fh.write("SECRET=dev-only\n")

        run(d, "init")

        # The disaster (what an agent with bash access can do)
        subprocess.run(["rm", "-rf", os.path.join(d, "src")], check=True)
        with open(os.path.join(d, "README.md"), "w") as fh:
            fh.write("agent rewrote this\n")
        os.remove(os.path.join(d, ".env"))
        with open(os.path.join(d, "junk.txt"), "w") as fh:
            fh.write("junk")

        run(d, "snap", "-m", "agent run")
        run(d, "undo")

        assert read(os.path.join(d, "src", "app.py")) == 'print("hello")\n'
        assert read(os.path.join(d, "README.md")) == "# My Project\n"
        assert read(os.path.join(d, ".env")) == "SECRET=dev-only\n"
        assert not os.path.exists(os.path.join(d, "junk.txt"))

        # Redo replays the disaster; undo fixes it again
        run(d, "redo")
        assert not os.path.exists(os.path.join(d, "src", "app.py"))
        run(d, "undo")
        assert read(os.path.join(d, "src", "app.py")) == 'print("hello")\n'


def test_unsnapshotted_changes_survive_undo():
    """Undo must checkpoint dirty state first — undo is itself undoable."""
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "a.txt"), "w") as fh:
            fh.write("v1")
        run(d, "init")
        with open(os.path.join(d, "a.txt"), "w") as fh:
            fh.write("v2 (never snapshotted)")
        run(d, "undo")  # at baseline already, but checkpoint must be taken
        out = run(d, "log")
        assert "auto-checkpoint" in out


if __name__ == "__main__":
    test_agent_disaster_and_undo()
    test_unsnapshotted_changes_survive_undo()
    print("All CtrlZ tests passed ✅")
