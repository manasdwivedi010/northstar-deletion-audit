import pandas as pd
import json
import re
import sys
sys.path.insert(0, 'code')
import evidence_parser

sample_reqs = pd.read_csv('dataset/sample_deletion_requests.csv')
sample_out = pd.read_csv('dataset/sample_output.csv').set_index('case_id')
users_df = pd.read_csv('dataset/user_identities.csv')
audit_df = pd.read_csv('dataset/user_audit_log.csv')
activity_df = pd.read_csv('dataset/system_activity.csv')

# Build user identities
user_to_emails = {}
user_to_phones = {}
user_to_names = {}
email_to_uid = {}

for idx, r in users_df.iterrows():
    uid = r['user_id']
    em = str(r['email']).strip().lower()
    email_to_uid[em] = uid
    user_to_emails[uid] = {em}
    user_to_phones[uid] = {str(r['phone']).strip()}
    user_to_names[uid] = {str(r['name']).strip().lower()}

for idx, r in audit_df.iterrows():
    uid = r['user_id']
    fld = r['field_name']
    for v in [r['old_value'], r['new_value']]:
        if pd.notna(v) and v:
            v_s = str(v).strip()
            if fld == 'email':
                email_to_uid[v_s.lower()] = uid
                user_to_emails[uid].add(v_s.lower())
            elif fld == 'phone':
                user_to_phones[uid].add(v_s)
            elif fld == 'name':
                user_to_names[uid].add(v_s.lower())

all_evs = evidence_parser.parse_all_evidence('dataset')

# Map each evidence record to uid
ev_by_uid = {}
for ev in all_evs:
    matched_uids = set()
    if ev.get('user_id') and ev['user_id'] in user_to_emails:
        matched_uids.add(ev['user_id'])
    if ev.get('email') and ev['email'].lower() in email_to_uid:
        matched_uids.add(email_to_uid[ev['email'].lower()])
    for uid in matched_uids:
        ev_by_uid.setdefault(uid, []).append(ev)

print(f"Users with matched evidence: {len(ev_by_uid)}")

# Check sample cases
for idx, r in sample_reqs.iterrows():
    cid = r['case_id']
    em = r['email'].strip().lower()
    uid = email_to_uid.get(em)
    steps = json.loads(sample_out.loc[cid, 'steps_json'])
    exp_res = set(s['resource_id'] for s in steps)
    ev_res = set(e['resource_id'] for e in ev_by_uid.get(uid, []))
    print(f"{cid} ({uid}): exp_res={exp_res} | found_in_ev={ev_res}")
