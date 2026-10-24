import pandas as pd
import json

sample_out = pd.read_csv('dataset/sample_output.csv')
sample_reqs = pd.read_csv('dataset/sample_deletion_requests.csv').set_index('case_id')
for idx, r in sample_out.iterrows():
    cid = r['case_id']
    req = sample_reqs.loc[cid]
    steps = json.loads(r['steps_json'])
    evs = set(s.get('evidence_id') for s in steps if s.get('evidence_id'))
    ops = [f"{s['phase']}:{s['operation']}:{s['system_id']}" for s in steps]
    print(f"{cid} | {r['deletion_status']} | audit_at={req['audit_at']} | evs={evs}")
