# claude-code-tracker

A Claude Code plugin that tracks every prompt and **real token usage** from the Claude API into a local SQLite database. No estimates — actual `input_tokens`, `output_tokens`, and cache token counts from the transcript JSONL files.

## Features

- **Real token data** — reads directly from Claude Code's transcript JSONL files (`~/.claude/projects/`)
- **Zero dependencies** — pure Python stdlib (sqlite3, json, pathlib)
- **Non-blocking hooks** — `UserPromptSubmit` logs synchronously in <10ms; `Stop` runs async
- **Slash commands** — stats dashboard, today's usage, cost report, search, export, reset
- **Token-awareness skill** — Claude automatically answers cost/usage questions using your real data
- **Works on Mac, Linux, and Windows**

## Requirements

- Python 3.8+
- Claude Code
- Git

---

## Installation

### Mac / Linux

Open Terminal and run:

```bash
curl -sL https://raw.githubusercontent.com/55onurisik/claude-code-tracker/main/install.sh | bash
```

Or manually:

```bash
git clone https://github.com/55onurisik/claude-code-tracker ~/.claude/plugins/repos/claude-code-tracker
```

Then **restart Claude Code**.

---

### Windows

1. Make sure [Python](https://www.python.org/downloads/) and [Git](https://git-scm.com/) are installed
2. Download and run `install.bat`:

```
curl -o install.bat https://raw.githubusercontent.com/55onurisik/claude-code-tracker/main/install.bat
install.bat
```

Or manually in PowerShell:

```powershell
git clone https://github.com/55onurisik/claude-code-tracker "$env:USERPROFILE\.claude\plugins\repos\claude-code-tracker"
copy "$env:USERPROFILE\.claude\plugins\repos\claude-code-tracker\hooks\hooks.windows.json" "$env:USERPROFILE\.claude\plugins\repos\claude-code-tracker\hooks\hooks.json"
```

Then **restart Claude Code**.

---

## Verify Installation

After restarting Claude Code, run:

```
/token-tracker:stats
```

Submit a few prompts, then:

```
/token-tracker:today
```

---

## Slash Commands

| Command | Description |
|---|---|
| `/token-tracker:stats` | Global dashboard: totals, model breakdown, peak hours |
| `/token-tracker:today` | Today's responses with per-turn token/cost breakdown |
| `/token-tracker:cost` | Daily/weekly/monthly cost report with bar chart |
| `/token-tracker:search <keyword>` | Search past prompts by keyword (last 20 results) |
| `/token-tracker:export [csv\|json]` | Export all data to home directory |
| `/token-tracker:reset` | Wipe the database (with confirmation) |

---

## Database

**Location:**
- Mac/Linux: `~/.claude-tracker/tracker.db`
- Windows: `C:\Users\<username>\.claude-tracker\tracker.db`

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

**Mac/Linux:**
```bash
sqlite3 ~/.claude-tracker/tracker.db "SELECT * FROM daily_stats LIMIT 7"
sqlite3 ~/.claude-tracker/tracker.db "SELECT * FROM model_usage"
```

**Windows (PowerShell):**
```powershell
sqlite3 "$env:USERPROFILE\.claude-tracker\tracker.db" "SELECT * FROM daily_stats LIMIT 7"
```

---

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
    → Extracts real: input_tokens, output_tokens, cache tokens
    → Calculates cost using pricing table in db.py
    → Inserts into responses table + updates sessions totals
```

---

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

---

## License

MIT
