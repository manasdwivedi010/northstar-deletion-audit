import os
import re
import pandas as pd

manifest = pd.read_csv('dataset/evidence_files.csv')
found_ev = {}
for idx, r in manifest.iterrows():
    p = os.path.join('dataset', r['file_path'])
    try:
        with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
            c = fp.read()
            matches = re.findall(r'audit_record_\d+', c)
            if matches:
                found_ev[r['file_id']] = (r['origin'], r['captured_at'], len(matches), set(matches[:5]))
    except Exception:
        pass

for fid, info in sorted(found_ev.items()):
    print(f"{fid}: {info[0]} | {info[1]} | total={info[2]} | sample={info[3]}")
