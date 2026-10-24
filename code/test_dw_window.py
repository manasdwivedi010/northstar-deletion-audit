import pandas as pd
import json

sample_reqs = pd.read_csv('dataset/sample_deletion_requests.csv')
sample_out = pd.read_csv('dataset/sample_output.csv').set_index('case_id')
activity = pd.read_csv('dataset/system_activity.csv')

for idx, r in sample_reqs.iterrows():
    cid = r['case_id']
    req_at = r['requested_at']
    rep_at = r['reported_at']
    
    # Deletion worker events during request window
    dw_acts = activity[(activity['source_system'] == 'deletion_worker') & 
                       (activity['event_time'] >= req_at) & 
                       (activity['event_time'] <= rep_at)]
    
    expected_steps = json.loads(sample_out.loc[cid, 'steps_json'])
    exp_res = [(s['system_id'], s['resource_id'], s['operation']) for s in expected_steps]
    
    act_res = [(a['target_system'], a['resource_id'], a['event_type']) for _, a in dw_acts.iterrows()]
    
    print(f"\n{cid} ({req_at} -> {rep_at}):")
    print(f"  Expected resources ({len(exp_res)}): {exp_res}")
    print(f"  Activity resources ({len(act_res)}): {act_res}")
