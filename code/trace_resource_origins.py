import pandas as pd
import json
import os

sample_out = pd.read_csv('dataset/sample_output.csv')
sample_reqs = pd.read_csv('dataset/sample_deletion_requests.csv').set_index('case_id')
ev_files = pd.read_csv('dataset/evidence_files.csv').set_index('file_id')

all_steps = []
for idx, r in sample_out.iterrows():
    cid = r['case_id']
    steps = json.loads(r['steps_json'])
    for s in steps:
        all_steps.append((cid, s['system_id'], s['resource_id'], s['phase'], s['operation'], s.get('evidence_id')))

df_steps = pd.DataFrame(all_steps, columns=['case_id', 'system_id', 'resource_id', 'phase', 'operation', 'evidence_id']).drop_duplicates(subset=['case_id', 'system_id', 'resource_id'])

print(f"Total unique (case, system, resource) pairs: {len(df_steps)}")

# For each pair, check where it exists in evidence files or system_activity
activity = pd.read_csv('dataset/system_activity.csv')

found_in_cited_ev = 0
found_in_activity = 0
for idx, r in df_steps.iterrows():
    res = r['resource_id']
    ev_id = r['evidence_id']
    # Check cited evidence
    in_ev = False
    if ev_id and ev_id in ev_files.index:
        p = os.path.join('dataset', ev_files.loc[ev_id, 'file_path'])
        if os.path.exists(p):
            try:
                with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                    if res in fp.read():
                        in_ev = True
            except Exception:
                pass
    in_act = (len(activity[activity['resource_id'] == res]) > 0)
    if in_ev:
        found_in_cited_ev += 1
    if in_act:
        found_in_activity += 1
    if not in_ev and not in_act:
        print(f"Not in cited ev or act: case={r['case_id']} sys={r['system_id']} res={res} ev={ev_id}")

print(f"Found in cited ev: {found_in_cited_ev} / {len(df_steps)}")
print(f"Found in activity: {found_in_activity} / {len(df_steps)}")
