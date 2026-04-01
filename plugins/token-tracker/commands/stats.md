---
description: Show a global token usage dashboard with totals, model breakdown, and activity patterns
allowed-tools: Bash(*)
---

Run this command to display a full usage dashboard from the tracker database:

```bash
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null || echo python3)
"$PYTHON" -c "
import sqlite3, pathlib

db = pathlib.Path.home() / '.claude-tracker' / 'tracker.db'
if not db.exists():
    print('No tracker database found. Submit a prompt first to start tracking.')
    exit()

conn = sqlite3.connect(str(db))
conn.row_factory = sqlite3.Row

# Overall totals
totals = conn.execute('''
    SELECT
        (SELECT COUNT(*) FROM prompts)                          AS total_prompts,
        (SELECT COUNT(*) FROM responses)                        AS total_responses,
        (SELECT COUNT(*) FROM sessions)                         AS total_sessions,
        COALESCE((SELECT SUM(input_tokens)  FROM responses), 0) AS total_input,
        COALESCE((SELECT SUM(output_tokens) FROM responses), 0) AS total_output,
        COALESCE((SELECT SUM(cache_read_tokens) FROM responses), 0) AS total_cache_read,
        COALESCE((SELECT SUM(total_tokens)  FROM responses), 0) AS total_tokens,
        COALESCE((SELECT SUM(cost_usd)      FROM responses), 0) AS total_cost,
        (SELECT MIN(timestamp) FROM prompts)                    AS first_seen,
        (SELECT MAX(timestamp) FROM prompts)                    AS last_seen
''').fetchone()

print('╔══════════════════════════════════════════════════════╗')
print('║          CLAUDE CODE TOKEN TRACKER - STATS           ║')
print('╚══════════════════════════════════════════════════════╝')
print()
print('=== TOTALS ===')
print(f'  Prompts logged   : {totals[\"total_prompts\"]:,}')
print(f'  Responses logged : {totals[\"total_responses\"]:,}')
print(f'  Sessions         : {totals[\"total_sessions\"]:,}')
print(f'  Input tokens     : {totals[\"total_input\"]:,}')
print(f'  Output tokens    : {totals[\"total_output\"]:,}')
print(f'  Cache read tokens: {totals[\"total_cache_read\"]:,}')
print(f'  Total tokens     : {totals[\"total_tokens\"]:,}')
print(f'  Total cost (est) : \${totals[\"total_cost\"]:.4f}')
if totals['total_responses']:
    avg_cost = totals['total_cost'] / totals['total_responses']
    avg_tok  = totals['total_tokens'] / totals['total_responses']
    print(f'  Avg cost/response: \${avg_cost:.6f}')
    print(f'  Avg tokens/resp  : {avg_tok:.0f}')
if totals['first_seen']:
    print(f'  First recorded   : {totals[\"first_seen\"][:19]}')
    print(f'  Last recorded    : {totals[\"last_seen\"][:19]}')

# Model breakdown
rows = conn.execute('SELECT * FROM model_usage').fetchall()
if rows:
    print()
    print('=== MODEL BREAKDOWN ===')
    for row in rows:
        print(f'  {row[\"model\"]}')
        print(f'    responses={row[\"response_count\"]:,}  in={row[\"total_input_tokens\"]:,}  out={row[\"total_output_tokens\"]:,}  cost=\${row[\"total_cost_usd\"]:.4f}')

# Most active days
rows = conn.execute('SELECT * FROM daily_stats LIMIT 5').fetchall()
if rows:
    print()
    print('=== MOST ACTIVE DAYS ===')
    for row in rows:
        print(f'  {row[\"day\"]}  {row[\"prompt_count\"]:>3} responses  {row[\"total_tokens\"]:>9,} tokens  \${row[\"total_cost_usd\"]:.4f}')

# Hourly heatmap (top 5)
rows = conn.execute('SELECT * FROM hourly_distribution ORDER BY prompt_count DESC LIMIT 5').fetchall()
if rows:
    print()
    print('=== PEAK HOURS ===')
    for row in rows:
        bar = '█' * min(row['prompt_count'], 30)
        print(f'  {row[\"hour\"]:02d}:00  {bar}  ({row[\"prompt_count\"]} responses)')

conn.close()
"
```

Present the output as a formatted dashboard. Real token counts come from the Claude API transcript files, not estimates.
