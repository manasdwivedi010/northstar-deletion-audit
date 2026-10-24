"""
Evaluate audit_engine.py against sample_output.csv
"""
import json
import pandas as pd
import sys
sys.path.insert(0, 'code')
from audit_engine import DeletionAuditEngine

engine = DeletionAuditEngine('dataset')
sample_reqs = pd.read_csv('dataset/sample_deletion_requests.csv')
sample_out = pd.read_csv('dataset/sample_output.csv').set_index('case_id')

status_matches = 0
step_matches = 0
total_cases = len(sample_reqs)

for idx, r in sample_reqs.iterrows():
    cid = r['case_id']
    exp_status = sample_out.loc[cid, 'deletion_status']
    exp_steps = json.loads(sample_out.loc[cid, 'steps_json'])
    
    pred_status, pred_steps = engine.audit_case(r)
    
    status_ok = (pred_status == exp_status)
    if status_ok:
        status_matches += 1
        
    steps_ok = (pred_steps == exp_steps)
    if steps_ok:
        step_matches += 1
    else:
        print(f"\n{cid} MISMATCH: pred_status={pred_status} (exp {exp_status}) | pred_len={len(pred_steps)} (exp {len(exp_steps)})")
        # Print step diff
        pred_ops = [(s['phase'], s['operation'], s['system_id'], s['resource_id'], s.get('evidence_id')) for s in pred_steps]
        exp_ops = [(s['phase'], s['operation'], s['system_id'], s['resource_id'], s.get('evidence_id')) for s in exp_steps]
        diff_missing = [x for x in exp_ops if x not in pred_ops]
        diff_extra = [x for x in pred_ops if x not in exp_ops]
        if diff_missing:
            print(f"  Missing in pred: {diff_missing}")
        if diff_extra:
            print(f"  Extra in pred: {diff_extra}")

print("\n" + "=" * 50)
print(f"Status Accuracy: {status_matches} / {total_cases} ({status_matches / total_cases * 100:.1f}%)")
print(f"Exact Step Accuracy: {step_matches} / {total_cases} ({step_matches / total_cases * 100:.1f}%)")
print("=" * 50)
