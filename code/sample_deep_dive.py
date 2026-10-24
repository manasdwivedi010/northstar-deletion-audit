import pandas as pd
import json

sample_reqs = pd.read_csv('dataset/sample_deletion_requests.csv')
sample_out = pd.read_csv('dataset/sample_output.csv')
users = pd.read_csv('dataset/user_identities.csv')
audit = pd.read_csv('dataset/user_audit_log.csv')
ev_files = pd.read_csv('dataset/evidence_files.csv').set_index('file_id')

merged = pd.merge(sample_reqs, sample_out, on='case_id')

for idx, r in merged.iterrows():
    email = r['email']
    u = users[users['email'].str.lower() == email.lower()]
    if len(u) == 0:
        a = audit[audit['old_value'].str.lower() == email.lower()]
        uid = a.iloc[0]['user_id']
    else:
        uid = u.iloc[0]['user_id']
    
    steps = json.loads(r['steps_json'])
    ev_cites = set(s['evidence_id'] for s in steps if s.get('evidence_id'))
    print(f"\n==================================================")
    print(f"{r['case_id']}: {uid} | {email} | status={r['deletion_status']} (rep={r['reported_status']})")
    print(f"req={r['requested_at']} | rep_at={r['reported_at']} | audit_at={r['audit_at']}")
    print(f"evidence cited: {ev_cites}")
    for ev in ev_cites:
        ev_info = ev_files.loc[ev]
        print(f"  -> {ev}: {ev_info['captured_at']} | {ev_info['origin']} | {ev_info['file_path']}")
    for s in steps:
        print(f"  step {s['step_no']}: {s['phase']} | {s['system_id']} | {s['resource_id']} | {s['operation']} | {s['state']} | {s.get('evidence_id')}")
