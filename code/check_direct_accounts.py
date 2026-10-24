import pandas as pd
import json
import re
import hashlib
import sys
sys.path.insert(0, 'code')
import evidence_parser

sample_reqs = pd.read_csv('dataset/sample_deletion_requests.csv')
sample_out = pd.read_csv('dataset/sample_output.csv').set_index('case_id')
activity_df = pd.read_csv('dataset/system_activity.csv')
users_df = pd.read_csv('dataset/user_identities.csv')
audit_df = pd.read_csv('dataset/user_audit_log.csv')

# 1. Identity maps
email_to_uid = {}
uid_to_emails = {}
uid_to_hashes = {}
for idx, r in users_df.iterrows():
    uid = r['user_id']
    em = str(r['email']).strip().lower()
    email_to_uid[em] = uid
    uid_to_emails[uid] = {em}
    uid_to_hashes[uid] = {hashlib.sha256(em.encode()).hexdigest()}

for idx, r in audit_df.iterrows():
    uid = r['user_id']
    fld = r['field_name']
    for v in [r['old_value'], r['new_value']]:
        if pd.notna(v) and v and fld == 'email':
            em = str(v).strip().lower()
            email_to_uid[em] = uid
            uid_to_emails[uid].add(em)
            uid_to_hashes[uid].add(hashlib.sha256(em.encode()).hexdigest())

# 2. Parse all evidence
all_evs = evidence_parser.parse_all_evidence('dataset')

# Map accounts directly found in evidence to users
acc_to_uid = {}
uid_to_acc = {}
for ev in all_evs:
    res = ev.get('resource_id')
    if res and res.startswith('account_'):
        u = ev.get('user_id')
        e = ev.get('email')
        h = ev.get('hash')
        matched_u = None
        if u and u in uid_to_emails:
            matched_u = u
        elif e and e.lower() in email_to_uid:
            matched_u = email_to_uid[e.lower()]
        elif h:
            for cand_u, hashes in uid_to_hashes.items():
                if h in hashes:
                    matched_u = cand_u
                    break
        if matched_u:
            acc_to_uid[res] = matched_u
            uid_to_acc[matched_u] = res

# 3. Add explicit user <= 10 mapping
for i in range(1, 11):
    u = f"user_{i:02d}"
    acc = f"account_{i:03d}"
    acc_to_uid[acc] = u
    uid_to_acc[u] = acc
    uid_to_acc[f"user_{i}"] = acc

print(f"Users with directly known account: {len(uid_to_acc)}")

# Check sample accounts
known = 0
for idx, r in sample_reqs.iterrows():
    cid = r['case_id']
    steps = json.loads(sample_out.loc[cid, 'steps_json'])
    exp_acc = [s['resource_id'] for s in steps if s['system_id'] == 'account_service']
    exp_id = exp_acc[0] if exp_acc else None
    
    em = r['email'].strip().lower()
    uid = email_to_uid.get(em)
    pred = uid_to_acc.get(uid)
    if pred == exp_id:
        known += 1
    else:
        print(f"Unknown in sample: {cid} ({uid}) exp={exp_id} pred={pred}")

print(f"Direct known sample accounts: {known} / 32")
