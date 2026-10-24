import os
import pandas as pd

targets = [
    'audit_record_4902', 'audit_record_9394', 'audit_record_2945', 
    'audit_record_4816', 'audit_record_987', 'audit_record_1596',
    'audit_record_9528', 'audit_record_1797', 'audit_record_6645',
    'audit_record_6793', 'audit_record_5569', 'audit_record_3482',
    'audit_record_4128', 'audit_record_7095', 'audit_record_3954',
    'audit_record_1707', 'audit_record_7068'
]

manifest = pd.read_csv('dataset/evidence_files.csv')

for t in targets:
    found = []
    for idx, r in manifest.iterrows():
        p = os.path.join('dataset', r['file_path'])
        if os.path.exists(p):
            try:
                with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                    if t in fp.read():
                        found.append(r['file_id'])
            except Exception:
                pass
    print(f"{t}: {found}")
