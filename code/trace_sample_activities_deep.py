import pandas as pd
import json

df_act = pd.read_csv('dataset/system_activity.csv')
sample_out = pd.read_csv('dataset/sample_output.csv').set_index('case_id')
sample_reqs = pd.read_csv('dataset/sample_deletion_requests.csv')

# Let's see the cases where we know all expected resources
for idx, r in sample_reqs.iterrows():
    cid = r['case_id']
    steps = json.loads(sample_out.loc[cid, 'steps_json'])
    res_set = set(s['resource_id'] for s in steps)
    
    # Find all activities containing any of these resources
    acts = df_act[df_act['resource_id'].isin(res_set)]
    print(f"\n--- {cid} (rep_at={r['reported_at']}) ---")
    print(f"Resources: {res_set}")
    for a_idx, a_row in acts.iterrows():
        print(f"  {a_row['event_time']} | {a_row['source_system']} -> {a_row['target_system']} | {a_row['event_type']} | {a_row['resource_id']} | {a_row['reported_result']}")
