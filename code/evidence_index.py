import pandas as pd
import json
import sqlite3
import pypdf
import os

ev_manifest = pd.read_csv('dataset/evidence_files.csv')
print(f"Total evidence files in manifest: {len(ev_manifest)}")

file_types = {}
for idx, r in ev_manifest.iterrows():
    fid = r['file_id']
    fpath = os.path.join('dataset', r['file_path'])
    origin = r['origin']
    ext = os.path.splitext(fpath)[1].lower()
    file_types[fid] = {
        'path': fpath,
        'origin': origin,
        'captured_at': r['captured_at'],
        'ext': ext
    }

print("File extension breakdown:")
exts = pd.Series([v['ext'] for v in file_types.values()]).value_counts()
print(exts)
