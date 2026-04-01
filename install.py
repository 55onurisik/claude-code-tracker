#!/usr/bin/env python3
import subprocess, pathlib, shutil, sys

REPO = "https://github.com/55onurisik/claude-code-tracker"

# Claude Code scans marketplaces/ directory — this is the correct install path
DEST = pathlib.Path.home() / ".claude" / "plugins" / "marketplaces" / "community" / "plugins" / "claude-code-tracker"

DEST.parent.mkdir(parents=True, exist_ok=True)

if DEST.exists():
    print("Updating claude-code-tracker...")
    subprocess.run(["git", "-C", str(DEST), "pull"], check=True)
else:
    print("Installing claude-code-tracker...")
    subprocess.run(["git", "clone", REPO, str(DEST)], check=True)

# Windows: switch to windows-compatible hooks (uses 'python' instead of 'python3')
if sys.platform == "win32":
    shutil.copy(DEST / "hooks" / "hooks.windows.json", DEST / "hooks" / "hooks.json")

print()
print("Done! Restart Claude Code, then test with: /token-tracker:stats")
