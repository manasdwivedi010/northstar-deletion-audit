"""
Build full audit for each case and compare against sample_output.csv
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
print(f"Total parsed evidence records: {len(all_ev_records)}")

# Index parsed evidence by (user_id, email, phone)
# Also map known resources from system_activity
dw_acts = activity_df[activity_df['source_system'] == 'deletion_worker']

print("Ready to test.")
