import sqlite3, glob, json

keys = set()
for f in glob.glob('dataset/evidence/databases/*.sql'):
    conn = sqlite3.connect(':memory:')
    with open(f, 'r', encoding='utf-8') as fp:
        conn.executescript(fp.read())
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in c.fetchall()]
    for t in tables:
        try:
            c.execute(f"SELECT record_json FROM {t}")
            for r in c.fetchall():
                try:
                    d = json.loads(r[0])
                    keys.update(d.keys())
                except:
                    pass
        except:
            pass
print('Record JSON keys found:', keys)
