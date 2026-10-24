import glob
import sqlite3
import os

sql_files = glob.glob('dataset/evidence/databases/*.sql')
print(f"Total SQL files: {len(sql_files)}")

for sf in sql_files:
    fname = os.path.basename(sf)
    conn = sqlite3.connect(':memory:')
    with open(sf, 'r', encoding='utf-8') as f:
        sql = f.read()
    try:
        conn.executescript(sql)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cursor.fetchall()]
        row_counts = {}
        for t in tables:
            cursor.execute(f"SELECT count(*) FROM {t}")
            row_counts[t] = cursor.fetchone()[0]
        print(f"{fname}: tables={row_counts}")
    except Exception as e:
        print(f"Error executing {fname}: {e}")
    finally:
        conn.close()
