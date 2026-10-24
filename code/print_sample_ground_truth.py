import pandas as pd
import json

sample_reqs = pd.read_csv('dataset/sample_deletion_requests.csv').set_index('case_id')
sample_out = pd.read_csv('dataset/sample_output.csv').set_index('case_id')

for cid in sample_reqs.index:
    st = sample_out.loc[cid, 'deletion_status']
    steps = json.loads(sample_out.loc[cid, 'steps_json'])
    step_summary = []
    for s in steps:
        step_summary.append(f"{s['phase']}:{s['operation']}:{s['system_id']}:{s['resource_id']}:{s.get('evidence_id','')}")
    print(f"\n{cid} | {st} | req_email={sample_reqs.loc[cid, 'email']} | audit_at={sample_reqs.loc[cid, 'audit_at']}")
    for ss in step_summary:
        print(f"   {ss}")
