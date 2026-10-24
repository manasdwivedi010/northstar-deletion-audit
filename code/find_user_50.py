import os
import pandas as pd

manifest = pd.read_csv('dataset/evidence_files.csv')
for idx, r in manifest.iterrows():
    p = os.path.join('dataset', r['file_path'])
    try:
        with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
            c = fp.read()
            if 'user_50' in c or 'mori.ren@gmail.com' in c:
                print(f"user_50 found in {r['file_id']} ({r['file_path']})")
    except Exception:
        pass
