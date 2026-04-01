---
description: Export token tracking data to CSV or JSON
argument-hint: [csv|json] [output-path]
allowed-tools: Bash(python3:*)
---

Export all tracking data. Arguments: **$ARGUMENTS**

```bash
python3 -c "
import sqlite3, pathlib, json, csv, sys
from datetime import datetime

db = pathlib.Path.home() / '.claude-tracker' / 'tracker.db'
if not db.exists():
    print('No tracker database found.')
    exit()

args = '''$ARGUMENTS'''.strip().split()
fmt = (args[0].lower() if args else 'csv')
if fmt not in ('csv', 'json'):
    fmt = 'csv'

ts = datetime.now().strftime('%Y%m%d_%H%M%S')
default_path = pathlib.Path.home() / f'claude-tracker-export-{ts}.{fmt}'
out_path = pathlib.Path(args[1]) if len(args) > 1 else default_path

conn = sqlite3.connect(str(db))
conn.row_factory = sqlite3.Row

rows = conn.execute('''
    SELECT
        p.id             AS prompt_id,
        p.timestamp      AS prompt_timestamp,
        p.session_id,
        p.prompt,
        p.char_count,
        p.cwd,
        r.id             AS response_id,
        r.timestamp      AS response_timestamp,
        r.input_tokens,
        r.output_tokens,
        r.cache_creation_tokens,
        r.cache_read_tokens,
        r.total_tokens,
        r.cost_usd,
        r.model
    FROM prompts p
    LEFT JOIN responses r ON r.prompt_id = p.id
    ORDER BY p.timestamp
''').fetchall()

conn.close()

data = [dict(row) for row in rows]

if fmt == 'json':
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)
else:
    if data:
        with open(out_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
    else:
        open(out_path, 'w').close()

print(f'Exported {len(data)} records to:')
print(f'  {out_path}')
print(f'  Format : {fmt.upper()}')
if data:
    total_cost = sum(r['cost_usd'] or 0 for r in data)
    print(f'  Total cost in export: \${total_cost:.4f}')
"
```

Confirm the export path and row count to the user. The file will be in the home directory unless a custom path was provided.
