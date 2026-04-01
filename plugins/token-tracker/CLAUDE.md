# claude-token-tracker

Claude Code plugin that tracks real token usage from API transcripts into SQLite.

## Project Rules

- **Python stdlib only** — no pip installs, no third-party packages
- **Python 3.8+** compatible — no `match` statements, use `str | None` only inside `TYPE_CHECKING`
- **Hooks must always exit 0** — never `sys.exit(1)` or `sys.exit(2)` from hook scripts
- **DB path**: `~/.claude-tracker/tracker.db`
- **Token data** is at `entry.message.usage` in transcript JSONL (not top-level)
- **costUSD** in transcripts is always null — cost is calculated in `db.calculate_cost()`
- **`${CLAUDE_PLUGIN_ROOT}`** is the env var for the plugin directory in hooks

## Architecture

```
scripts/db.py              — schema, migration, get_conn(), calculate_cost()
scripts/parse_transcript.py — streams JSONL line by line, returns last usage entry
scripts/log_prompt.py      — UserPromptSubmit hook (<10ms target)
scripts/log_response.py    — Stop hook (async, reads transcript)
commands/*.md              — slash commands, each runs inline Python via Bash
skills/token-awareness/    — activates when user asks about costs/tokens
hooks/hooks.json           — hook wiring (UserPromptSubmit + Stop)
```

## Testing

```bash
# Test DB initialization
python3 scripts/db.py

# Test prompt hook
echo '{"session_id":"test1","user_prompt":"hello world","cwd":"/tmp","transcript_path":""}' \
  | python3 scripts/log_prompt.py
echo "Exit code: $?"

# Test response hook with a real transcript
JSONL=$(ls ~/.claude/projects/*/*.jsonl 2>/dev/null | head -1)
echo "{\"session_id\":\"test1\",\"transcript_path\":\"$JSONL\"}" \
  | python3 scripts/log_response.py
echo "Exit code: $?"

# Test transcript parser
python3 scripts/parse_transcript.py "$JSONL"

# Test bad input safety (must exit 0)
echo "not json" | python3 scripts/log_prompt.py; echo "Exit: $?"
echo ""         | python3 scripts/log_response.py; echo "Exit: $?"

# Inspect DB
sqlite3 ~/.claude-tracker/tracker.db "SELECT * FROM prompts ORDER BY id DESC LIMIT 5"
sqlite3 ~/.claude-tracker/tracker.db "SELECT * FROM responses ORDER BY id DESC LIMIT 5"
sqlite3 ~/.claude-tracker/tracker.db "SELECT * FROM daily_stats LIMIT 7"
```

## DB Migration Notes

The existing `~/.claude-tracker/tracker.db` has an old schema with `estimated_tokens` columns. The `_migrate()` function in `db.py` adds missing columns using `ALTER TABLE ADD COLUMN` — never drops or renames, so existing data is preserved.
