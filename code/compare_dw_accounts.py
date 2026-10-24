import pandas as pd
import json

sample_reqs = pd.read_csv('dataset/sample_deletion_requests.csv')
sample_out = pd.read_csv('dataset/sample_output.csv').set_index('case_id')
activity = pd.read_csv('dataset/system_activity.csv')

dw_accs = activity[(activity['source_system'] == 'deletion_worker') & (activity['target_system'] == 'account_service')].copy()

for idx, r in sample_reqs.iterrows():
    cid = r['case_id']
    steps = json.loads(sample_out.loc[cid, 'steps_json'])
    acc_steps = [s['resource_id'] for s in steps if s['system_id'] == 'account_service']
    exp_acc = acc_steps[0] if acc_steps else 'NONE'
    
    # check if exp_acc is in dw_accs
    row = dw_accs[dw_accs['resource_id'] == exp_acc]
    if len(row) > 0:
        ev_time = row.iloc[0]['event_time']
        act_id = row.iloc[0]['activity_id']
        print(f"{cid} | req={r['requested_at']} | rep={r['reported_at']} | exp={exp_acc} | act={act_id} ({ev_time})")
    else:
        print(f"{cid} | req={r['requested_at']} | rep={r['reported_at']} | exp={exp_acc} | NOT IN DW")
