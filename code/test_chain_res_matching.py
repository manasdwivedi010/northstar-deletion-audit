import pandas as pd
import json
import re
import sys
sys.path.insert(0, 'code')
import evidence_parser

sample_reqs = pd.read_csv('dataset/sample_deletion_requests.csv')
sample_out = pd.read_csv('dataset/sample_output.csv').set_index('case_id')
activity_df = pd.read_csv('dataset/system_activity.csv')
users_df = pd.read_csv('dataset/user_identities.csv')
audit_df = pd.read_csv('dataset/user_audit_log.csv')

# Build user maps
email_to_uid = {}
uid_to_emails = {}
uid_to_hashes = {}
import hashlib

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

all_evs = evidence_parser.parse_all_evidence('dataset')

# Map each resource to uid from evidence
res_to_uid = {}
for ev in all_evs:
    res = ev.get('resource_id')
    u = ev.get('user_id')
    e = ev.get('email')
    h = ev.get('hash')
    
    matched_uid = None
    if u and u in uid_to_emails:
        matched_uid = u
    elif e and e.lower() in email_to_uid:
        matched_uid = email_to_uid[e.lower()]
    elif h:
        for u_cand, hashes in uid_to_hashes.items():
            if h in hashes:
                matched_uid = u_cand
                break
    if matched_uid and res:
        res_to_uid[res] = matched_uid

# Group activities into batches/chains
dw_acts = activity_df[activity_df['source_system'] == 'deletion_worker'].copy()
dw_acts['time_pd'] = pd.to_datetime(dw_acts['event_time'])

# Partition dw_acts into time batches (gap > 2 hours starts new batch)
batches = []
curr_batch = []
last_time = None

for idx, r in dw_acts.iterrows():
    t = r['time_pd']
    if last_time is None or (t - last_time).total_seconds() > 2 * 3600:
        if curr_batch:
            batches.append(curr_batch)
        curr_batch = [r]
    else:
        curr_batch.append(r)
    last_time = t
if curr_batch:
    batches.append(curr_batch)

print(f"Total deletion worker batches: {len(batches)}")

# In each batch, match accounts to users
# Let's see: In each batch, what accounts and what non-accounts exist?
user_to_account = {}

# Also explicit accounts 1-10
for i in range(1, 11):
    user_to_account[f"user_{i:02d}"] = f"account_{i:03d}"
    user_to_account[f"user_{i}"] = f"account_{i:03d}"

# Check sample accuracy
correct = 0
for idx, r in sample_reqs.iterrows():
    cid = r['case_id']
    steps = json.loads(sample_out.loc[cid, 'steps_json'])
    exp_acc = [s['resource_id'] for s in steps if s['system_id'] == 'account_service']
    exp_id = exp_acc[0] if exp_acc else None
    
    em = r['email'].strip().lower()
    uid = email_to_uid.get(em)
    
    # Can we find exp_id via resources?
    # Resources belonging to this uid:
    my_res = [res for res, u in res_to_uid.items() if u == uid]
    # Find batch containing any of my_res
    matched_acc = None
    for b in batches:
        b_res = [row['resource_id'] for row in b]
        common = set(my_res).intersection(set(b_res))
        if common:
            # This batch processes user's resources!
            # Which account in this batch?
            b_accs = [row['resource_id'] for row in b if row['target_system'] == 'account_service']
            if len(b_accs) == 1:
                matched_acc = b_accs[0]
            elif len(b_accs) > 1:
                # Find the account closest in sequence to the common resource
                # Or matching the reported_status
                rep_st = r['reported_status']
                st_map = {'COMPLETE': 'SUCCESS', 'PARTIALLY_COMPLETE': 'PARTIAL', 'NOT_STARTED': 'FAILED'}
                cand_accs = [row['resource_id'] for row in b if row['target_system'] == 'account_service' and row['reported_result'] == st_map[rep_st]]
                if len(cand_accs) == 1:
                    matched_acc = cand_accs[0]
                elif len(cand_accs) > 1:
                    # Index distance in batch
                    res_idx = min(i for i, row in enumerate(b) if row['resource_id'] in common)
                    cand_dists = [(abs(i - res_idx), row['resource_id']) for i, row in enumerate(b) if row['resource_id'] in cand_accs]
                    cand_dists.sort()
                    matched_acc = cand_dists[0][1]
    
    final_acc = matched_acc or user_to_account.get(uid)
    if final_acc == exp_id:
        correct += 1
    else:
        print(f"{cid} ({uid}): exp={exp_id} vs pred={final_acc}")

print(f"\nExact account match via resource-chains: {correct} / {len(sample_reqs)}")
