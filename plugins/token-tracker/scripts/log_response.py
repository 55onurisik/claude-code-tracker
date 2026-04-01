#!/usr/bin/env python3
"""
Stop hook for claude-token-tracker.

Reads the session's transcript JSONL, extracts the real token usage from
the last non-sidechain assistant entry, and logs it to the SQLite DB.

Runs with async: true in hooks.json — does not block Claude's exit.
MUST always exit 0.

stdin JSON fields used:
    session_id, transcript_path
"""
import json
import os
import sys
from datetime import datetime, timezone

# Ensure the scripts directory is on the path regardless of cwd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import calculate_cost, get_conn  # noqa: E402
from parse_transcript import get_last_usage  # noqa: E402


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    try:
        session_id = data.get("session_id") or ""
        transcript_path = data.get("transcript_path") or ""

        if not transcript_path:
            sys.exit(0)

        usage = get_last_usage(transcript_path)
        if not usage:
            sys.exit(0)

        input_tok = usage["input_tokens"]
        output_tok = usage["output_tokens"]
        cache_create = usage["cache_creation_tokens"]
        cache_read = usage["cache_read_tokens"]
        model = usage["model"]
        total_tokens = input_tok + output_tok + cache_create + cache_read
        cost = calculate_cost(model, input_tok, output_tok, cache_create, cache_read)
        now = datetime.now(timezone.utc).isoformat()

        with get_conn() as conn:
            # Best-effort: find the most recent prompt for this session
            row = conn.execute(
                "SELECT id FROM prompts WHERE session_id = ? ORDER BY id DESC LIMIT 1",
                (session_id,),
            ).fetchone()
            prompt_id = row["id"] if row else None

            conn.execute(
                """
                INSERT INTO responses (
                    timestamp, session_id, prompt_id,
                    input_tokens, output_tokens,
                    cache_creation_tokens, cache_read_tokens,
                    total_tokens, cost_usd, model, transcript_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now, session_id, prompt_id,
                    input_tok, output_tok,
                    cache_create, cache_read,
                    total_tokens, cost, model, transcript_path,
                ),
            )

            conn.execute(
                """
                UPDATE sessions SET
                    last_seen           = ?,
                    total_input_tokens  = total_input_tokens  + ?,
                    total_output_tokens = total_output_tokens + ?,
                    total_cost_usd      = total_cost_usd      + ?
                WHERE session_id = ?
                """,
                (now, input_tok, output_tok, cost, session_id),
            )
    except Exception:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
