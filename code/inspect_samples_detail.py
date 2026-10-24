import pandas as pd
import json
import sys

start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
end = int(sys.argv[2]) if len(sys.argv) > 2 else 5

sample_out = pd.read_csv('dataset/sample_output.csv')
sample_reqs = pd.read_csv('dataset/sample_deletion_requests.csv').set_index('case_id')

for idx, r in sample_out.iloc[start:end].iterrows():
    cid = r['case_id']
    req = sample_reqs.loc[cid]
    steps = json.loads(r['steps_json'])
    print(f"=== {cid} | status={r['deletion_status']} | req_stat={req['reported_status']} | num_steps={len(steps)} ===")
    for s in steps:
        p = s['phase']
        op = s['operation']
        sys_id = s['system_id']
        res_id = s['resource_id']
        st = s['state']
        ev = s.get('evidence_id', '')
        print(f"  [{p}] {op} | sys={sys_id} | res={res_id} | st={st} | ev={ev}")
