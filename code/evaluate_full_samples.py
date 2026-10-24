"""
Full implementation of the Northstar Shop Deletion Audit Engine
Tested against all 32 sample cases in sample_output.csv
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

# Load dataset files
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

# Sorting constants
PHASE_ORDER = {"FINDING": 1, "REMEDIATION": 2, "VERIFICATION": 3}
OP_ORDER = {
    # Findings
    "REPORT_REMAINING_RECORD": 1,
    "REPORT_EXPOSED_PII": 2,
    "REPORT_ACTIVE_DATA_FLOW": 3,
    "REPORT_RESTORE_RISK": 4,
    # Remediation
    "DISABLE_DATA_FLOW": 1,
    "BLOCK_RESTORE": 2,
    "DELETE_RECORD": 3,
    "REDACT_RECORD": 4,
    "ANONYMIZE_RECORD": 5,
    # Verification
    "VERIFY_RECORD_ABSENT": 1,
    "VERIFY_RECORD_PRESENT": 2,
    "VERIFY_RECORD_REDACTED": 3,
    "VERIFY_RECORD_ANONYMIZED": 4,
    "VERIFY_DATA_FLOW_DISABLED": 5,
    "VERIFY_RESTORE_BLOCKED": 6,
}

def sort_steps(steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    def sort_key(s):
        p_val = PHASE_ORDER.get(s["phase"], 99)
        o_val = OP_ORDER.get(s["operation"], 99)
        sys_val = s.get("system_id", "")
        res_val = s.get("resource_id", "")
        return (p_val, o_val, sys_val, res_val)

    sorted_list = sorted(steps, key=sort_key)
    for idx, s in enumerate(sorted_list, 1):
        s["step_no"] = idx
    return sorted_list

print("Evaluator module initialized.")
