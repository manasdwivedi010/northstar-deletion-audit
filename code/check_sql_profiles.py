import sqlite3
import pandas as pd

manifest = pd.read_csv('dataset/evidence_files.csv')
total_profiles = 0
for idx, r in manifest.iterrows():
    if r['file_path'].endswith('.sql'):
        try:
            conn = sqlite3.connect(':memory:')
            with open('dataset/' + r['file_path'], 'r', encoding='utf-8') as f:
                conn.executescript(f.read())
            c = conn.cursor()
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='customer_profiles'")
            if c.fetchone():
                c.execute("SELECT count(resource_id) FROM customer_profiles")
                cnt = c.fetchone()[0]
                total_profiles += cnt
                print(f"{r['file_id']}: {cnt} profiles")
            conn.close()
        except Exception as e:
            print(f"Error {r['file_id']}: {e}")
print(f"Total profiles in SQL customer_profiles: {total_profiles}")
