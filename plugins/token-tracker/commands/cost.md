---
description: Show daily, weekly, and monthly cost reports with token breakdown
allowed-tools: Bash(python3:*)
---

Run this command to display a cost report from the tracker database:

```bash
python3 -c "
import sqlite3, pathlib

db = pathlib.Path.home() / '.claude-tracker' / 'tracker.db'
if not db.exists():
    print('No tracker database found.')
    exit()

conn = sqlite3.connect(str(db))
conn.row_factory = sqlite3.Row

# Daily costs (last 30 days)
rows = conn.execute('''
    SELECT day, prompt_count, total_input_tokens, total_output_tokens,
           total_cache_read_tokens, total_tokens, total_cost_usd
    FROM daily_stats
    WHERE day >= date(\"now\", \"-30 days\")
    ORDER BY day DESC
''').fetchall()

print('=== DAILY COSTS (LAST 30 DAYS) ===')
if not rows:
    print('  No data yet.')
else:
    max_cost = max(r['total_cost_usd'] for r in rows) or 1
    for row in rows:
        bar_len = int((row['total_cost_usd'] / max_cost) * 25)
        bar = '█' * bar_len
        print(f'  {row[\"day\"]}  \${row[\"total_cost_usd\"]:7.4f}  {bar:<25}  ({row[\"prompt_count\"]} responses, {row[\"total_tokens\"]:,} tok)')

# Weekly totals
print()
print('=== WEEKLY TOTALS (LAST 12 WEEKS) ===')
rows = conn.execute('''
    SELECT
        strftime(\"%Y-W%W\", timestamp)      AS week,
        COUNT(*)                             AS responses,
        COALESCE(SUM(total_tokens), 0)       AS tokens,
        COALESCE(SUM(cost_usd), 0)           AS cost
    FROM responses
    WHERE timestamp >= datetime(\"now\", \"-12 weeks\")
    GROUP BY week
    ORDER BY week DESC
''').fetchall()
if not rows:
    print('  No data yet.')
else:
    for row in rows:
        print(f'  {row[\"week\"]}  \${row[\"cost\"]:8.4f}  {row[\"tokens\"]:>10,} tokens  {row[\"responses\"]} responses')

# Monthly totals
print()
print('=== MONTHLY TOTALS ===')
rows = conn.execute('''
    SELECT
        strftime(\"%Y-%m\", timestamp)        AS month,
        COUNT(*)                             AS responses,
        COALESCE(SUM(input_tokens), 0)       AS input_tok,
        COALESCE(SUM(output_tokens), 0)      AS output_tok,
        COALESCE(SUM(cache_read_tokens), 0)  AS cache_read,
        COALESCE(SUM(cost_usd), 0)           AS cost
    FROM responses
    GROUP BY month
    ORDER BY month DESC
    LIMIT 12
''').fetchall()
if not rows:
    print('  No data yet.')
else:
    for row in rows:
        print(f'  {row[\"month\"]}  \${row[\"cost\"]:8.4f}  in={row[\"input_tok\"]:,}  out={row[\"output_tok\"]:,}  cache_read={row[\"cache_read\"]:,}  ({row[\"responses\"]} responses)')

# Model cost comparison
rows = conn.execute('SELECT * FROM model_usage').fetchall()
if rows and len(rows) > 1:
    print()
    print('=== COST BY MODEL ===')
    for row in rows:
        print(f'  {row[\"model\"]}')
        print(f'    \${row[\"total_cost_usd\"]:.4f}  ({row[\"response_count\"]} responses)')

conn.close()
"
```

Format and present this as a clear cost report. Highlight any days or weeks with unusually high spending.
