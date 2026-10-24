import pandas as pd
import json

sample_reqs = pd.read_csv('dataset/sample_deletion_requests.csv').set_index('case_id')
sample_out = pd.read_csv('dataset/sample_output.csv')
ev_files = pd.read_csv('dataset/evidence_files.csv').set_index('file_id')

for idx, r in sample_out.iterrows():
    cid = r['case_id']
    req = sample_reqs.loc[cid]
    audit_at = pd.to_datetime(req['audit_at'])
    steps = json.loads(r['steps_json'])
    evs = set(s.get('evidence_id') for s in steps if s.get('evidence_id'))
    print(f"{cid} (audit_at={req['audit_at']}):")
    for ev in evs:
        cap_at = pd.to_datetime(ev_files.loc[ev, 'captured_at'])
        diff = audit_at - cap_at
        print(f"  {ev}: captured_at={ev_files.loc[ev, 'captured_at']} (diff = {diff})")
