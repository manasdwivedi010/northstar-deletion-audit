import pandas as pd
import json
import re

sample_reqs = pd.read_csv('dataset/sample_deletion_requests.csv')
sample_out = pd.read_csv('dataset/sample_output.csv').set_index('case_id')
activity_df = pd.read_csv('dataset/system_activity.csv')
users_df = pd.read_csv('dataset/user_identities.csv')
audit_df = pd.read_csv('dataset/user_audit_log.csv')

import sys
sys.path.insert(0, 'code')
import evidence_parser

all_evs = evidence_parser.parse_all_evidence('dataset')

# Map users to emails, phones, names
email_to_uid = {}
uid_to_emails = {}
for idx, r in users_df.iterrows():
    uid = r['user_id']
    em = str(r['email']).strip().lower()
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

# Deletion worker events for accounts
dw_accs = activity_df[(activity_df['source_system'] == 'deletion_worker') & (activity_df['target_system'] == 'account_service')].copy()
dw_accs['time_pd'] = pd.to_datetime(dw_accs['event_time'])

STATUS_MAP = {
    'COMPLETE': 'SUCCESS',
    'PARTIALLY_COMPLETE': 'PARTIAL',
    'NOT_STARTED': 'FAILED'
}

# Also gather any resources linked to each user from evidence
uid_to_resources = {}
for ev in all_evs:
    u = ev.get('user_id')
    e = ev.get('email')
    res = ev.get('resource_id')
    if u:
        uid_to_resources.setdefault(u, set()).add(res)
    if e and e.lower() in email_to_uid:
        uid_to_resources.setdefault(email_to_uid[e.lower()], set()).add(res)

print("Starting matching test...")
matches = 0
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
    exp_dw_res = STATUS_MAP.get(rep_st)
    
    # 1. User <= 10 explicit account_001..010
    pred_acc = None
    if uid:
        m = re.match(r'user_0*(\d+)', uid)
        if m and int(m.group(1)) <= 10:
            pred_acc = f"account_{int(m.group(1)):03d}"
            
    # 2. Check if user already has an account_xxx in evidence
    if not pred_acc and uid in uid_to_resources:
        for res in uid_to_resources[uid]:
            if res.startswith('account_'):
                pred_acc = res
                break
                
    # 3. Match from dw_accs by window + status
    if not pred_acc:
        # Candidate activities in [req_pd, rep_pd + 2h]
        cands = dw_accs[(dw_accs['time_pd'] >= req_pd - pd.Timedelta(hours=2)) & 
                        (dw_accs['time_pd'] <= rep_pd + pd.Timedelta(hours=2)) &
                        (dw_accs['reported_result'] == exp_dw_res)].copy()
        if len(cands) == 1:
            pred_acc = cands.iloc[0]['resource_id']
        elif len(cands) > 1:
            cands['diff'] = (rep_pd - cands['time_pd']).abs()
            pred_acc = cands.sort_values('diff').iloc[0]['resource_id']
            
    is_ok = (pred_acc == exp_id)
    if is_ok:
        matches += 1
    else:
        print(f"{cid} ({uid}): exp={exp_id} vs pred={pred_acc} (rep_at={r['reported_at']}, st={rep_st})")

print(f"\nAccount matches: {matches} / {len(sample_reqs)}")
