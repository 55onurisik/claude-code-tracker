#!/usr/bin/env python
"""
Stop hook for claude-token-tracker.

Reads the session's transcript JSONL, sums token usage across all new
non-sidechain assistant entries since the last recorded turn, and logs to SQLite.

Runs with async: true in hooks.json — does not block Claude's exit.
MUST always exit 0.

stdin JSON fields used:
    session_id, transcript_path
"""
import json
import os
import sys
from datetime import datetime, timezone

if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Ensure the scripts directory is on the path regardless of cwd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import calculate_cost, get_conn  # noqa: E402
from parse_transcript import get_all_usage_entries  # noqa: E402


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

        all_entries = get_all_usage_entries(transcript_path)
        if not all_entries:
            sys.exit(0)

        with get_conn() as conn:
            # Get how many entries were already processed for this session
            sess_row = conn.execute(
                "SELECT last_entry_index FROM sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            last_index = sess_row["last_entry_index"] if sess_row else 0

            new_entries = all_entries[last_index:]
            if not new_entries:
                sys.exit(0)

            # Sum tokens across all new API calls in this turn
            input_tok = sum(e["input_tokens"] for e in new_entries)
            output_tok = sum(e["output_tokens"] for e in new_entries)
            cache_create = sum(e["cache_creation_tokens"] for e in new_entries)
            cache_read = sum(e["cache_read_tokens"] for e in new_entries)
            model = new_entries[-1]["model"]
            total_tokens = input_tok + output_tok + cache_create + cache_read
            cost = calculate_cost(model, input_tok, output_tok, cache_create, cache_read)
            now = datetime.now(timezone.utc).isoformat()
            new_index = len(all_entries)

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
                    last_entry_index    = ?,
                    total_input_tokens  = total_input_tokens  + ?,
                    total_output_tokens = total_output_tokens + ?,
                    total_cost_usd      = total_cost_usd      + ?
                WHERE session_id = ?
                """,
                (now, new_index, input_tok + cache_create + cache_read, output_tok, cost, session_id),
            )
    except Exception:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
