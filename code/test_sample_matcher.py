"""
Detailed matcher for sample cases against sample_output.csv
"""
import os
import re
import json
import pandas as pd
import sys
sys.path.insert(0, 'code')
import evidence_parser

sample_reqs = pd.read_csv('dataset/sample_deletion_requests.csv')
sample_out = pd.read_csv('dataset/sample_output.csv').set_index('case_id')
users_df = pd.read_csv('dataset/user_identities.csv')
audit_df = pd.read_csv('dataset/user_audit_log.csv')
activity_df = pd.read_csv('dataset/system_activity.csv')
manifest_df = pd.read_csv('dataset/evidence_files.csv').set_index('file_id')

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

all_ev_records = evidence_parser.parse_all_evidence('dataset')

# Map each sample case
matches = 0
for idx, r in sample_reqs.iterrows():
    cid = r['case_id']
    req_email = r['email'].strip().lower()
    uid = email_to_uid.get(req_email)
    all_emails = uid_to_emails.get(uid, {req_email})
    audit_at = r['audit_at']
    
    expected_steps = json.loads(sample_out.loc[cid, 'steps_json'])
    expected_res = set((s['system_id'], s['resource_id']) for s in expected_steps)
    
    # Matched evidence records for this case
    case_recs = []
    for rec in all_ev_records:
        if rec['captured_at'] > audit_at:
            continue
        # Check match
        matched = False
        if rec.get('user_id') == uid:
            matched = True
        elif rec.get('email') and rec['email'].lower() in all_emails:
            matched = True
        if matched:
            case_recs.append(rec)
            
    found_res = set((rec['system_id'], rec['resource_id']) for rec in case_recs)
    
    # Account service: if user has account_id, check if verified absent
    diff = expected_res - found_res
    print(f"{cid} ({uid}): exp={len(expected_res)} found={len(found_res)} diff={diff}")
