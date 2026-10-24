import pandas as pd

df = pd.read_csv('dataset/system_activity.csv')
dw = df[df['source_system'] == 'deletion_worker']

print(f"Total deletion worker events: {len(dw)}")
# Look at consecutive events
prev_account = None
account_to_resources = {}

for idx, r in dw.iterrows():
    target = r['target_system']
    res = r['resource_id']
    op = r['event_type']
    if target == 'account_service' and op == 'DELETE_RECORD':
        prev_account = res
        if prev_account not in account_to_resources:
            account_to_resources[prev_account] = []
    elif prev_account is not None:
        account_to_resources[prev_account].append((target, res, op))

print(f"Mapped accounts: {len(account_to_resources)}")
# Sample mapped accounts
for acc in list(account_to_resources.keys())[:10]:
    print(f"{acc} -> {account_to_resources[acc]}")
