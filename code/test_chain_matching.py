import pandas as pd
import json
import re

activity_df = pd.read_csv('dataset/system_activity.csv')
sample_reqs = pd.read_csv('dataset/sample_deletion_requests.csv')
sample_out = pd.read_csv('dataset/sample_output.csv').set_index('case_id')
users_df = pd.read_csv('dataset/user_identities.csv')
audit_df = pd.read_csv('dataset/user_audit_log.csv')

email_to_uid = {}
uid_to_emails = {}
for idx, r in users_df.iterrows():
    uid = r['user_id']
    em = r['email'].strip().lower()
    email_to_uid[em] = uid
    uid_to_emails[uid] = {em}

for idx, r in audit_df.iterrows():
    uid = r['user_id']
    fld = r['field_name']
    for v in [r['old_value'], r['new_value']]:
        if pd.notna(v) and v and fld == 'email':
            em = str(v).strip().lower()
            email_to_uid[em] = uid
            uid_to_emails[uid].add(em)

# Group deletion worker events into chains
dw = activity_df[activity_df['source_system'] == 'deletion_worker']

account_chains = {}
curr_acc = None

for idx, r in dw.iterrows():
    target = r['target_system']
    res = r['resource_id']
    op = r['event_type']
    if target == 'account_service' and op == 'DELETE_RECORD':
        curr_acc = res
        account_chains[curr_acc] = []
    elif curr_acc:
        account_chains[curr_acc].append(res)

# For each chain, find all users associated with any resource in the chain
import evidence_parser
all_evs = evidence_parser.parse_all_evidence('dataset')
res_to_users = {}
res_to_emails = {}
for ev in all_evs:
    res = ev['resource_id']
    if ev.get('user_id'):
        res_to_users.setdefault(res, set()).add(ev['user_id'])
    if ev.get('email'):
        res_to_emails.setdefault(res, set()).add(ev['email'].lower())

# Match chains to sample cases
mapped_accounts = {}
for acc, chain_res in account_chains.items():
    users_in_chain = set()
    emails_in_chain = set()
    for res in [acc] + chain_res:
        if res in res_to_users:
            users_in_chain.update(res_to_users[res])
        if res in res_to_emails:
            emails_in_chain.update(res_to_emails[res])
    for u in users_in_chain:
        mapped_accounts[u] = acc
    for e in emails_in_chain:
        mapped_accounts[e] = acc

print(f"Total mapped accounts through chains: {len(mapped_accounts)}")
correct = 0
for idx, r in sample_reqs.iterrows():
    cid = r['case_id']
    em = r['email'].strip().lower()
    uid = email_to_uid.get(em)
    steps = json.loads(sample_out.loc[cid, 'steps_json'])
    exp_acc = [s['resource_id'] for s in steps if s['system_id'] == 'account_service']
    exp_id = exp_acc[0] if exp_acc else None
    pred_acc = mapped_accounts.get(em) or mapped_accounts.get(uid)
    if pred_acc == exp_id:
        correct += 1
    else:
        print(f"{cid} ({uid}): pred={pred_acc} vs exp={exp_id}")

print(f"Sample account accuracy via chain: {correct} / {len(sample_reqs)}")
