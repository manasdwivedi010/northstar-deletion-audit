import pandas as pd

df = pd.read_csv('dataset/deletion_requests.csv')
for idx, r in df.iterrows():
    cid = int(r['case_id'].split('_')[1])
    if 533 <= cid <= 542:
        continue
    text = str(r['request_text']).lower()
    # Let's see if any of these mention 'not', 'keep', 'leave', 'access', 'export', 'change', 'reset'
    suspicious = ['not asking', 'do not', "don't", 'keep the', 'leave the', 'leave my', 'misspelled', 'information request', 'still use']
    if any(s in text for s in suspicious):
        print(f"{r['case_id']}: {r['request_text']}")
