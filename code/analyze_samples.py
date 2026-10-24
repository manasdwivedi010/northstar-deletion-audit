import pandas as pd
import json

sample_reqs = pd.read_csv('dataset/sample_deletion_requests.csv')
sample_out = pd.read_csv('dataset/sample_output.csv')
merged = pd.merge(sample_reqs, sample_out, on='case_id')

for idx in range(10):
    r = merged.iloc[idx]
    steps = json.loads(r['steps_json'])
    ev_ids = set(s.get('evidence_id') for s in steps if s.get('evidence_id'))
    print(f"{r['case_id']} | email={r['email']} | status={r['deletion_status']} | audit_at={r['audit_at']} | ev={ev_ids}")
    for s in steps:
        print(f"   {s['phase']} | {s['system_id']} | {s['resource_id']} | {s['operation']} | {s['state']} | {s.get('evidence_id')}")
