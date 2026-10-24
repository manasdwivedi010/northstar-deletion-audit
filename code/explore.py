import pandas as pd
import json

samples_df = pd.read_csv('dataset/sample_deletion_requests.csv')
output_df = pd.read_csv('dataset/sample_output.csv')

merged = pd.merge(samples_df, output_df, on='case_id')
for idx, row in merged.iterrows():
    steps = json.loads(row['steps_json'])
    print(f"{row['case_id']}: status={row['deletion_status']} (reported={row['reported_status']}) email={row['email']} ({len(steps)} steps)")
    for s in steps:
        print(f"   step {s['step_no']}: {s['phase']} | {s['system_id']} | {s['resource_id']} | {s['operation']} | {s['state']} | ev={s.get('evidence_id')}")
