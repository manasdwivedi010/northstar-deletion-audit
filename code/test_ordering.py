import pandas as pd
import json

df = pd.read_csv('dataset/sample_output.csv')

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

mismatches = 0
for idx, r in df.iterrows():
    steps = json.loads(r['steps_json'])
    # Sort steps according to the rule
    sorted_steps = sorted(steps, key=lambda s: (
        PHASE_ORDER[s['phase']],
        OP_ORDER[s['operation']],
        s['system_id'],
        s['resource_id']
    ))
    # compare
    for i, (orig, expected) in enumerate(zip(steps, sorted_steps)):
        if (orig['phase'], orig['operation'], orig['system_id'], orig['resource_id']) != \
           (expected['phase'], expected['operation'], expected['system_id'], expected['resource_id']):
            print(f"Mismatch in {r['case_id']} step {i+1}:")
            print(f"  Orig:     {orig}")
            print(f"  Expected: {expected}")
            mismatches += 1

print(f"Total step order mismatches: {mismatches}")
