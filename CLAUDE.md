# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

A Claude Code plugin that captures real token usage and API costs from every Claude Code session into a local SQLite database (`~/.claude-tracker/tracker.db`). It hooks into Claude's `UserPromptSubmit` and `Stop` events to read the actual `message.usage` data from transcript JSONL files.

## Project Rules

- **Python stdlib only** — no pip installs, no third-party packages
- **Python 3.8+** compatible — no `match` statements; use `str | None` only inside `TYPE_CHECKING`
- **Hooks must always exit 0** — never `sys.exit(1)` from hook scripts; failures must never block Claude
- **Token data** is at `entry.message.usage` in transcript JSONL (not top-level); field names are `cache_creation_input_tokens` and `cache_read_input_tokens` (note the `_input_` infix)
- **`costUSD`** in transcripts is always null — cost is calculated via `db.calculate_cost()`
- **`${CLAUDE_PLUGIN_ROOT}`** is the env var for the plugin directory in hooks
- **Windows encoding**: Hook scripts must reconfigure `sys.stdin`/`sys.stdout` to UTF-8 at the top

## Architecture

The plugin lives in `plugins/token-tracker/`. All active code is in that subdirectory.

```
Data flow:
  UserPromptSubmit → log_prompt.py  → INSERT prompts + UPSERT sessions
  Stop (async)     → log_response.py → parse_transcript.py → INSERT responses + UPDATE sessions
```

Key files:
```
scripts/db.py               — schema, migration, get_conn(), calculate_cost(), MODEL_PRICING
scripts/parse_transcript.py — streams JSONL, returns usage from last non-sidechain assistant entry
scripts/log_prompt.py       — UserPromptSubmit hook (<10ms target, synchronous)
scripts/log_response.py     — Stop hook (async, reads transcript JSONL)
hooks/hooks.json            — hook wiring (UserPromptSubmit + Stop)
commands/*.md               — slash commands that run inline Python via Bash
skills/token-awareness/     — auto-activates when user asks about costs/tokens
```

**Pricing**: Update `MODEL_PRICING` dict in `scripts/db.py` when Anthropic changes rates.

**DB migration**: `_migrate()` in `db.py` only adds missing columns (`ALTER TABLE ADD COLUMN`) — never drops or renames. It rebuilds `prompts` only if the old `estimated_tokens NOT NULL` schema is detected.

## Testing

All tests are manual. Run from `plugins/token-tracker/`:

```bash
# Test DB init
python scripts/db.py

# Test prompt hook
echo '{"session_id":"test1","prompt":"hello","cwd":"/tmp","transcript_path":""}' \
  | python scripts/log_prompt.py

# Test response hook with a real transcript
JSONL=$(ls ~/.claude/projects/*/*.jsonl 2>/dev/null | head -1)
echo "{\"session_id\":\"test1\",\"transcript_path\":\"$JSONL\"}" \
  | python scripts/log_response.py

# Test transcript parser standalone
python scripts/parse_transcript.py "$JSONL"

# Safety: bad input must always exit 0
echo "not json" | python scripts/log_prompt.py; echo "Exit: $?"
echo ""         | python scripts/log_response.py; echo "Exit: $?"

# Inspect DB
sqlite3 ~/.claude-tracker/tracker.db "SELECT * FROM responses ORDER BY id DESC LIMIT 5"
sqlite3 ~/.claude-tracker/tracker.db "SELECT * FROM daily_stats LIMIT 7"
```

## Installation

```bash
# Mac/Linux
python3 install.py

# Windows
python install.py
```

The installer uses `claude plugin install` CLI to register the plugin from the local path.
