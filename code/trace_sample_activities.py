import pandas as pd
import json

sample_reqs = pd.read_csv('dataset/sample_deletion_requests.csv')
sample_out = pd.read_csv('dataset/sample_output.csv').set_index('case_id')
users = pd.read_csv('dataset/user_identities.csv').set_index('user_id')
audit = pd.read_csv('dataset/user_audit_log.csv')
activity = pd.read_csv('dataset/system_activity.csv')

# Build identity maps
email_to_uid = {}
uid_to_all_emails = {}
uid_to_all_names = {}
uid_to_all_phones = {}

for uid, r in users.iterrows():
    em = r['email'].strip().lower()
    email_to_uid[em] = uid
    uid_to_all_emails[uid] = {em}
    uid_to_all_names[uid] = {r['name'].strip().lower()}
    uid_to_all_phones[uid] = {r['phone'].strip()}

for idx, r in audit.iterrows():
    uid = r['user_id']
    fld = r['field_name']
    for v in [r['old_value'], r['new_value']]:
        if pd.notna(v) and v:
            v_s = str(v).strip()
            if fld == 'email':
                email_to_uid[v_s.lower()] = uid
                uid_to_all_emails[uid].add(v_s.lower())
            elif fld == 'name':
                uid_to_all_names[uid].add(v_s.lower())
            elif fld == 'phone':
                uid_to_all_phones[uid].add(v_s)

# For each sample case, find all activities related to this user/email
for idx, r in sample_reqs.iterrows():
    cid = r['case_id']
    req_email = r['email'].strip().lower()
    uid = email_to_uid.get(req_email)
    out_row = sample_out.loc[cid]
    expected_steps = json.loads(out_row['steps_json'])
    expected_resources = [(s['system_id'], s['resource_id'], s['operation'], s['phase'], s.get('evidence_id')) for s in expected_steps]
    
    # User's known activity events
    # Match by email or user_id in details or resource_id
    matched_activities = []
    for a_idx, act in activity.iterrows():
        det = str(act['details'])
        res = str(act['resource_id'])
        if (uid and uid in det) or (req_email in det.lower()):
            matched_activities.append((act['activity_id'], act['event_time'], act['event_type'], act['target_system'], res))
            
    print(f"\n=== {cid} ({uid}) expected={out_row['deletion_status']} ===")
    print("  Expected steps in sample_output:")
    for er in expected_resources:
        print(f"    {er[3]}: {er[2]} | {er[0]}:{er[1]} | ev={er[4]}")
    print(f"  Matched system_activity ({len(matched_activities)}):")
    for ma in matched_activities:
        print(f"    {ma[0]} | {ma[1]} | {ma[2]} | {ma[3]} | {ma[4]}")
