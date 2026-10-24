import pandas as pd
import json

sample_out = pd.read_csv('dataset/sample_output.csv')
sample_reqs = pd.read_csv('dataset/sample_deletion_requests.csv').set_index('case_id')
activity = pd.read_csv('dataset/system_activity.csv')

for idx, r in sample_out.iloc[:10].iterrows():
    cid = r['case_id']
    steps = json.loads(r['steps_json'])
    audit_records = [s['resource_id'] for s in steps if s['system_id'] == 'security_service']
    account_records = [s['resource_id'] for s in steps if s['system_id'] == 'account_service']
    print(f"{cid}: account={account_records} security={audit_records}")
    # Search for audit_record in system_activity
    for ar in audit_records:
        m = activity[activity['resource_id'] == ar]
        if len(m) > 0:
            print(f"  found {ar} in activity: {m['activity_id'].values}")
        else:
            # check in details
            m_det = activity[activity['details'].str.contains(ar, na=False)]
            if len(m_det) > 0:
                print(f"  found {ar} in activity details: {m_det['activity_id'].values}")
