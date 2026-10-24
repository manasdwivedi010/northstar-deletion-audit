import os
import pandas as pd

manifest = pd.read_csv('dataset/evidence_files.csv')
for idx, r in manifest.iterrows():
    p = os.path.join('dataset', r['file_path'])
    try:
        with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
            c = fp.read()
            if 'analytics_1895' in c or 'analytics_4566' in c or 'support_4715' in c:
                print(f"found in {r['file_id']} ({r['file_path']})")
    except Exception:
        pass
