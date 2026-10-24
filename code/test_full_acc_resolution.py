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

# 2. Parse evidence and map resources to users
all_evs = evidence_parser.parse_all_evidence('dataset')
res_to_uid = {}
uid_to_acc_direct = {}

for ev in all_evs:
    res = ev.get('resource_id')
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
    if matched_u and res:
        res_to_uid[res] = matched_u
        if res.startswith('account_'):
            uid_to_acc_direct[matched_u] = res

# Explicit user 1-10 mapping
for i in range(1, 11):
    u = f"user_{i:02d}"
    acc = f"account_{i:03d}"
    uid_to_acc_direct[u] = acc
    uid_to_acc_direct[f"user_{i}"] = acc

# 3. Build chains from system_activity.csv
# In system_activity.csv, deletion worker events follow each other in time
dw = activity_df[activity_df['source_system'] == 'deletion_worker'].copy()
dw['time_pd'] = pd.to_datetime(dw['event_time'])

# Build deletion worker chains
# An account deletion starts a chain, and subsequent non-account deletions belong to the nearest account deletion
acc_to_chain_res = {}
curr_acc = None
for idx, r in dw.iterrows():
    tgt = r['target_system']
    res = r['resource_id']
    op = r['event_type']
    if tgt == 'account_service' and op == 'DELETE_RECORD':
        curr_acc = res
        acc_to_chain_res[curr_acc] = []
    elif curr_acc:
        acc_to_chain_res[curr_acc].append(res)

# Link accounts to users via chain resources
acc_to_uid_chain = {}
for acc, chain_res in acc_to_chain_res.items():
    u_counts = {}
    for res in chain_res:
        if res in res_to_uid:
            u = res_to_uid[res]
            u_counts[u] = u_counts.get(u, 0) + 1
    if u_counts:
        best_u = sorted(u_counts.items(), key=lambda x: x[1], reverse=True)[0][0]
        acc_to_uid_chain[acc] = best_u

# Test matching all 32 sample cases
STATUS_MAP = {'COMPLETE': 'SUCCESS', 'PARTIALLY_COMPLETE': 'PARTIAL', 'NOT_STARTED': 'FAILED'}
correct = 0

for idx, r in sample_reqs.iterrows():
    cid = r['case_id']
    steps = json.loads(sample_out.loc[cid, 'steps_json'])
    exp_acc = [s['resource_id'] for s in steps if s['system_id'] == 'account_service']
    exp_id = exp_acc[0] if exp_acc else None
    
    em = r['email'].strip().lower()
    uid = email_to_uid.get(em)
    rep_pd = pd.to_datetime(r['reported_at'])
    req_pd = pd.to_datetime(r['requested_at'])
    rep_st = r['reported_status']
    exp_dw_st = STATUS_MAP.get(rep_st)
    
    # 1. Direct match (user <= 10 or evidence account_xxx)
    pred = uid_to_acc_direct.get(uid)
    
    # 2. Match via chain resources
    if not pred:
        for acc, u in acc_to_uid_chain.items():
            if u == uid:
                pred = acc
                break
                
    # 3. Match from dw by window and unique status
    if not pred:
        cands = dw[(dw['target_system'] == 'account_service') & 
                   (dw['reported_result'] == exp_dw_st) &
                   (dw['time_pd'] >= req_pd - pd.Timedelta(hours=2)) &
                   (dw['time_pd'] <= rep_pd + pd.Timedelta(hours=2))].copy()
        if len(cands) == 1:
            pred = cands.iloc[0]['resource_id']
        elif len(cands) > 1:
            # Filter out accounts already assigned to another user
            unassigned = [row['resource_id'] for _, row in cands.iterrows() if row['resource_id'] not in acc_to_uid_chain]
            if len(unassigned) == 1:
                pred = unassigned[0]
            else:
                cands['diff'] = (rep_pd - cands['time_pd']).abs()
                pred = cands.sort_values('diff').iloc[0]['resource_id']
                
    if pred == exp_id:
        correct += 1
    else:
        print(f"Mismatch: {cid} ({uid}) exp={exp_id} pred={pred}")

print(f"\nTotal sample account accuracy: {correct} / {len(sample_reqs)} ({correct / len(sample_reqs) * 100:.1f}%)")
