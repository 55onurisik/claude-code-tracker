---
name: token-awareness
description: >
  Use this skill when the user asks about token usage, API costs, how much they have spent,
  how many tokens a session used, "show my usage", "what's my cost today", "how expensive
  was that", "token stats", "am I using too many tokens", Claude Code billing, or any
  question about token consumption or cost optimization.
version: 1.0.0
---

# Token Awareness Skill

The claude-token-tracker plugin automatically logs real token usage and costs from every Claude Code session into `~/.claude-tracker/tracker.db`. Use the slash commands to answer usage questions.

## Quick Reference

| User question | Command to run |
|---|---|
| Overall stats / dashboard | `/token-tracker:stats` |
| Today's usage | `/token-tracker:today` |
| Cost breakdown | `/token-tracker:cost` |
| Find a past prompt | `/token-tracker:search <keyword>` |
| Export data | `/token-tracker:export [csv\|json]` |
| Reset database | `/token-tracker:reset` |

## Inline DB Queries

For specific one-off questions you can query the database directly:

```python
import sqlite3, pathlib
db = pathlib.Path.home() / '.claude-tracker' / 'tracker.db'
conn = sqlite3.connect(str(db))
conn.row_factory = sqlite3.Row
# Query as needed, e.g.:
# conn.execute("SELECT SUM(cost_usd) FROM responses WHERE date(timestamp) = date('now')")
```

## Key Facts

- Token counts are **real values from the Claude API**, not estimates.
- Cache read tokens cost ~90% less than input tokens — heavy cache usage is good.
- The `Stop` hook runs asynchronously: response data appears a few seconds after a turn ends.
- Cost is calculated using the pricing table in `scripts/db.py` (update it if prices change).

## Cost Formula (claude-sonnet-4-6, April 2026)

```
cost = (input_tokens × $3.00 + output_tokens × $15.00
        + cache_creation × $3.75 + cache_read × $0.30) / 1,000,000
```

## Optimization Tips

- Use `/compact` regularly to shrink context — reduces cache_creation_tokens on the next turn.
- Prefer Haiku for simple tasks (8-20× cheaper per token than Sonnet/Opus).
- Long system prompts are cached after the first use — cache_read_tokens are cheap.
