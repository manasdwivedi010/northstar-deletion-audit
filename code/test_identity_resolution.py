import pandas as pd

sample_reqs = pd.read_csv('dataset/sample_deletion_requests.csv')
del_reqs = pd.read_csv('dataset/deletion_requests.csv')
all_reqs = pd.concat([sample_reqs, del_reqs], ignore_index=True)

users_df = pd.read_csv('dataset/user_identities.csv')
audit_df = pd.read_csv('dataset/user_audit_log.csv')

# Build mapping of email -> user_id
email_to_uid = {}
for idx, r in users_df.iterrows():
    email_to_uid[r['email'].strip().lower()] = r['user_id']

audit_email_to_uid = {}
for idx, r in audit_df[audit_df['field_name'] == 'email'].iterrows():
    if pd.notna(r['old_value']):
        audit_email_to_uid[r['old_value'].strip().lower()] = r['user_id']
    if pd.notna(r['new_value']):
        audit_email_to_uid[r['new_value'].strip().lower()] = r['user_id']

unresolved = []
resolved_direct = 0
resolved_audit = 0

for idx, r in all_reqs.iterrows():
    e = r['email'].strip().lower()
    if e in email_to_uid:
        resolved_direct += 1
    elif e in audit_email_to_uid:
        resolved_audit += 1
    else:
        unresolved.append((r['case_id'], r['email']))

print(f"Total cases: {len(all_reqs)}")
print(f"Resolved direct via identities: {resolved_direct}")
print(f"Resolved via audit log: {resolved_audit}")
print(f"Unresolved: {len(unresolved)}")
if unresolved:
    print("Unresolved cases:", unresolved)
