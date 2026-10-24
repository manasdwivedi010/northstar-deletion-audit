import pandas as pd
import json
import sys
sys.path.insert(0, 'code')
import evidence_parser

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

# Parse all evidence
all_ev_records = evidence_parser.parse_all_evidence('dataset')
print(f"Total parsed evidence records: {len(all_ev_records)}")

# Compare for sample cases
perfect_matches = 0
for idx, r in sample_reqs.iterrows():
    cid = r['case_id']
    req_email = r['email'].strip().lower()
    uid = email_to_uid.get(req_email)
    all_emails = uid_to_all_emails.get(uid, {req_email})
    audit_at = r['audit_at']
    
    expected_steps = json.loads(sample_out.loc[cid, 'steps_json'])
    expected_status = sample_out.loc[cid, 'deletion_status']
    
    # Expected resources:
    expected_res = set((s['system_id'], s['resource_id']) for s in expected_steps)
    
    # Evidence records for this user captured before or at audit_at
    user_evs = [ev for ev in all_ev_records if ev['captured_at'] <= audit_at and (
        (ev.get('user_id') == uid) or 
        (ev.get('email') and ev['email'].lower() in all_emails)
    )]
    
    found_res = set((ev['system_id'], ev['resource_id']) for ev in user_evs)
    
    diff = expected_res - found_res
    extra = found_res - expected_res
    if not diff and not extra:
        perfect_matches += 1
    else:
        print(f"\n{cid} ({uid}) status={expected_status}:")
        if diff: print(f"  MISSING resources: {diff}")
        if extra: print(f"  EXTRA resources: {extra}")

print(f"\nPerfect resource set matches: {perfect_matches} / {len(sample_reqs)}")
