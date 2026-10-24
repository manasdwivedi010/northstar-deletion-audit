import pandas as pd

df = pd.read_csv('dataset/deletion_requests.csv')
for idx, r in df.iterrows():
    text = str(r['request_text']).lower()
    # Check phrases indicating keeping account or non-deletion actions
    keep_indicators = ['leave the account active', 'keep the account as it is', 'without removing any of my records', 'leave my profile', 'continue using the service', 'opt out of marketing', 'marketing emails only', 'do not delete', 'access my data', 'download my account information', 'copy of last year']
    if any(k in text for k in keep_indicators):
        print(f"{r['case_id']} | reported={r['reported_status']} | {r['request_text']}")
