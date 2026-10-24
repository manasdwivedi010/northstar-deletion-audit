import pandas as pd
import json

sample_reqs = pd.read_csv('dataset/sample_deletion_requests.csv')
sample_out = pd.read_csv('dataset/sample_output.csv')
merged = pd.merge(sample_reqs, sample_out, on='case_id')

all_res = []
for idx, r in merged.iterrows():
    steps = json.loads(r['steps_json'])
    for s in steps:
        all_res.append({
            'case_id': r['case_id'],
            'email': r['email'],
            'phase': s['phase'],
            'system_id': s['system_id'],
            'resource_id': s['resource_id'],
            'operation': s['operation'],
            'evidence_id': s.get('evidence_id')
        })

res_df = pd.DataFrame(all_res)
print(f"Total steps across 32 samples: {len(res_df)}")
print("Systems involved:")
print(res_df['system_id'].value_counts())
print("\nUnique resources per case count:")
for cid, g in res_df.groupby('case_id'):
    resources = g[['system_id', 'resource_id', 'operation', 'evidence_id']].drop_duplicates().to_dict(orient='records')
    print(f"{cid}: {len(resources)} unique resource/operations -> {resources}")
