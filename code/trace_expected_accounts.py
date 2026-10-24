import pandas as pd
import json

sample_out = pd.read_csv('dataset/sample_output.csv')
activity = pd.read_csv('dataset/system_activity.csv').set_index('resource_id')

for idx, r in sample_out.iterrows():
    cid = r['case_id']
    steps = json.loads(r['steps_json'])
    acc_steps = [s['resource_id'] for s in steps if s['system_id'] == 'account_service']
    if acc_steps:
        acc_id = acc_steps[0]
        if acc_id in activity.index:
            row = activity.loc[acc_id]
            if isinstance(row, pd.DataFrame):
                row = row.iloc[0]
            print(f"{cid}: {acc_id} -> {row['activity_id']} | {row['event_time']} | {row['event_type']} | {row['details']}")
        else:
            print(f"{cid}: {acc_id} -> NOT IN ACTIVITY")
