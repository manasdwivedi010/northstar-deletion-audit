import pandas as pd

ev_files = pd.read_csv('dataset/evidence_files.csv').set_index('file_id')
sample_out = pd.read_csv('dataset/sample_output.csv')
sample_reqs = pd.read_csv('dataset/sample_deletion_requests.csv').set_index('case_id')

all_evs = set()
for idx, r in sample_out.iterrows():
    import json
    steps = json.loads(r['steps_json'])
    for s in steps:
        if s.get('evidence_id'):
            all_evs.add(s['evidence_id'])

for ev in sorted(all_evs):
    row = ev_files.loc[ev]
    print(f"{ev}: captured_at={row['captured_at']} | origin={row['origin']} | path={row['file_path']}")
