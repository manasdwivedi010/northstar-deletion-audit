import pandas as pd
import json
import sqlite3
import os
import glob
import re

# Load all core CSVs
sample_reqs = pd.read_csv('dataset/sample_deletion_requests.csv')
sample_out = pd.read_csv('dataset/sample_output.csv')
users_df = pd.read_csv('dataset/user_identities.csv')
audit_df = pd.read_csv('dataset/user_audit_log.csv')
activity_df = pd.read_csv('dataset/system_activity.csv')
ev_manifest = pd.read_csv('dataset/evidence_files.csv').set_index('file_id')

# Identity resolution
user_to_all_emails = {}
user_to_all_phones = {}
user_to_all_names = {}
email_to_uid = {}

for idx, r in users_df.iterrows():
    uid = r['user_id']
    user_to_all_emails[uid] = {r['email'].strip().lower()}
    user_to_all_phones[uid] = {r['phone'].strip()}
    user_to_all_names[uid] = {r['name'].strip().lower()}
    email_to_uid[r['email'].strip().lower()] = uid

for idx, r in audit_df.iterrows():
    uid = r['user_id']
    field = r['field_name']
    for val in [r['old_value'], r['new_value']]:
        if pd.notna(val) and val:
            val_s = str(val).strip()
            if field == 'email':
                user_to_all_emails[uid].add(val_s.lower())
                email_to_uid[val_s.lower()] = uid
            elif field == 'phone':
                user_to_all_phones[uid].add(val_s)
            elif field == 'name':
                user_to_all_names[uid].add(val_s.lower())

print(f"Indexed {len(user_to_all_emails)} users.")
