import pandas as pd
import json

sample_reqs = pd.read_csv('dataset/sample_deletion_requests.csv').set_index('case_id')
sample_out = pd.read_csv('dataset/sample_output.csv').set_index('case_id')
manifest = pd.read_csv('dataset/evidence_files.csv').set_index('file_id')

for cid in sample_reqs.index:
    audit_at = pd.to_datetime(sample_reqs.loc[cid, 'audit_at'])
    steps = json.loads(sample_out.loc[cid, 'steps_json'])
    ev_ids = set(s['evidence_id'] for s in steps if s.get('evidence_id'))
    for eid in ev_ids:
        cap_at = pd.to_datetime(manifest.loc[eid, 'captured_at'])
        diff_hours = (cap_at - audit_at).total_seconds() / 3600
        print(f"{cid} -> {eid}: audit_at={audit_at}, cap_at={cap_at}, diff_hours={diff_hours:+.1f}")
