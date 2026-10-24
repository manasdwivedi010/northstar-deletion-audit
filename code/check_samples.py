import pandas as pd
import json

sample_reqs = pd.read_csv('dataset/sample_deletion_requests.csv')
sample_out = pd.read_csv('dataset/sample_output.csv')
ev_files = pd.read_csv('dataset/evidence_files.csv').set_index('file_id')

merged = pd.merge(sample_reqs, sample_out, on='case_id')

# Let's inspect cases 1 to 10
for idx in range(10):
    r = merged.iloc[idx]
    steps = json.loads(r['steps_json'])
    print(f"=== {r['case_id']} ({r['email']}) status={r['deletion_status']} ===")
    for s in steps:
        print(f"  {s['phase']} | {s['system_id']} | {s['resource_id']} | {s['operation']} | {s['state']} | ev={s.get('evidence_id')}")
