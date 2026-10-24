import pandas as pd

df = pd.read_csv('dataset/evidence_files.csv').set_index('file_id')
for i in range(1, 62):
    fid = f"evidence_{i:02d}"
    if fid in df.index:
        r = df.loc[fid]
        print(f"{fid}: {r['origin']} | {r['captured_at']} | {r['file_path']}")
