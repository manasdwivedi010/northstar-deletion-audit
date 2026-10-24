import os
import pandas as pd

manifest = pd.read_csv('dataset/evidence_files.csv')
print(f"Total evidence files: {len(manifest)}")
type_counts = {}
for idx, r in manifest.iterrows():
    ext = os.path.splitext(r['file_path'])[1].lower()
    type_counts[ext] = type_counts.get(ext, 0) + 1
print("File types:", type_counts)
