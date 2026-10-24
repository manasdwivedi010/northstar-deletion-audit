import pandas as pd
import json

df_act = pd.read_csv('dataset/system_activity.csv')
dw = df_act[df_act['source_system'] == 'deletion_worker'].copy()
dw['time_pd'] = pd.to_datetime(dw['event_time'])

# Partition into batches by time gap > 1 hour
batches = []
curr_batch = []
last_t = None
for idx, r in dw.iterrows():
    t = r['time_pd']
    if last_t is None or (t - last_t).total_seconds() > 3600:
        if curr_batch:
            batches.append(curr_batch)
        curr_batch = [r]
    else:
        curr_batch.append(r)
    last_t = t
if curr_batch:
    batches.append(curr_batch)

print(f"Total batches: {len(batches)}")

# In each batch, see how accounts and non-accounts are arranged
for b_idx, b in enumerate(batches):
    accs = [r for r in b if r['target_system'] == 'account_service']
    non_accs = [r for r in b if r['target_system'] != 'account_service']
    if len(accs) > 1 and len(non_accs) > 0:
        t_start = b[0]['event_time']
        print(f"\nBatch {b_idx} at {t_start}: {len(accs)} accounts, {len(non_accs)} non-accounts")
        print("  Accounts:", [r['resource_id'] for r in accs])
        print("  Non-accounts:", [(r['target_system'], r['resource_id']) for r in non_accs])
        if b_idx > 20: # just sample a few
            break
