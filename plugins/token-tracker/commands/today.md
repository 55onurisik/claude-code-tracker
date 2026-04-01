---
description: Show today's prompts with real token counts and costs
allowed-tools: Bash(*)
---

Run this command to show today's usage from the tracker database:

```bash
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null || echo python3)
"$PYTHON" -c "
import sqlite3, pathlib
from datetime import date

db = pathlib.Path.home() / '.claude-tracker' / 'tracker.db'
if not db.exists():
    print('No tracker database found. Submit a prompt first to start tracking.')
    exit()

conn = sqlite3.connect(str(db))
conn.row_factory = sqlite3.Row
today = date.today().isoformat()

summary = conn.execute('''
    SELECT
        COUNT(*)                              AS cnt,
        COALESCE(SUM(total_tokens), 0)        AS tokens,
        COALESCE(SUM(input_tokens), 0)        AS input_tok,
        COALESCE(SUM(output_tokens), 0)       AS output_tok,
        COALESCE(SUM(cache_read_tokens), 0)   AS cache_read,
        COALESCE(SUM(cost_usd), 0)            AS cost
    FROM responses WHERE date(timestamp) = ?
''', (today,)).fetchone()

print(f'=== TODAY ({today}) ===')
print(f'  Responses  : {summary[\"cnt\"]}')
print(f'  Input tok  : {summary[\"input_tok\"]:,}')
print(f'  Output tok : {summary[\"output_tok\"]:,}')
print(f'  Cache read : {summary[\"cache_read\"]:,}')
print(f'  Total tok  : {summary[\"tokens\"]:,}')
print(f'  Total cost : \${summary[\"cost\"]:.6f}')
print()

rows = conn.execute('''
    SELECT
        r.timestamp,
        COALESCE(SUBSTR(p.prompt, 1, 80), \"(no prompt)\") AS preview,
        r.input_tokens,
        r.output_tokens,
        r.cache_read_tokens,
        r.total_tokens,
        r.cost_usd,
        r.model
    FROM responses r
    LEFT JOIN prompts p ON r.prompt_id = p.id
    WHERE date(r.timestamp) = ?
    ORDER BY r.timestamp ASC
''', (today,)).fetchall()

if not rows:
    print('No responses logged today yet.')
    print('(The Stop hook runs async — give it a moment after your last prompt.)')
else:
    for i, row in enumerate(rows, 1):
        model_short = (row['model'] or 'unknown').replace('claude-', '').replace('-20', ' 20')
        cost_str = f'\${row[\"cost_usd\"]:.6f}' if row['cost_usd'] is not None else '(pending)'
        tok_str  = f'{row[\"total_tokens\"]:,}' if row['total_tokens'] else '?'
        print(f'[{i:02d}] {row[\"timestamp\"][:19]}  {model_short}')
        print(f'     Prompt : {row[\"preview\"]}...' if len(row['preview'] or '') == 80 else f'     Prompt : {row[\"preview\"]}')
        print(f'     Tokens : in={row[\"input_tokens\"]:,}  out={row[\"output_tokens\"]:,}  cache_read={row[\"cache_read_tokens\"]:,}  total={tok_str}')
        print(f'     Cost   : {cost_str}')
        print()

conn.close()
"
```

Display the output. If no responses appear yet, the async Stop hook may still be processing — run `/token-tracker:today` again after a moment.
