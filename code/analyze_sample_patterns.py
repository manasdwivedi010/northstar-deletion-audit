import pandas as pd
import json

sample_out = pd.read_csv('dataset/sample_output.csv')
sample_reqs = pd.read_csv('dataset/sample_deletion_requests.csv').set_index('case_id')
users_df = pd.read_csv('dataset/user_identities.csv')
audit_df = pd.read_csv('dataset/user_audit_log.csv')
activity_df = pd.read_csv('dataset/system_activity.csv')

# Build identity map
email_to_uid = {}
for idx, r in users_df.iterrows():
    email_to_uid[r['email'].strip().lower()] = r['user_id']
for idx, r in audit_df.iterrows():
    val = r['old_value']
    if r['field_name'] == 'email' and pd.notna(val) and val:
        email_to_uid[str(val).strip().lower()] = r['user_id']

print(f"{'case_id':<8} | {'user_id':<8} | {'status':<11} | {'num_steps':<9} | {'resources in sample_output'}")
print("-" * 80)
for idx, r in sample_out.iterrows():
    cid = r['case_id']
    req = sample_reqs.loc[cid]
    uid = email_to_uid.get(req['email'].strip().lower(), 'UNKNOWN')
    steps = json.loads(r['steps_json'])
    res_list = [f"{s['system_id']}:{s['resource_id']}({s['phase'][0]}:{s['operation'][:4]})" for s in steps]
    print(f"{cid:<8} | {uid:<8} | {r['deletion_status']:<11} | {len(steps):<9} | {', '.join(res_list)}")
