import glob
import sqlite3
import os

for sf in glob.glob('dataset/evidence/databases/*.sql'):
    fname = os.path.basename(sf)
    conn = sqlite3.connect(':memory:')
    with open(sf, 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in c.fetchall() if r[0] != 'snapshot_scope']
    cols_by_table = {}
    for t in tables:
        c.execute(f"PRAGMA table_info({t})")
        cols_by_table[t] = [r[1] for r in c.fetchall()]
    print(f"{fname}: {cols_by_table}")
    conn.close()
