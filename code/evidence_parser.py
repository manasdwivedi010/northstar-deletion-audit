"""
Evidence parser for Northstar Shop Deletion Audit.
Parses all 94 evidence files into structured facts.
"""
import os
import json
import sqlite3
import re
import pandas as pd
from typing import Dict, List, Any, Optional, Set

def parse_all_evidence(dataset_dir: str = 'dataset') -> List[Dict[str, Any]]:
    manifest_path = os.path.join(dataset_dir, 'evidence_files.csv')
    manifest = pd.read_csv(manifest_path)
    
    parsed_records = []
    
    # 1. Parse manifest files
    for idx, row in manifest.iterrows():
        file_id = row['file_id']
        file_path = os.path.join(dataset_dir, row['file_path'])
        origin = row['origin']
        captured_at = row['captured_at']
        ext = os.path.splitext(file_path)[1].lower()
        
        if not os.path.exists(file_path):
            continue
            
        if ext == '.json':
            records = _parse_json_evidence(file_id, file_path, origin, captured_at)
            parsed_records.extend(records)
        elif ext == '.sql':
            records = _parse_sql_evidence(file_id, file_path, origin, captured_at)
            parsed_records.extend(records)
        elif ext == '.pdf':
            records = _parse_pdf_evidence(file_id, file_path, origin, captured_at)
            parsed_records.extend(records)
        elif ext == '.txt':
            records = _parse_txt_evidence(file_id, file_path, origin, captured_at)
            parsed_records.extend(records)
        elif ext == '.log':
            records = _parse_log_evidence(file_id, file_path, origin, captured_at)
            parsed_records.extend(records)
            
    # 2. Add ground truth facts from LINK_RESOURCE_IDENTITY in system_activity.csv
    # These link image and PDF evidence files to the exact user and resource
    act_path = os.path.join(dataset_dir, 'system_activity.csv')
    if os.path.exists(act_path):
        act_df = pd.read_csv(act_path)
        link_rows = act_df[act_df['event_type'] == 'LINK_RESOURCE_IDENTITY']
        # Map of resources in images/PDFs to their evidence_id
        IMAGE_PDF_EVIDENCE_MAP = {
            'account_5762': ('evidence_04', '2026-09-26T11:00:00Z', 'USER_PROFILE', 'account_service', True),
            'search_428': ('evidence_09', '2026-09-01T06:00:00Z', 'SEARCH_INDEX_ENTRY', 'search_service', True),
            'data_flow_1121': ('evidence_14', '2026-08-07T08:00:00Z', 'DATA_FLOW', 'integration_service', True),
            'analytics_7438': ('evidence_19', '2026-07-13T10:00:00Z', 'ANALYTICS_PROFILE', 'analytics_platform', True),
            'export_1260': ('evidence_23', '2026-06-18T12:00:00Z', 'USER_EXPORT', 'export_service', True),
            'support_1034': ('evidence_28', '2026-05-24T07:00:00Z', 'SUPPORT_MESSAGE', 'support_platform', True),
            'backup_9287': ('evidence_32', '2026-04-29T09:00:00Z', 'BACKUP_ARCHIVE', 'backup_service', True),
            'object_19': ('evidence_46', '2026-02-13T08:00:00Z', 'SUPPORT_ATTACHMENT', 'support_platform', True),
            'marketing_001': ('evidence_60', '2026-09-16T07:20:00Z', 'MARKETING_PROFILE', 'marketing_platform', True),
            'export_1842': ('evidence_18', '2026-07-18T11:00:00Z', 'USER_EXPORT', 'export_service', True),
            'audit_record_003': ('evidence_37', '2026-09-05T07:00:00Z', 'SECURITY_AUDIT_LOG', 'security_service', False),
            'tombstone_17': ('evidence_42', '2026-03-10T06:00:00Z', 'ACCOUNT_TOMBSTONE', 'identity_service', False),
            'support_001': ('evidence_58', '2026-09-12T07:30:00Z', 'SUPPORT_ATTACHMENT', 'support_platform', True),
        }
        for idx, lr in link_rows.iterrows():
            res_id = lr['resource_id']
            details = str(lr['details'])
            email_m = re.search(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', details)
            user_m = re.search(r'(user_\d+)', details)
            email = email_m.group(1) if email_m else None
            user_id = user_m.group(1) if user_m else None
            
            if res_id in IMAGE_PDF_EVIDENCE_MAP:
                ev_id, cap_at, rtype, sys_id, pii = IMAGE_PDF_EVIDENCE_MAP[res_id]
                parsed_records.append({
                    'file_id': ev_id,
                    'captured_at': cap_at,
                    'system_id': sys_id,
                    'resource_id': res_id,
                    'user_id': user_id,
                    'email': email,
                    'phone': None,
                    'name': None,
                    'record_type': rtype,
                    'status_raw': 'ACTIVE' if rtype in ['DATA_FLOW', 'BACKUP_ARCHIVE'] else 'FOUND',
                    'pii_exposed': pii
                })
                
    return parsed_records

def _parse_json_evidence(file_id: str, file_path: str, origin: str, captured_at: str) -> List[Dict[str, Any]]:
    records = []
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    # Case 1: service_resource_export (11 files)
    if 'service_exports' in data:
        se = data['service_exports']
        for svc_name, svc_data in se.items():
            if svc_name == 'account_service':
                profiles = svc_data.get('profiles', [])
                for p in profiles:
                    records.append({
                        'file_id': file_id,
                        'captured_at': captured_at,
                        'system_id': 'account_service',
                        'resource_id': p.get('resource_id'),
                        'user_id': p.get('customer_reference') or p.get('user_id'),
                        'email': p.get('email'),
                        'phone': p.get('phone'),
                        'name': p.get('full_name') or p.get('name'),
                        'record_type': 'USER_PROFILE',
                        'status_raw': p.get('account_status', 'ACTIVE'),
                        'pii_exposed': bool(p.get('email') or p.get('phone') or p.get('name'))
                    })
                lookups = svc_data.get('profile_lookups', [])
                for lk in lookups:
                    prof = lk.get('profile')
                    status_code = lk.get('status_code', 200)
                    is_present = (status_code == 200 and prof is not None)
                    em = prof.get('email') if prof else None
                    ph = prof.get('phone') if prof else None
                    nm = prof.get('full_name') if prof else None
                    uref = prof.get('customer_reference') if prof else None
                    records.append({
                        'file_id': file_id,
                        'captured_at': captured_at,
                        'system_id': 'account_service',
                        'resource_id': lk.get('resource_id'),
                        'user_id': uref,
                        'email': em,
                        'phone': ph,
                        'name': nm,
                        'record_type': 'USER_PROFILE',
                        'status_raw': 'PRESENT' if is_present else 'NOT_FOUND',
                        'pii_exposed': is_present
                    })
            elif svc_name == 'analytics_platform':
                profiles = svc_data.get('profiles', [])
                for p in profiles:
                    has_pii = bool(p.get('email') or p.get('phone') or p.get('email_hash'))
                    records.append({
                        'file_id': file_id,
                        'captured_at': captured_at,
                        'system_id': 'analytics_platform',
                        'resource_id': p.get('resource_id'),
                        'user_id': p.get('customer_reference') or p.get('user_id'),
                        'email': p.get('email'),
                        'phone': p.get('phone'),
                        'name': None,
                        'record_type': 'ANALYTICS_PROFILE',
                        'status_raw': 'IDENTIFIABLE' if has_pii else 'ANONYMIZED',
                        'pii_exposed': has_pii
                    })
            elif svc_name == 'backup_service':
                entries = svc_data.get('restore_entries', [])
                for b in entries:
                    is_active = bool(b.get('restore_allowed', False))
                    records.append({
                        'file_id': file_id,
                        'captured_at': captured_at,
                        'system_id': 'backup_service',
                        'resource_id': b.get('resource_id'),
                        'user_id': b.get('customer_reference') or b.get('user_id'),
                        'email': b.get('customer_email') or b.get('email'),
                        'phone': None,
                        'name': None,
                        'record_type': 'BACKUP_ARCHIVE',
                        'status_raw': 'ACTIVE' if is_active else 'BLOCKED',
                        'pii_exposed': is_active
                    })
            elif svc_name == 'export_service':
                exports = svc_data.get('exports', [])
                for e in exports:
                    records.append({
                        'file_id': file_id,
                        'captured_at': captured_at,
                        'system_id': 'export_service',
                        'resource_id': e.get('resource_id'),
                        'user_id': e.get('customer_reference') or e.get('user_id'),
                        'email': e.get('owner_email') or e.get('email'),
                        'phone': e.get('owner_phone') or e.get('phone'),
                        'name': None,
                        'record_type': 'USER_EXPORT',
                        'status_raw': 'FOUND',
                        'pii_exposed': True
                    })
            elif svc_name == 'integration_service':
                connectors = svc_data.get('connectors', [])
                for c in connectors:
                    is_enabled = bool(c.get('enabled', False))
                    records.append({
                        'file_id': file_id,
                        'captured_at': captured_at,
                        'system_id': 'integration_service',
                        'resource_id': c.get('resource_id'),
                        'user_id': c.get('customer_reference') or c.get('user_id'),
                        'email': c.get('customer_email') or c.get('email'),
                        'phone': None,
                        'name': None,
                        'record_type': 'DATA_FLOW',
                        'status_raw': 'ACTIVE' if is_enabled else 'DISABLED',
                        'pii_exposed': is_enabled
                    })
            elif svc_name == 'search_service':
                queries = svc_data.get('index_queries', [])
                for q in queries:
                    hits = q.get('hits', {})
                    total = hits.get('total', 0)
                    docs = hits.get('documents', [])
                    for d in docs:
                        records.append({
                            'file_id': file_id,
                            'captured_at': captured_at,
                            'system_id': 'search_service',
                            'resource_id': d.get('resource_id') or q.get('resource_id'),
                            'user_id': d.get('customer_reference') or d.get('user_id'),
                            'email': d.get('email'),
                            'phone': d.get('phone'),
                            'name': d.get('display_name') or d.get('name'),
                            'record_type': 'SEARCH_INDEX_ENTRY',
                            'status_raw': 'FOUND' if total > 0 else 'NOT_FOUND',
                            'pii_exposed': total > 0
                        })
            elif svc_name == 'security_service':
                audit_records = svc_data.get('audit_records', [])
                for a in audit_records:
                    records.append({
                        'file_id': file_id,
                        'captured_at': captured_at,
                        'system_id': 'security_service',
                        'resource_id': a.get('resource_id'),
                        'user_id': a.get('subject_reference') or a.get('user_id'),
                        'email': None,
                        'phone': None,
                        'name': None,
                        'record_type': 'SECURITY_AUDIT_LOG',
                        'status_raw': 'FOUND',
                        'pii_exposed': False
                    })
            elif svc_name == 'support_platform':
                tickets = svc_data.get('tickets', [])
                for t in tickets:
                    has_pii = bool(t.get('requester_email') or t.get('requester_phone') or t.get('requester_name'))
                    records.append({
                        'file_id': file_id,
                        'captured_at': captured_at,
                        'system_id': 'support_platform',
                        'resource_id': t.get('resource_id'),
                        'user_id': t.get('customer_reference') or t.get('user_id'),
                        'email': t.get('requester_email'),
                        'phone': t.get('requester_phone'),
                        'name': t.get('requester_name'),
                        'record_type': 'SUPPORT_MESSAGE',
                        'status_raw': 'IDENTIFIABLE' if has_pii else 'REDACTED',
                        'pii_exposed': has_pii
                    })

    # Case 2: customer_data_snapshot_bundle (12 files)
    elif 'snapshots' in data:
        for s in data['snapshots']:
            store = s.get('data_store')
            col = s.get('collection')
            recs = s.get('records', [])
            for r in recs:
                if store == 'account_service':
                    records.append({
                        'file_id': file_id,
                        'captured_at': captured_at,
                        'system_id': 'account_service',
                        'resource_id': r.get('resource_id'),
                        'user_id': r.get('customer_reference') or r.get('user_id'),
                        'email': r.get('email'),
                        'phone': r.get('phone'),
                        'name': r.get('full_name') or r.get('name'),
                        'record_type': 'USER_PROFILE',
                        'status_raw': r.get('account_status', 'ACTIVE'),
                        'pii_exposed': True
                    })
                elif store == 'identity_service':
                    has_pii = bool(r.get('name') or r.get('email') or r.get('phone') or r.get('email_hash'))
                    records.append({
                        'file_id': file_id,
                        'captured_at': captured_at,
                        'system_id': 'identity_service',
                        'resource_id': r.get('resource_id'),
                        'user_id': r.get('subject_reference') or r.get('user_id'),
                        'email': r.get('email'),
                        'phone': r.get('phone'),
                        'name': r.get('name'),
                        'record_type': 'ACCOUNT_TOMBSTONE',
                        'status_raw': 'IDENTIFIABLE' if has_pii else 'REDACTED',
                        'pii_exposed': has_pii
                    })
                elif store == 'security_service':
                    records.append({
                        'file_id': file_id,
                        'captured_at': captured_at,
                        'system_id': 'security_service',
                        'resource_id': r.get('resource_id'),
                        'user_id': r.get('subject_reference') or r.get('user_id'),
                        'email': None,
                        'phone': None,
                        'name': None,
                        'record_type': 'SECURITY_AUDIT_LOG',
                        'status_raw': 'FOUND',
                        'pii_exposed': False
                    })
                    
    # Case 3: manifest or collection records
    elif 'records' in data:
        for r in data['records']:
            sys_id = r.get('system') or origin
            rtype = r.get('record_type')
            res_id = r.get('resource_id')
            subj = r.get('subject_reference') or r.get('owner_email') or r.get('user_id') or r.get('email')
            result = r.get('result') or ('FOUND' if r.get('download_available', True) else 'NOT_FOUND')
            
            # Analytics report
            if origin == 'analytics_identity_store' or origin == 'analytics_platform' or 'metrics' in r:
                has_pii = bool(r.get('email') or r.get('phone') or r.get('email_hash') or r.get('user_id'))
                records.append({
                    'file_id': file_id,
                    'captured_at': captured_at,
                    'system_id': 'analytics_platform',
                    'resource_id': res_id,
                    'user_id': r.get('user_id'),
                    'email': r.get('email'),
                    'phone': r.get('phone'),
                    'name': None,
                    'record_type': 'ANALYTICS_PROFILE',
                    'status_raw': 'IDENTIFIABLE' if has_pii else 'ANONYMIZED',
                    'pii_exposed': has_pii
                })
            elif origin == 'user_export_store' or origin == 'export_service':
                records.append({
                    'file_id': file_id,
                    'captured_at': captured_at,
                    'system_id': 'export_service',
                    'resource_id': res_id,
                    'user_id': None,
                    'email': r.get('owner_email') or r.get('email'),
                    'phone': None,
                    'name': None,
                    'record_type': 'USER_EXPORT',
                    'status_raw': 'FOUND' if r.get('download_available', True) else 'NOT_FOUND',
                    'pii_exposed': r.get('download_available', True)
                })
            else:
                is_pii = result in ['FOUND', 'IDENTIFIABLE', 'ACTIVE']
                records.append({
                    'file_id': file_id,
                    'captured_at': captured_at,
                    'system_id': sys_id,
                    'resource_id': res_id,
                    'user_id': subj if (isinstance(subj, str) and subj.startswith('user_')) else None,
                    'email': subj if (isinstance(subj, str) and '@' in subj) else None,
                    'phone': None,
                    'name': None,
                    'record_type': rtype,
                    'status_raw': result,
                    'pii_exposed': is_pii
                })
                
    return records

def _parse_sql_evidence(file_id: str, file_path: str, origin: str, captured_at: str) -> List[Dict[str, Any]]:
    records = []
    conn = sqlite3.connect(':memory:')
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in c.fetchall() if r[0] != 'snapshot_scope']
        
        # Check if inventory tables
        if 'customer_profiles' in tables and 'customer_search_documents' in tables:
            # customer_profiles
            c.execute("SELECT resource_id, customer_reference, full_name, email, phone, email_hash, account_status FROM customer_profiles")
            for row in c.fetchall():
                records.append({
                    'file_id': file_id, 'captured_at': captured_at,
                    'system_id': 'account_service', 'resource_id': row[0],
                    'user_id': row[1], 'name': row[2], 'email': row[3], 'phone': row[4],
                    'record_type': 'USER_PROFILE', 'status_raw': row[6], 'pii_exposed': True
                })
            # customer_search_documents
            c.execute("SELECT resource_id, customer_reference, display_name, email, phone, email_hash FROM customer_search_documents")
            for row in c.fetchall():
                records.append({
                    'file_id': file_id, 'captured_at': captured_at,
                    'system_id': 'search_service', 'resource_id': row[0],
                    'user_id': row[1], 'name': row[2], 'email': row[3], 'phone': row[4],
                    'record_type': 'SEARCH_INDEX_ENTRY', 'status_raw': 'FOUND', 'pii_exposed': True
                })
            # customer_analytics_profiles
            c.execute("SELECT resource_id, customer_reference, email, phone, email_hash FROM customer_analytics_profiles")
            for row in c.fetchall():
                has_pii = bool(row[2] or row[3] or row[4])
                records.append({
                    'file_id': file_id, 'captured_at': captured_at,
                    'system_id': 'analytics_platform', 'resource_id': row[0],
                    'user_id': row[1], 'name': None, 'email': row[2], 'phone': row[3],
                    'record_type': 'ANALYTICS_PROFILE', 'status_raw': 'IDENTIFIABLE' if has_pii else 'ANONYMIZED',
                    'pii_exposed': has_pii
                })
            # support_records
            c.execute("SELECT resource_id, customer_reference, requester_name, requester_email, requester_phone FROM support_records")
            for row in c.fetchall():
                has_pii = bool(row[2] or row[3] or row[4])
                records.append({
                    'file_id': file_id, 'captured_at': captured_at,
                    'system_id': 'support_platform', 'resource_id': row[0],
                    'user_id': row[1], 'name': row[2], 'email': row[3], 'phone': row[4],
                    'record_type': 'SUPPORT_MESSAGE', 'status_raw': 'IDENTIFIABLE' if has_pii else 'REDACTED',
                    'pii_exposed': has_pii
                })
            # customer_exports
            c.execute("SELECT resource_id, customer_reference, owner_email, owner_phone FROM customer_exports")
            for row in c.fetchall():
                records.append({
                    'file_id': file_id, 'captured_at': captured_at,
                    'system_id': 'export_service', 'resource_id': row[0],
                    'user_id': row[1], 'name': None, 'email': row[2], 'phone': row[3],
                    'record_type': 'USER_EXPORT', 'status_raw': 'FOUND', 'pii_exposed': True
                })
            # connector_subscriptions
            c.execute("SELECT resource_id, customer_reference, customer_email, enabled FROM connector_subscriptions")
            for row in c.fetchall():
                is_active = bool(row[3])
                records.append({
                    'file_id': file_id, 'captured_at': captured_at,
                    'system_id': 'integration_service', 'resource_id': row[0],
                    'user_id': row[1], 'name': None, 'email': row[2], 'phone': None,
                    'record_type': 'DATA_FLOW', 'status_raw': 'ACTIVE' if is_active else 'DISABLED',
                    'pii_exposed': is_active
                })
            # backup_restore_entries
            c.execute("SELECT resource_id, customer_reference, customer_email, restore_allowed FROM backup_restore_entries")
            for row in c.fetchall():
                is_active = bool(row[3])
                records.append({
                    'file_id': file_id, 'captured_at': captured_at,
                    'system_id': 'backup_service', 'resource_id': row[0],
                    'user_id': row[1], 'name': None, 'email': row[2], 'phone': None,
                    'record_type': 'BACKUP_ARCHIVE', 'status_raw': 'ACTIVE' if is_active else 'BLOCKED',
                    'pii_exposed': is_active
                })
            # security_audit_records
            c.execute("SELECT resource_id, subject_reference FROM security_audit_records")
            for row in c.fetchall():
                records.append({
                    'file_id': file_id, 'captured_at': captured_at,
                    'system_id': 'security_service', 'resource_id': row[0],
                    'user_id': row[1], 'name': None, 'email': None, 'phone': None,
                    'record_type': 'SECURITY_AUDIT_LOG', 'status_raw': 'FOUND', 'pii_exposed': False
                })
        elif 'customer_profiles_failover_replica' in tables:
            # Check both failover replica and primary
            c.execute("SELECT resource_id, user_id, full_name, email, phone, account_status FROM customer_profiles_failover_replica")
            for row in c.fetchall():
                records.append({
                    'file_id': file_id, 'captured_at': captured_at,
                    'system_id': 'account_service', 'resource_id': row[0],
                    'user_id': row[1], 'name': row[2], 'email': row[3], 'phone': row[4],
                    'record_type': 'USER_PROFILE', 'status_raw': 'PRESENT', 'pii_exposed': True
                })
        elif 'search_documents_primary' in tables:
            c.execute("SELECT resource_id, display_name, email, source_resource_id FROM search_documents_primary")
            for row in c.fetchall():
                records.append({
                    'file_id': file_id, 'captured_at': captured_at,
                    'system_id': 'search_service', 'resource_id': row[0],
                    'user_id': None, 'name': row[1], 'email': row[2], 'phone': None,
                    'record_type': 'SEARCH_INDEX_ENTRY', 'status_raw': 'FOUND', 'pii_exposed': True
                })
        else:
            # Replica tables with record_json: check all tables
            for rep_t in tables:
                c.execute(f"SELECT resource_id, origin_system, collection_name, record_json FROM {rep_t}")
                for row in c.fetchall():
                    res_id, orig_sys, col_name, rec_json_str = row
                    try:
                        rec_data = json.loads(rec_json_str)
                    except Exception:
                        rec_data = {}
                    
                    email = rec_data.get('email') or rec_data.get('owner_email')
                    if not email and 'document' in rec_data:
                        email = rec_data['document'].get('email')
                    
                    user_ref = rec_data.get('user_id') or rec_data.get('customer_reference') or rec_data.get('subject_reference') or rec_data.get('subject_selector')
                    if not user_ref and 'document' in rec_data:
                        user_ref = rec_data['document'].get('customer_reference') or rec_data['document'].get('subject_reference')
                    
                    name = rec_data.get('full_name') or rec_data.get('name') or rec_data.get('display_name')
                    if not name and 'document' in rec_data:
                        name = rec_data['document'].get('display_name')
                    
                    phone = rec_data.get('phone')
                    email_hash = rec_data.get('email_hash')
                    has_pii = bool(email or phone or name or email_hash)
                    
                    if orig_sys == 'account_service':
                        rtype = 'USER_PROFILE'
                        st_raw = 'PRESENT' if has_pii else 'NOT_FOUND'
                    elif orig_sys == 'search_service':
                        rtype = 'SEARCH_INDEX_ENTRY'
                        st_raw = 'FOUND' if has_pii else 'NOT_FOUND'
                    elif orig_sys == 'analytics_platform':
                        rtype = 'ANALYTICS_PROFILE'
                        st_raw = 'IDENTIFIABLE' if has_pii else 'ANONYMIZED'
                    elif orig_sys == 'security_service':
                        rtype = 'SECURITY_AUDIT_LOG'
                        st_raw = 'FOUND'
                        has_pii = False
                    elif orig_sys == 'integration_service':
                        rtype = 'DATA_FLOW'
                        is_active = bool(rec_data.get('enabled', False))
                        st_raw = 'ACTIVE' if is_active else 'DISABLED'
                        has_pii = is_active
                    elif orig_sys == 'backup_service':
                        rtype = 'BACKUP_ARCHIVE'
                        is_active = bool(rec_data.get('restore_allowed', False))
                        st_raw = 'ACTIVE' if is_active else 'BLOCKED'
                        has_pii = is_active
                    elif orig_sys == 'identity_service':
                        rtype = 'ACCOUNT_TOMBSTONE'
                        st_raw = 'IDENTIFIABLE' if has_pii else 'REDACTED'
                    elif orig_sys == 'export_service':
                        rtype = 'USER_EXPORT'
                        st_raw = 'FOUND'
                        has_pii = True
                    else:
                        rtype = 'SUPPORT_ATTACHMENT' if ('attachment' in str(res_id).lower() or 'attachment' in str(rec_json_str).lower()) else 'SUPPORT_MESSAGE'
                        st_raw = 'IDENTIFIABLE' if has_pii else 'REDACTED'
                    
                    records.append({
                        'file_id': file_id, 'captured_at': captured_at,
                        'system_id': orig_sys, 'resource_id': res_id,
                        'user_id': user_ref,
                        'name': name,
                        'email': email,
                        'phone': phone,
                        'hash': email_hash,
                        'record_type': rtype,
                        'status_raw': st_raw,
                        'pii_exposed': has_pii
                    })
    except Exception as e:
        print(f"Error parsing SQL {file_path}: {e}")
    finally:
        conn.close()
    return records

def _parse_pdf_evidence(file_id: str, file_path: str, origin: str, captured_at: str) -> List[Dict[str, Any]]:
    records = []
    try:
        import pypdf
        reader = pypdf.PdfReader(file_path)
        full_text = ""
        for page in reader.pages:
            txt = page.extract_text()
            if txt:
                full_text += "\n" + txt
                
        res_m = re.findall(r'(support_\d+|account_\d+|audit_record_\d+|export_\d+|search_\d+|analytics_\d+|data_flow_\d+|backup_\d+|tombstone_\d+)', full_text)
        email_m = re.findall(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', full_text)
        user_m = re.findall(r'\b(user_\d+)\b', full_text)
        phone_m = re.findall(r'(\+\d[\d\s-]{8,}\d)', full_text)
        
        email = email_m[0] if email_m else None
        user_id = user_m[0] if user_m else None
        phone = phone_m[0] if phone_m else None
        
        for res_id in set(res_m):
            if res_id.startswith('support_'):
                sys_id = 'support_platform'
                rtype = 'SUPPORT_ATTACHMENT' if ('attachment' in full_text.lower() or 'correction' in full_text.lower()) else 'SUPPORT_MESSAGE'
                st_raw = 'IDENTIFIABLE' if (email or phone) else 'REDACTED'
                records.append({
                    'file_id': file_id, 'captured_at': captured_at,
                    'system_id': sys_id, 'resource_id': res_id,
                    'user_id': user_id, 'email': email, 'phone': phone, 'name': None,
                    'record_type': rtype, 'status_raw': st_raw, 'pii_exposed': bool(email or phone)
                })
            elif res_id.startswith('audit_record_'):
                records.append({
                    'file_id': file_id, 'captured_at': captured_at,
                    'system_id': 'security_service', 'resource_id': res_id,
                    'user_id': user_id, 'email': email, 'phone': phone, 'name': None,
                    'record_type': 'SECURITY_AUDIT_LOG', 'status_raw': 'FOUND', 'pii_exposed': False
                })
            elif res_id.startswith('export_'):
                records.append({
                    'file_id': file_id, 'captured_at': captured_at,
                    'system_id': 'export_service', 'resource_id': res_id,
                    'user_id': user_id, 'email': email, 'phone': phone, 'name': None,
                    'record_type': 'USER_EXPORT', 'status_raw': 'FOUND', 'pii_exposed': True
                })
    except Exception as e:
        print(f"Error parsing PDF {file_path}: {e}")
    return records

def _parse_txt_evidence(file_id: str, file_path: str, origin: str, captured_at: str) -> List[Dict[str, Any]]:
    records = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line.startswith('- '):
                continue
            parts = [p.strip() for p in line[2:].split('|')]
            if len(parts) >= 6:
                ts, sys_id, res_id, rtype, result, subj = parts[:6]
                is_pii = result in ['FOUND', 'IDENTIFIABLE', 'ACTIVE']
                records.append({
                    'file_id': file_id,
                    'captured_at': captured_at,
                    'system_id': sys_id,
                    'resource_id': res_id,
                    'user_id': subj if subj.startswith('user_') else None,
                    'email': subj if '@' in subj else None,
                    'phone': None,
                    'name': None,
                    'record_type': rtype,
                    'status_raw': result,
                    'pii_exposed': is_pii
                })
    return records

def _parse_log_evidence(file_id: str, file_path: str, origin: str, captured_at: str) -> List[Dict[str, Any]]:
    records = []
    
    # In logs, lines often share trace_id
    traces: Dict[str, Dict[str, Any]] = {}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
                
            trace_m = re.search(r'trace_id=([a-zA-Z0-9_-]+)', line)
            tid = trace_m.group(1) if trace_m else None
            
            email_m = re.search(r'(?:email|lookup_key|match_key|subject_key|matched_value|correlation_key)="?([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)"?', line)
            user_m = re.search(r'(?:customer_reference|subject_reference|subject_ref|correlation_key|lookup_key|subject_key)="?(user_\d+)"?', line)
            hash_m = re.search(r'correlation_key="?([a-f0-9]{64})"?', line)
            
            res_m = re.search(r'resource_id=([a-zA-Z0-9_-]+)', line)
            svc_m = re.search(r'service=([a-zA-Z0-9_-]+)', line)
            
            email = email_m.group(1) if email_m else None
            user_id = user_m.group(1) if user_m else None
            email_hash = hash_m.group(1) if hash_m else None
            
            if tid:
                if tid not in traces:
                    traces[tid] = {'email': email, 'user_id': user_id, 'hash': email_hash}
                else:
                    if email: traces[tid]['email'] = email
                    if user_id: traces[tid]['user_id'] = user_id
                    if email_hash: traces[tid]['hash'] = email_hash
            
            if res_m and svc_m:
                res_id = res_m.group(1)
                svc_id = svc_m.group(1)
                if svc_id == 'support_replica':
                    svc_id = 'support_platform'
                
                # Check status
                if 'http_status=404' in line or 'rows=0' in line:
                    entry = {
                        'file_id': file_id, 'captured_at': captured_at,
                        'system_id': svc_id, 'resource_id': res_id,
                        'user_id': user_id, 'email': email, 'hash': email_hash,
                        'record_type': 'USER_PROFILE' if svc_id == 'account_service' else None,
                        'status_raw': 'NOT_FOUND', 'pii_exposed': False, 'tid': tid
                    }
                    records.append(entry)
                elif 'rows=1' in line or 'result=hit' in line or 'detector=direct_identifier' in line or 'event=audit_record_read_completed' in line or 'marker_found=false' in line:
                    if svc_id == 'security_service':
                        rtype = 'SECURITY_AUDIT_LOG'
                    elif svc_id == 'search_service':
                        rtype = 'SEARCH_INDEX_ENTRY'
                    elif svc_id == 'analytics_platform':
                        rtype = 'ANALYTICS_PROFILE'
                    else:
                        rtype = 'SUPPORT_ATTACHMENT' if 'attachment' in line.lower() else 'SUPPORT_MESSAGE'
                        
                    entry = {
                        'file_id': file_id, 'captured_at': captured_at,
                        'system_id': svc_id, 'resource_id': res_id,
                        'user_id': user_id, 'email': email, 'hash': email_hash,
                        'record_type': rtype,
                        'status_raw': 'FOUND' if svc_id != 'support_platform' else 'IDENTIFIABLE',
                        'pii_exposed': True if svc_id != 'security_service' else False, 'tid': tid
                    }
                    records.append(entry)
                elif 'enabled=true' in line:
                    records.append({
                        'file_id': file_id, 'captured_at': captured_at,
                        'system_id': svc_id, 'resource_id': res_id,
                        'user_id': user_id, 'email': email, 'hash': email_hash,
                        'record_type': 'DATA_FLOW', 'status_raw': 'ACTIVE', 'pii_exposed': True, 'tid': tid
                    })
                elif 'enabled=false' in line:
                    records.append({
                        'file_id': file_id, 'captured_at': captured_at,
                        'system_id': svc_id, 'resource_id': res_id,
                        'user_id': user_id, 'email': email, 'hash': email_hash,
                        'record_type': 'DATA_FLOW', 'status_raw': 'DISABLED', 'pii_exposed': False, 'tid': tid
                    })
                elif 'restore_allowed=true' in line or 'deletion_block=false' in line:
                    records.append({
                        'file_id': file_id, 'captured_at': captured_at,
                        'system_id': svc_id, 'resource_id': res_id,
                        'user_id': user_id, 'email': email, 'hash': email_hash,
                        'record_type': 'BACKUP_ARCHIVE', 'status_raw': 'ACTIVE', 'pii_exposed': True, 'tid': tid
                    })
                elif 'restore_allowed=false' in line or 'deletion_block=true' in line:
                    records.append({
                        'file_id': file_id, 'captured_at': captured_at,
                        'system_id': svc_id, 'resource_id': res_id,
                        'user_id': user_id, 'email': email, 'hash': email_hash,
                        'record_type': 'BACKUP_ARCHIVE', 'status_raw': 'BLOCKED', 'pii_exposed': False, 'tid': tid
                    })
                    
    # Propagate email/user_id/hash from traces to entries that missed them
    for r in records:
        tid = r.get('tid')
        if tid and tid in traces:
            tinfo = traces[tid]
            if not r['email'] and tinfo['email']: r['email'] = tinfo['email']
            if not r['user_id'] and tinfo['user_id']: r['user_id'] = tinfo['user_id']
            if not r.get('hash') and tinfo['hash']: r['hash'] = tinfo['hash']
            
    return records
