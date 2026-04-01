---
description: Reset (wipe) the token tracker database after explicit confirmation
allowed-tools: Bash(*)
---

**WARNING: This will permanently delete all tracked prompt and token data.**

First, show the user what will be deleted:

```bash
python -c "
import sqlite3, pathlib

db = pathlib.Path.home() / '.claude-tracker' / 'tracker.db'
if not db.exists():
    print('Database does not exist — nothing to reset.')
    exit()

conn = sqlite3.connect(str(db))
conn.row_factory = sqlite3.Row

p = conn.execute('SELECT COUNT(*) FROM prompts').fetchone()[0]
r = conn.execute('SELECT COUNT(*) FROM responses').fetchone()[0]
s = conn.execute('SELECT COUNT(*) FROM sessions').fetchone()[0]
cost = conn.execute('SELECT COALESCE(SUM(cost_usd), 0) FROM responses').fetchone()[0]
first = conn.execute('SELECT MIN(timestamp) FROM prompts').fetchone()[0]
last  = conn.execute('SELECT MAX(timestamp) FROM prompts').fetchone()[0]
conn.close()

print('The following data will be permanently deleted:')
print(f'  Prompts  : {p:,}')
print(f'  Responses: {r:,}')
print(f'  Sessions : {s:,}')
print(f'  Total tracked spend: \${cost:.4f}')
if first:
    print(f'  Date range: {first[:10]} to {last[:10]}')
"
```

Ask the user to explicitly type "yes" or "confirm" to proceed. **Do not run the deletion without this confirmation.**

If the user confirms, run:

```bash
python -c "
import sqlite3, pathlib

db = pathlib.Path.home() / '.claude-tracker' / 'tracker.db'
if not db.exists():
    print('Database does not exist.')
    exit()

conn = sqlite3.connect(str(db))
conn.execute('DELETE FROM responses')
conn.execute('DELETE FROM prompts')
conn.execute('DELETE FROM sessions')
try:
    conn.execute('DELETE FROM sqlite_sequence')
except Exception:
    pass
conn.commit()
conn.execute('VACUUM')
conn.close()
print('Database wiped. Token tracking will resume automatically on the next prompt.')
"
```

Confirm the result to the user.
