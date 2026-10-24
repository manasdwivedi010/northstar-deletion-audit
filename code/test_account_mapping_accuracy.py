import pandas as pd
import json

sample_reqs = pd.read_csv('dataset/sample_deletion_requests.csv')
sample_out = pd.read_csv('dataset/sample_output.csv').set_index('case_id')
activity = pd.read_csv('dataset/system_activity.csv')

# All deletion worker account delete events
dw_accs = activity[(activity['source_system'] == 'deletion_worker') & (activity['target_system'] == 'account_service')].copy()
dw_accs['event_time_pd'] = pd.to_datetime(dw_accs['event_time'])

correct = 0
for idx, r in sample_reqs.iterrows():
    cid = r['case_id']
    rep_at_pd = pd.to_datetime(r['reported_at'])
    req_at_pd = pd.to_datetime(r['requested_at'])
    
    # Expected account
    steps = json.loads(sample_out.loc[cid, 'steps_json'])
    exp_acc = [s['resource_id'] for s in steps if s['system_id'] == 'account_service']
    exp_acc_id = exp_acc[0] if exp_acc else None
    
    # Find dw_accs closest to reported_at (prior to reported_at + 10 mins, after requested_at)
    candidates = dw_accs[(dw_accs['event_time_pd'] >= req_at_pd) & (dw_accs['event_time_pd'] <= rep_at_pd + pd.Timedelta(minutes=15))].copy()
    if len(candidates) > 0:
        candidates['diff'] = (rep_at_pd - candidates['event_time_pd']).abs()
        best = candidates.sort_values('diff').iloc[0]['resource_id']
    else:
        # Check closest overall
        dw_accs['diff'] = (rep_at_pd - dw_accs['event_time_pd']).abs()
        best = dw_accs.sort_values('diff').iloc[0]['resource_id']
        
    if best == exp_acc_id:
        correct += 1
    else:
        print(f"{cid}: predicted {best} vs expected {exp_acc_id} (rep_at={r['reported_at']})")

print(f"Account mapping accuracy: {correct} / {len(sample_reqs)}")
