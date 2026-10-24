"""
Evaluate parsed evidence against sample_output.csv
"""
import sys
sys.path.insert(0, 'code')
import evidence_parser
import pandas as pd
import json

sample_reqs = pd.read_csv('dataset/sample_deletion_requests.csv')
sample_out = pd.read_csv('dataset/sample_output.csv')
users_df = pd.read_csv('dataset/user_identities.csv')
audit_df = pd.read_csv('dataset/user_audit_log.csv')
activity_df = pd.read_csv('dataset/system_activity.csv')
ev_manifest = pd.read_csv('dataset/evidence_files.csv').set_index('file_id')

# Identity resolution
user_to_all_emails = {}
user_to_all_phones = {}
user_to_all_names = {}
email_to_uid = {}

for idx, r in users_df.iterrows():
    uid = r['user_id']
    user_to_all_emails[uid] = {r['email'].strip().lower()}
    user_to_all_phones[uid] = {r['phone'].strip()}
    user_to_all_names[uid] = {r['name'].strip().lower()}
    email_to_uid[r['email'].strip().lower()] = uid

for idx, r in audit_df.iterrows():
    uid = r['user_id']
    field = r['field_name']
    for val in [r['old_value'], r['new_value']]:
        if pd.notna(val) and val:
            val_s = str(val).strip()
            if field == 'email':
                user_to_all_emails[uid].add(val_s.lower())
                email_to_uid[val_s.lower()] = uid
            elif field == 'phone':
                user_to_all_phones[uid].add(val_s)
            elif field == 'name':
                user_to_all_names[uid].add(val_s.lower())

all_records = evidence_parser.parse_all_evidence('dataset')

# Test matching for each sample case
merged = pd.merge(sample_reqs, sample_out, on='case_id')
for idx, r in merged.iterrows():
    req_email = r['email'].strip().lower()
    uid = email_to_uid.get(req_email)
    audit_at = r['audit_at']
    expected_steps = json.loads(r['steps_json'])
    
    # User identifiers
    user_emails = user_to_all_emails.get(uid, {req_email})
    
    # Filter parsed evidence for this user captured before or at audit_at
    user_ev_records = []
    for rec in all_records:
        if rec['captured_at'] > audit_at:
            continue
        # Check match
        matched = False
        if rec.get('user_id') == uid:
            matched = True
        elif rec.get('email') and rec['email'].lower() in user_emails:
            matched = True
        if matched:
            user_ev_records.append(rec)
            
    print(f"\n{r['case_id']}: uid={uid} expected_status={r['deletion_status']} ({len(expected_steps)} steps)")
    print(f"  Matched evidence records ({len(user_ev_records)}):")
    for ev in user_ev_records:
        print(f"    file={ev['file_id']} | sys={ev['system_id']} | res={ev['resource_id']} | type={ev['record_type']} | status={ev['status_raw']} | pii={ev['pii_exposed']}")
