---
description: Show full prompt text by ID
argument-hint: <prompt_id>
allowed-tools: Bash(*)
---

Show full prompt text for ID: **$ARGUMENTS**

```bash
python -c "
import sqlite3, pathlib

db = pathlib.Path.home() / '.claude-tracker' / 'tracker.db'
if not db.exists():
    print('No tracker database found.')
    exit()

arg = '''$ARGUMENTS'''.strip()
if not arg or not arg.isdigit():
    print('Usage: /token-tracker:prompt <id>')
    print('Tip: use /token-tracker:today or /token-tracker:search to find prompt IDs.')
    exit()

conn = sqlite3.connect(str(db))
conn.row_factory = sqlite3.Row

row = conn.execute('''
    SELECT
        p.id, p.timestamp, p.session_id, p.char_count, p.cwd, p.prompt,
        r.input_tokens, r.output_tokens, r.cache_read_tokens,
        r.total_tokens, r.cost_usd, r.model
    FROM prompts p
    LEFT JOIN responses r ON r.prompt_id = p.id
    WHERE p.id = ?
''', (int(arg),)).fetchone()

conn.close()

if not row:
    print(f'No prompt found with ID {arg}.')
    exit()

model_str = (row['model'] or 'unknown').replace('claude-', '').replace('-20', ' 20')
cost_str  = f\"\${row['cost_usd']:.6f}\" if row['cost_usd'] is not None else '(no response logged)'
tok_str   = f\"{row['total_tokens']:,}\" if row['total_tokens'] else '—'

print(f'=== PROMPT #{row[\"id\"]} ===')
print(f'  Time    : {row[\"timestamp\"][:19]}')
print(f'  Session : {row[\"session_id\"]}')
print(f'  Dir     : {row[\"cwd\"]}')
print(f'  Chars   : {row[\"char_count\"]:,}')
print(f'  Model   : {model_str}')
print(f'  Tokens  : in={row[\"input_tokens\"]}  out={row[\"output_tokens\"]}  cache_read={row[\"cache_read_tokens\"]}  total={tok_str}')
print(f'  Cost    : {cost_str}')
print()
print('--- PROMPT TEXT ---')
print(row['prompt'])
print('-------------------')
"
```

Display the full prompt text as shown. If the user wants to find a prompt ID first, suggest `/token-tracker:today` or `/token-tracker:search <keyword>`.
