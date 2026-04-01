#!/usr/bin/env python3
import subprocess, pathlib, shutil, sys

REPO = "https://github.com/55onurisik/claude-code-tracker"
DEST = pathlib.Path.home() / ".claude" / "plugins" / "marketplaces" / "claude-plugins-official" / "plugins" / "token-tracker"

DEST.parent.mkdir(parents=True, exist_ok=True)

if DEST.exists():
    print("Updating token-tracker...")
    subprocess.run(["git", "-C", str(DEST), "pull"], check=True)
else:
    print("Installing token-tracker...")
    subprocess.run(["git", "clone", REPO, str(DEST)], check=True)

# Windows: switch to windows-compatible hooks
if sys.platform == "win32":
    shutil.copy(DEST / "hooks" / "hooks.windows.json", DEST / "hooks" / "hooks.json")

print()
print("Done! Restart Claude Code, then run: /token-tracker:stats")
