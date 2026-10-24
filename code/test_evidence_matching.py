"""
Test automatic matching of case to evidence and generation of steps
"""
import os
import re
import json
import sqlite3
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Set
import sys
sys.path.insert(0, 'code')
import evidence_parser

sample_reqs = pd.read_csv('dataset/sample_deletion_requests.csv')
sample_out = pd.read_csv('dataset/sample_output.csv').set_index('case_id')
users_df = pd.read_csv('dataset/user_identities.csv')
audit_df = pd.read_csv('dataset/user_audit_log.csv')
activity_df = pd.read_csv('dataset/system_activity.csv')
manifest_df = pd.read_csv('dataset/evidence_files.csv').set_index('file_id')

# Identity resolution
email_to_uid = {}
uid_to_emails = {}
uid_to_names = {}
uid_to_phones = {}

for idx, r in users_df.iterrows():
    uid = r['user_id']
    em = r['email'].strip().lower()
    email_to_uid[em] = uid
    uid_to_emails[uid] = {em}
    uid_to_names[uid] = {r['name'].strip().lower()}
    uid_to_phones[uid] = {r['phone'].strip()}

for idx, r in audit_df.iterrows():
    uid = r['user_id']
    fld = r['field_name']
    for v in [r['old_value'], r['new_value']]:
        if pd.notna(v) and v:
            v_s = str(v).strip()
            if fld == 'email':
                email_to_uid[v_s.lower()] = uid
                uid_to_emails[uid].add(v_s.lower())
            elif fld == 'name':
                uid_to_names[uid].add(v_s.lower())
            elif fld == 'phone':
                uid_to_phones[uid].add(v_s)

# Parse all evidence
all_ev_records = evidence_parser.parse_all_evidence('dataset')

# Map each evidence file to all records it contains
ev_to_records = {}
for r in all_ev_records:
    fid = r['file_id']
    if fid not in ev_to_records:
        ev_to_records[fid] = []
    ev_to_records[fid].append(r)

# Check matching for each sample case
print("Parsed records by evidence file:")
for fid, recs in sorted(ev_to_records.items()):
    if fid in ['evidence_01', 'evidence_03', 'evidence_05', 'evidence_51', 'evidence_54', 'evidence_56', 'evidence_57', 'evidence_58', 'evidence_59', 'evidence_61', 'evidence_92', 'evidence_93', 'evidence_94']:
        print(f"  {fid}: {len(recs)} records")
