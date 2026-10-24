import pandas as pd
import json
import hashlib
import sys
sys.path.insert(0, 'code')
import evidence_parser

sample_reqs = pd.read_csv('dataset/sample_deletion_requests.csv').set_index('case_id')
sample_out = pd.read_csv('dataset/sample_output.csv').set_index('case_id')
manifest = pd.read_csv('dataset/evidence_files.csv').set_index('file_id')
users_df = pd.read_csv('dataset/user_identities.csv')
audit_df = pd.read_csv('dataset/user_audit_log.csv')

# Build identity maps
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

all_evs = evidence_parser.parse_all_evidence('dataset')

# Group parsed evidence by file_id
ev_by_file = {}
for ev in all_evs:
    ev_by_file.setdefault(ev['file_id'], []).append(ev)

# For each sample case, test finding primary evidence file
correct_ev = 0
for cid in sample_reqs.index:
    audit_at = pd.to_datetime(sample_reqs.loc[cid, 'audit_at'])
    req_email = sample_reqs.loc[cid, 'email'].strip().lower()
    uid = email_to_uid.get(req_email)
    my_emails = uid_to_emails.get(uid, {req_email})
    my_hashes = uid_to_hashes.get(uid, set())
    
    # Expected evidence from sample_output
    steps = json.loads(sample_out.loc[cid, 'steps_json'])
    exp_eids = set(s['evidence_id'] for s in steps if s.get('evidence_id'))
    
    # Candidate files: captured at or before audit_at
    cands = []
    for fid, row in manifest.iterrows():
        cap_at = pd.to_datetime(row['captured_at'])
        if cap_at <= audit_at:
            # Check if this file has records matching user
            recs = ev_by_file.get(fid, [])
            match_count = 0
            for r in recs:
                if r.get('user_id') == uid:
                    match_count += 1
                elif r.get('email') and r['email'].lower() in my_emails:
                    match_count += 1
                elif r.get('hash') and r['hash'] in my_hashes:
                    match_count += 1
            if match_count > 0:
                diff_sec = (audit_at - cap_at).total_seconds()
                cands.append((fid, match_count, diff_sec))
                
    # Sort candidates by:
    # 1. diff_sec (closest to audit_at first)
    cands.sort(key=lambda x: x[2])
    
    pred_eid = cands[0][0] if cands else None
    
    # Is pred_eid in exp_eids?
    if pred_eid in exp_eids:
        correct_ev += 1
    else:
        print(f"{cid} ({uid}): exp={exp_eids} pred={pred_eid} | cands={[(c[0], c[1], round(c[2]/3600, 1)) for c in cands[:3]]}")

print(f"\nPrimary evidence file accuracy: {correct_ev} / {len(sample_reqs)} ({correct_ev / len(sample_reqs) * 100:.1f}%)")
