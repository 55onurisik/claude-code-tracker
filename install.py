#!/usr/bin/env python3
import subprocess, pathlib, shutil, sys

REPO = "https://github.com/55onurisik/claude-code-tracker"
DEST = pathlib.Path.home() / ".claude" / "plugins" / "repos" / "claude-code-tracker"

if DEST.exists():
    print("Updating...")
    subprocess.run(["git", "-C", str(DEST), "pull"], check=True)
else:
    print("Installing...")
    subprocess.run(["git", "clone", REPO, str(DEST)], check=True)

if sys.platform == "win32":
    shutil.copy(DEST / "hooks" / "hooks.windows.json", DEST / "hooks" / "hooks.json")

print("\nDone! Restart Claude Code, then run: /token-tracker:stats")
