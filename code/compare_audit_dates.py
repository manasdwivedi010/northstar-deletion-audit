import pandas as pd
import json

sample_out = pd.read_csv('dataset/sample_output.csv')
sample_reqs = pd.read_csv('dataset/sample_deletion_requests.csv').set_index('case_id')
ev_files = pd.read_csv('dataset/evidence_files.csv').set_index('file_id')

for idx, r in sample_out.iterrows():
    cid = r['case_id']
    req = sample_reqs.loc[cid]
    steps = json.loads(r['steps_json'])
    evs = set(s.get('evidence_id') for s in steps if s.get('evidence_id'))
    print(f"{cid} | audit_at={req['audit_at']} | reported_at={req['reported_at']}")
    for ev in evs:
        row = ev_files.loc[ev]
        print(f"   cited: {ev} | captured_at={row['captured_at']} | path={row['file_path']}")
