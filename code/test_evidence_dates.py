import pandas as pd
import json

sample_reqs = pd.read_csv('dataset/sample_deletion_requests.csv')
sample_out = pd.read_csv('dataset/sample_output.csv')
ev_files = pd.read_csv('dataset/evidence_files.csv').set_index('file_id')

merged = pd.merge(sample_reqs, sample_out, on='case_id')

for idx, r in merged.iterrows():
    steps = json.loads(r['steps_json'])
    ev_cites = set(s['evidence_id'] for s in steps if s.get('evidence_id'))
    audit_at = r['audit_at']
    for ev in ev_cites:
        cap_at = ev_files.loc[ev, 'captured_at']
        origin = ev_files.loc[ev, 'origin']
        fpath = ev_files.loc[ev, 'file_path']
        print(f"{r['case_id']}: audit_at={audit_at} | cited={ev} cap_at={cap_at} | origin={origin}")
