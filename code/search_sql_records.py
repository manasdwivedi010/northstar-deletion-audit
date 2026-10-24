import os
import json
import sqlite3
import pandas as pd

manifest = pd.read_csv('dataset/evidence_files.csv')

def search_sql(path, target):
    try:
        conn = sqlite3.connect(':memory:')
        with open(path, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in c.fetchall()]
        for t in tables:
            try:
                c.execute(f"SELECT * FROM {t}")
                for row in c.fetchall():
                    if any(target in str(val) for val in row):
                        return True
            except Exception:
                pass
        conn.close()
    except Exception:
        pass
    return False

for t in ['audit_record_6645', 'audit_record_5569']:
    print(f"Searching {t}...")
    for idx, r in manifest.iterrows():
        p = os.path.join('dataset', r['file_path'])
        if p.endswith('.sql'):
            if search_sql(p, t):
                print(f"  found {t} in {r['file_id']} ({p})")
