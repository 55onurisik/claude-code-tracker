#!/usr/bin/env python
"""
UserPromptSubmit hook for claude-token-tracker.

Reads JSON from stdin, logs the user's prompt to the SQLite DB.
MUST always exit 0 — never block Claude.

stdin JSON fields used:
    session_id, user_prompt, cwd, transcript_path
"""
import json
import os
import sys
from datetime import datetime, timezone

# Ensure the scripts directory is on the path regardless of cwd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import get_conn  # noqa: E402


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    try:
        session_id = data.get("session_id") or ""
        user_prompt = data.get("prompt") or data.get("user_prompt") or ""
        cwd = data.get("cwd") or ""
        transcript_path = data.get("transcript_path") or ""
        now = datetime.now(timezone.utc).isoformat()
        char_count = len(user_prompt)

        with get_conn() as conn:
            conn.execute(
                """
                INSERT INTO prompts (timestamp, session_id, prompt, char_count, cwd, transcript_path)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (now, session_id, user_prompt, char_count, cwd, transcript_path),
            )

            conn.execute(
                """
                INSERT INTO sessions (session_id, first_seen, last_seen, prompt_count)
                VALUES (?, ?, ?, 1)
                ON CONFLICT(session_id) DO UPDATE SET
                    last_seen    = excluded.last_seen,
                    prompt_count = prompt_count + 1
                """,
                (session_id, now, now),
            )
    except Exception:
        # Silently swallow — never block the user's prompt
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
