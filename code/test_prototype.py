"""
Prototype Deletion Audit Engine tested on sample cases.
"""
import os
import re
import json
import sqlite3
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Set

# 1. Load ground truth and reference data
sample_reqs = pd.read_csv('dataset/sample_deletion_requests.csv')
sample_out = pd.read_csv('dataset/sample_output.csv').set_index('case_id')
users_df = pd.read_csv('dataset/user_identities.csv')
audit_df = pd.read_csv('dataset/user_audit_log.csv')
activity_df = pd.read_csv('dataset/system_activity.csv')
manifest_df = pd.read_csv('dataset/evidence_files.csv').set_index('file_id')

# Identity resolution maps
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

print("Identity maps loaded.")
