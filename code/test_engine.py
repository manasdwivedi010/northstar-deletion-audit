"""
Complete Deletion Audit Engine Prototype
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

class DeletionAuditEngine:
    def __init__(self, dataset_dir: str = 'dataset'):
        self.dataset_dir = dataset_dir
        self.load_data()
        
    def load_data(self):
        # 1. Identities
        users_df = pd.read_csv(os.path.join(self.dataset_dir, 'user_identities.csv'))
        audit_df = pd.read_csv(os.path.join(self.dataset_dir, 'user_audit_log.csv'))
        self.activity_df = pd.read_csv(os.path.join(self.dataset_dir, 'system_activity.csv'))
        self.manifest_df = pd.read_csv(os.path.join(self.dataset_dir, 'evidence_files.csv')).set_index('file_id')
        
        self.email_to_uid = {}
        self.uid_to_emails = {}
        self.uid_to_names = {}
        self.uid_to_phones = {}

        for idx, r in users_df.iterrows():
            uid = r['user_id']
            em = r['email'].strip().lower()
            self.email_to_uid[em] = uid
            self.uid_to_emails[uid] = {em}
            self.uid_to_names[uid] = {r['name'].strip().lower()}
            self.uid_to_phones[uid] = {r['phone'].strip()}

        for idx, r in audit_df.iterrows():
            uid = r['user_id']
            fld = r['field_name']
            for v in [r['old_value'], r['new_value']]:
                if pd.notna(v) and v:
                    v_s = str(v).strip()
                    if fld == 'email':
                        self.email_to_uid[v_s.lower()] = uid
                        self.uid_to_emails[uid].add(v_s.lower())
                    elif fld == 'name':
                        self.uid_to_names[uid].add(v_s.lower())
                    elif fld == 'phone':
                        self.uid_to_phones[uid].add(v_s)

        # 2. Activity analysis
        classify_rows = self.activity_df[self.activity_df['event_type'] == 'CLASSIFY_REQUEST']
        self.non_deletion_accounts = set(classify_rows['resource_id'].unique())
        
        # Link resource identity
        link_rows = self.activity_df[self.activity_df['event_type'] == 'LINK_RESOURCE_IDENTITY']
        self.identity_links = {}
        for idx, r in link_rows.iterrows():
            det = str(r['details'])
            em_m = re.search(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', det)
            uid_m = re.search(r'(user_\d+)', det)
            em = em_m.group(1).lower() if em_m else None
            uid = uid_m.group(1) if uid_m else None
            if em:
                self.identity_links[em] = r['resource_id']
            if uid:
                self.identity_links[uid] = r['resource_id']

        # 3. Parse all evidence
        self.all_ev_records = evidence_parser.parse_all_evidence(self.dataset_dir)
        print(f"Loaded {len(self.all_ev_records)} evidence records.")

    def audit_case(self, case_row: pd.Series) -> Tuple[str, List[Dict[str, Any]]]:
        cid = case_row['case_id']
        req_email = str(case_row['email']).strip().lower()
        req_text = str(case_row['request_text']).lower()
        req_at = case_row['requested_at']
        rep_at = case_row['reported_at']
        audit_at = case_row['audit_at']
        
        # Check NOT_APPLICABLE
        # In dataset, cases 533-542 are non-deletion requests
        is_non_deletion = False
        non_deletion_phrases = [
            "do not close", "do not delete", "don't delete", "keep the account", 
            "portable format", "misspelled", "out of date", "replace it with the new",
            "promotional emails", "marketing lists only", "information access request",
            "copy of last year", "copy of the information", "continue using the service"
        ]
        if any(p in req_text for p in non_deletion_phrases):
            is_non_deletion = True
            
        if is_non_deletion:
            return "NOT_APPLICABLE", []

        uid = self.email_to_uid.get(req_email)
        all_emails = self.uid_to_emails.get(uid, {req_email})
        
        # Candidate evidence files (captured <= audit_at, sorted by captured_at DESC)
        audit_pd = pd.to_datetime(audit_at)
        candidate_files = []
        for fid, row in self.manifest_df.iterrows():
            cap_pd = pd.to_datetime(row['captured_at'])
            if cap_pd <= audit_pd:
                candidate_files.append((fid, cap_pd, row['origin'], row['file_path']))
        candidate_files.sort(key=lambda x: x[1], reverse=True)

        return "COMPLETE", []

engine = DeletionAuditEngine('dataset')
print("Engine initialized successfully.")
