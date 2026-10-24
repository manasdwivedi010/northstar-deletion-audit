import os
import pandas as pd

ev_files = pd.read_csv('dataset/evidence_files.csv')

for target in ['audit_record_2016', 'audit_record_4902', 'account_001', 'account_7566']:
    found = []
    for idx, r in ev_files.iterrows():
        fpath = os.path.join('dataset', r['file_path'])
        if os.path.exists(fpath):
            try:
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as fp:
                    if target in fp.read():
                        found.append(r['file_id'])
            except Exception:
                pass
    print(f"{target} found in: {found}")
