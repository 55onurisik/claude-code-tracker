#!/usr/bin/env python3
import subprocess, sys

MARKETPLACE = "55onurisik/claude-code-tracker"
PLUGIN = "token-tracker"

def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout.strip())
    if result.returncode != 0 and result.stderr:
        print(result.stderr.strip())
    return result.returncode

print("Step 1/2 — Adding marketplace...")
code = run(["claude", "plugin", "marketplace", "add", MARKETPLACE])

print("Step 2/2 — Installing plugin...")
code = run(["claude", "plugin", "install", PLUGIN])

if code == 0:
    print()
    print("Done! Restart Claude Code, then run: /token-tracker:stats")
else:
    print()
    print("Something went wrong. Try manually:")
    print(f"  claude plugin marketplace add {MARKETPLACE}")
    print(f"  claude plugin install {PLUGIN}")
