import os
import json
import pandas as pd

manifest = pd.read_csv('dataset/evidence_files.csv')
for idx, r in manifest.iterrows():
    if r['file_path'].endswith('.json'):
        path = os.path.join('dataset', r['file_path'])
        with open(path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                keys = list(data.keys()) if isinstance(data, dict) else f"list({len(data)})"
                print(f"{r['file_id']}: origin={r['origin']} | keys={keys}")
            except Exception as e:
                print(f"{r['file_id']}: ERROR {e}")
