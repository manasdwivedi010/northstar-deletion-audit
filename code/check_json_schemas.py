import glob
import json
import os

for jf in glob.glob('dataset/evidence/records/*.json'):
    fname = os.path.basename(jf)
    with open(jf, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, dict):
        print(f"{fname}: dict keys={list(data.keys())[:5]}")
    elif isinstance(data, list):
        print(f"{fname}: list len={len(data)}")
