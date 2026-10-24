import pandas as pd
import json

sample_reqs = pd.read_csv('dataset/sample_deletion_requests.csv')
sample_out = pd.read_csv('dataset/sample_output.csv').set_index('case_id')
users = pd.read_csv('dataset/user_identities.csv').set_index('user_id')
audit = pd.read_csv('dataset/user_audit_log.csv')
activity = pd.read_csv('dataset/system_activity.csv')

# Build identity maps
email_to_uid = {}
uid_to_emails = {}
uid_to_names = {}
uid_to_phones = {}

for uid, r in users.iterrows():
    em = r['email'].strip().lower()
    email_to_uid[em] = uid
    uid_to_emails[uid] = {em}
    uid_to_names[uid] = {r['name'].strip().lower()}
    uid_to_phones[uid] = {r['phone'].strip()}

for idx, r in audit.iterrows():
    uid = r['user_id']
    fld = r['field_name']
    for v in [r['old_value'], r['new_value']]:
        if pd.notna(v) and v:
            v_s = str(v).strip()
            if fld == 'email':
                email_to_uid[v_s.lower()] = uid
                uid_to_emails[uid].add(v_s.lower())
            elif fld == 'name':
                uid_to_names[uid].add(v_s.lower())
            elif fld == 'phone':
                uid_to_phones[uid].add(v_s)

# Map case_id to primary account_id from activity
dw_acts = activity[(activity['source_system'] == 'deletion_worker') & (activity['target_system'] == 'account_service')]

for idx, r in sample_reqs.iterrows():
    cid = r['case_id']
    req_at = r['requested_at']
    rep_at = r['reported_at']
    req_email = r['email'].strip().lower()
    uid = email_to_uid.get(req_email)
    
    # Matching account activity
    acts = dw_acts[(dw_acts['event_time'] >= req_at) & (dw_acts['event_time'] <= rep_at)]
    acc_id = acts.iloc[0]['resource_id'] if len(acts) > 0 else 'NONE'
    
    expected_steps = json.loads(sample_out.loc[cid, 'steps_json'])
    exp_acc = [s['resource_id'] for s in expected_steps if s['system_id'] == 'account_service']
    exp_acc_id = exp_acc[0] if exp_acc else 'NONE'
    
    status = "OK" if acc_id == exp_acc_id else f"MISMATCH ({acc_id} vs {exp_acc_id})"
    print(f"{cid} ({uid}): {status}")
