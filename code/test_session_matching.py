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

# 1. Build identity index
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

# 2. Parse all evidence and map resources to users
all_evs = evidence_parser.parse_all_evidence('dataset')
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

# 3. Build deletion worker sessions from system_activity.csv
# In system_activity.csv, a session starts with DELETE_RECORD account_service account_xxx
# and includes subsequent events until the next account_service DELETE_RECORD or time gap.
dw = activity_df[activity_df['source_system'] == 'deletion_worker'].copy()

sessions = []
curr_session = None

for idx, r in dw.iterrows():
    tgt = r['target_system']
    res = r['resource_id']
    op = r['event_type']
    
    if tgt == 'account_service' and op == 'DELETE_RECORD':
        if curr_session:
            sessions.append(curr_session)
        curr_session = {
            'account_id': res,
            'event_time': r['event_time'],
            'reported_result': r['reported_result'],
            'resources': [res]
        }
    elif curr_session:
        curr_session['resources'].append(res)
if curr_session:
    sessions.append(curr_session)

print(f"Total deletion worker sessions created: {len(sessions)}")

# Map each session to a uid if any resource in the session is in res_to_uid
session_to_uid = {}
uid_to_session_acc = {}

for s in sessions:
    acc = s['account_id']
    for res in s['resources']:
        if res in res_to_uid:
            u = res_to_uid[res]
            session_to_uid[acc] = u
            uid_to_session_acc[u] = acc

# Check sample accounts
correct = 0
for idx, r in sample_reqs.iterrows():
    cid = r['case_id']
    steps = json.loads(sample_out.loc[cid, 'steps_json'])
    exp_acc = [s['resource_id'] for s in steps if s['system_id'] == 'account_service']
    exp_id = exp_acc[0] if exp_acc else None
    
    em = r['email'].strip().lower()
    uid = email_to_uid.get(em)
    
    # Priority 1: user <= 10
    pred = None
    if uid:
        m = re.match(r'user_0*(\d+)', uid)
        if m and int(m.group(1)) <= 10:
            pred = f"account_{int(m.group(1)):03d}"
            
    # Priority 2: Session mapping via resources
    if not pred and uid in uid_to_session_acc:
        pred = uid_to_session_acc[uid]
        
    # Priority 3: Fallback by window + status
    if not pred:
        rep_pd = pd.to_datetime(r['reported_at'])
        req_pd = pd.to_datetime(r['requested_at'])
        rep_st = r['reported_status']
        st_map = {'COMPLETE': 'SUCCESS', 'PARTIALLY_COMPLETE': 'PARTIAL', 'NOT_STARTED': 'FAILED'}
        cands = [s for s in sessions if s['reported_result'] == st_map[rep_st] and 
                 req_pd - pd.Timedelta(hours=2) <= pd.to_datetime(s['event_time']) <= rep_pd + pd.Timedelta(hours=2)]
        if cands:
            cands.sort(key=lambda s: abs((rep_pd - pd.to_datetime(s['event_time'])).total_seconds()))
            pred = cands[0]['account_id']
            
    if pred == exp_id:
        correct += 1
    else:
        print(f"{cid} ({uid}): exp={exp_id} vs pred={pred}")

print(f"\nFinal sample account accuracy: {correct} / {len(sample_reqs)}")
