import pandas as pd
import json

sample_reqs = pd.read_csv('dataset/sample_deletion_requests.csv')
sample_out = pd.read_csv('dataset/sample_output.csv').set_index('case_id')
df_act = pd.read_csv('dataset/system_activity.csv')
dw_acc = df_act[(df_act['source_system'] == 'deletion_worker') & (df_act['target_system'] == 'account_service')].copy()

for idx, r in sample_reqs.iterrows():
    cid = r['case_id']
    steps = json.loads(sample_out.loc[cid, 'steps_json'])
    accs = [s['resource_id'] for s in steps if s['system_id'] == 'account_service']
    acc = accs[0] if accs else None
    
    match = dw_acc[dw_acc['resource_id'] == acc]
    if len(match) > 0:
        row = match.iloc[0]
        print(f"{cid}: rep_at={r['reported_at']}, rep_st={r['reported_status']} -> dw_time={row['event_time']}, dw_res={row['reported_result']}, acc={acc}")
    else:
        print(f"{cid}: acc={acc} NOT IN dw_acc!")
