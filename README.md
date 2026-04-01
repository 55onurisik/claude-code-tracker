# claude-token-tracker

A Claude Code plugin that tracks every prompt and **real token usage** from the Claude API into a local SQLite database. No estimates — actual `input_tokens`, `output_tokens`, and cache token counts from the transcript JSONL files.

## Features

- **Real token data** — reads directly from Claude Code's transcript JSONL files (`~/.claude/projects/`)
- **Zero dependencies** — pure Python stdlib (sqlite3, json, pathlib)
- **Non-blocking hooks** — `UserPromptSubmit` logs synchronously in <10ms; `Stop` runs async
- **Slash commands** — stats dashboard, today's usage, cost report, search, export, reset
- **Token-awareness skill** — Claude automatically answers cost/usage questions using your real data
- **Non-destructive migration** — upgrades the existing DB schema without losing data

## Installation

### Option 1: Clone and symlink (recommended for development)

```bash
git clone https://github.com/YOUR_USER/claude-token-tracker
# Then point Claude Code to the plugin directory in your settings
```

### Option 2: Copy to plugins directory

```bash
cp -r claude-token-tracker ~/.claude/plugins/repos/claude-token-tracker
```

### Option 3: Plugin marketplace (when published)

```
/plugin install gh:YOUR_USER/claude-token-tracker
```

## Slash Commands

| Command | Description |
|---|---|
| `/token-tracker:stats` | Global dashboard: totals, model breakdown, peak hours |
| `/token-tracker:today` | Today's responses with per-turn token/cost breakdown |
| `/token-tracker:cost` | Daily/weekly/monthly cost report with bar chart |
| `/token-tracker:search <keyword>` | Search past prompts by keyword (last 20 results) |
| `/token-tracker:export [csv\|json]` | Export all data to home directory |
| `/token-tracker:reset` | Wipe the database (with confirmation) |

## Database

**Location:** `~/.claude-tracker/tracker.db`

### Schema

```sql
-- Every submitted prompt
prompts (id, timestamp, session_id, prompt, char_count, cwd, transcript_path)

-- Real API token usage per response
responses (id, timestamp, session_id, prompt_id,
           input_tokens, output_tokens,
           cache_creation_tokens, cache_read_tokens, total_tokens,
           cost_usd, model, transcript_path)

-- Per-session aggregates
sessions (session_id, first_seen, last_seen, prompt_count,
          total_input_tokens, total_output_tokens, total_cost_usd)
```

### Views

- `daily_stats` — per-day totals
- `hourly_distribution` — hour-of-day activity
- `model_usage` — breakdown by model

### Example queries

```bash
# Total spend this month
sqlite3 ~/.claude-tracker/tracker.db \
  "SELECT strftime('%Y-%m', timestamp) AS month, SUM(cost_usd) FROM responses GROUP BY month"

# Most expensive sessions
sqlite3 ~/.claude-tracker/tracker.db \
  "SELECT session_id, SUM(cost_usd) AS cost FROM responses GROUP BY session_id ORDER BY cost DESC LIMIT 10"

# Token usage by model
sqlite3 ~/.claude-tracker/tracker.db "SELECT * FROM model_usage"
```

## How It Works

```
User types a prompt
    ↓
UserPromptSubmit hook fires
    → scripts/log_prompt.py reads stdin JSON
    → Inserts into prompts table + upserts sessions table
    ↓
Claude responds (one or more API calls)
    ↓
Stop hook fires (async — doesn't delay Claude's exit)
    → scripts/log_response.py reads stdin JSON (includes transcript_path)
    → parse_transcript.py opens the JSONL file and scans line by line
    → Finds the last non-sidechain assistant entry with message.usage
    → Extracts real: input_tokens, output_tokens, cache_creation_input_tokens, cache_read_input_tokens
    → Calculates cost using pricing table in db.py
    → Inserts into responses table + updates sessions totals
```

## Updating Pricing

Edit the `MODEL_PRICING` dict in `scripts/db.py`:

```python
MODEL_PRICING = {
    "claude-sonnet-4-6": {
        "input": 3.00,        # $/M tokens
        "output": 15.00,
        "cache_creation": 3.75,
        "cache_read": 0.30,
    },
    ...
}
```

## Requirements

- Python 3.8+
- Claude Code with plugin support

## License

MIT
