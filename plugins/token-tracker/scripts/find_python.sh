#!/bin/sh
# Portable python finder for claude-token-tracker.
# Tries common python3/python executables across distros and PATH setups.
# Usage: sh find_python.sh <script.py>
for py in python3 python python3.12 python3.11 python3.10 python3.9 \
           /usr/bin/python3 /usr/bin/python \
           /usr/local/bin/python3 /usr/local/bin/python \
           /opt/homebrew/bin/python3 /opt/homebrew/bin/python; do
    if "$py" --version >/dev/null 2>&1; then
        exec "$py" "$@"
    fi
done
echo "claude-token-tracker: python not found" >&2
exit 0
