#!/bin/sh
# Python finder for claude-token-tracker.
# Usage: sh find_python.sh <script.py>
for py in python /usr/bin/python /usr/local/bin/python /opt/homebrew/bin/python; do
    if "$py" --version >/dev/null 2>&1; then
        exec "$py" "$@"
    fi
done
echo "claude-token-tracker: python not found" >&2
exit 0
