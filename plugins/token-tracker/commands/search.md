---
description: Search past prompts by keyword
argument-hint: <keyword>
allowed-tools: Bash(python3:*)
---

Search for prompts matching: **$ARGUMENTS**

```bash
python3 -c "
import sqlite3, pathlib, sys

db = pathlib.Path.home() / '.claude-tracker' / 'tracker.db'
if not db.exists():
    print('No tracker database found.')
    exit()

keyword = '''$ARGUMENTS'''.strip()
if not keyword:
    print('Usage: /token-tracker:search <keyword>')
    print('Example: /token-tracker:search \"refactor\"')
    exit()

conn = sqlite3.connect(str(db))
conn.row_factory = sqlite3.Row

rows = conn.execute('''
    SELECT
        p.id,
        p.timestamp,
        SUBSTR(p.prompt, 1, 120)          AS preview,
        p.cwd,
        p.session_id,
        r.total_tokens,
        r.cost_usd,
        r.model
    FROM prompts p
    LEFT JOIN responses r ON r.prompt_id = p.id
    WHERE p.prompt LIKE ?
    ORDER BY p.timestamp DESC
    LIMIT 20
''', (f'%{keyword}%',)).fetchall()

total = conn.execute(
    'SELECT COUNT(*) FROM prompts WHERE prompt LIKE ?', (f'%{keyword}%',)
).fetchone()[0]

conn.close()

print(f'Search: \"{keyword}\"  —  {total} total match(es), showing last {min(len(rows), 20)}')
print()

if not rows:
    print('No prompts found matching that keyword.')
else:
    for row in rows:
        cost_str   = f'\${row[\"cost_usd\"]:.6f}' if row['cost_usd'] is not None else '(no response logged)'
        tokens_str = f'{row[\"total_tokens\"]:,}' if row['total_tokens'] else '—'
        model_str  = (row['model'] or 'unknown').replace('claude-', '')
        preview    = row['preview'] or ''
        suffix     = '...' if len(preview) == 120 else ''
        print(f'[{row[\"id\"]}] {row[\"timestamp\"][:19]}  {row[\"cwd\"]}')
        print(f'     {preview}{suffix}')
        print(f'     tokens={tokens_str}  cost={cost_str}  model={model_str}')
        print()
"
```

Present the search results. Offer to refine or expand the search if needed.
