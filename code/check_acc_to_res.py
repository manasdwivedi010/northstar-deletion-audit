import pandas as pd
import json

df_act = pd.read_csv('dataset/system_activity.csv')
sample_out = pd.read_csv('dataset/sample_output.csv').set_index('case_id')

# Look at all 32 sample cases and what account and resources each has
account_to_resources = {}
for cid in sample_out.index:
    steps = json.loads(sample_out.loc[cid, 'steps_json'])
    accs = [s['resource_id'] for s in steps if s['system_id'] == 'account_service']
    if accs:
        acc = accs[0]
        other_res = [s['resource_id'] for s in steps if s['system_id'] != 'account_service']
        account_to_resources[acc] = other_res

print("Known sample account to other resources:")
for acc, res_list in sorted(account_to_resources.items()):
    print(f"  {acc}: {res_list}")
