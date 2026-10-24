import pandas as pd
import json

output_path = 'output.csv'
df = pd.read_csv(output_path)

print(f"Total rows: {len(df)}")
print(f"Columns: {list(df.columns)}")
assert len(df) == 518, f"Expected 518 rows, got {len(df)}"
assert list(df.columns) == ['case_id', 'deletion_status', 'steps_json'], f"Wrong columns: {list(df.columns)}"

# Check case_id range and ordering
first_case = df.iloc[0]['case_id']
last_case = df.iloc[-1]['case_id']
print(f"First case: {first_case}, Last case: {last_case}")
assert first_case == 'case_33', f"First case should be case_33, got {first_case}"
assert last_case == 'case_550', f"Last case should be case_550, got {last_case}"

# Check status distribution
status_counts = df['deletion_status'].value_counts()
print("\nStatus distribution:")
print(status_counts)

# Check JSON parsing and schema of each row
for idx, r in df.iterrows():
    cid = r['case_id']
    st = r['deletion_status']
    steps = json.loads(r['steps_json'])
    
    if st == 'NOT_APPLICABLE':
        assert steps == [], f"{cid} is NOT_APPLICABLE but has steps: {steps}"
    elif st == 'COMPLETE':
        assert len(steps) > 0, f"{cid} is COMPLETE but has no steps"
        for s in steps:
            assert s['phase'] == 'VERIFICATION', f"{cid} COMPLETE has non-verification phase: {s['phase']}"
            assert s['evidence_id'] != '', f"{cid} COMPLETE step missing evidence_id: {s}"
    elif st == 'INCOMPLETE':
        assert len(steps) > 0, f"{cid} is INCOMPLETE but has no steps"
        findings = [s for s in steps if s['phase'] == 'FINDING']
        assert len(findings) > 0, f"{cid} INCOMPLETE has no findings"
        for s in steps:
            if s['phase'] in ['REMEDIATION', 'VERIFICATION']:
                assert s['evidence_id'] == '', f"{cid} INCOMPLETE non-finding has evidence_id: {s['evidence_id']}"
            elif s['phase'] == 'FINDING':
                assert s['evidence_id'] != '', f"{cid} INCOMPLETE finding missing evidence_id: {s}"

print("\nAll 518 rows passed schema, JSON, ordering, and consistency checks successfully!")
