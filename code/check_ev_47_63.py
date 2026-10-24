import sqlite3

for f in ['evidence_47', 'evidence_63']:
    path = 'dataset/evidence/databases/' + ('customer_data_reporting_replica_20260208.sql' if f == 'evidence_47' else 'customer_data_inventory_20260213.sql')
    conn = sqlite3.connect(':memory:')
    with open(path, 'r', encoding='utf-8') as fp:
        conn.executescript(fp.read())
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in c.fetchall()]
    print(f"=== {f} ===")
    for t in tables:
        c.execute(f"PRAGMA table_info({t})")
        cols = [col[1] for col in c.fetchall()]
        c.execute(f"SELECT * FROM {t}")
        for row in c.fetchall():
            if 'user_50' in str(row) or 'mori.ren' in str(row):
                print(f"  {t}: {dict(zip(cols, row))}")
