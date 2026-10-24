import pandas as pd
import json

sample_reqs = pd.read_csv('dataset/sample_deletion_requests.csv')
sample_out = pd.read_csv('dataset/sample_output.csv').set_index('case_id')

for idx, r in sample_reqs.iterrows():
    cid = r['case_id']
    st = sample_out.loc[cid, 'deletion_status']
    steps = json.loads(sample_out.loc[cid, 'steps_json'])
    print(f"\n{cid} ({st}):")
    for s in steps:
        print(f"  [{s['phase']}] {s['operation']} | {s['system_id']} | {s['resource_id']} | {s['state']} | {s.get('evidence_id')}")
