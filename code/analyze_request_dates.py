import pandas as pd

del_reqs = pd.read_csv('dataset/deletion_requests.csv')
ev_files = pd.read_csv('dataset/evidence_files.csv')

print(f"Total requests: {len(del_reqs)}")
print("\nUnique audit_at values in deletion_requests.csv:")
audit_dates = del_reqs['audit_at'].value_counts()
print(audit_dates)

print("\nEvidence files captured_at matching or preceding those audit dates:")
for dt in sorted(del_reqs['audit_at'].unique()):
    # find evidence files within 48h before dt
    dt_pd = pd.to_datetime(dt)
    matched_evs = []
    for idx, r in ev_files.iterrows():
        cap_pd = pd.to_datetime(r['captured_at'])
        if cap_pd <= dt_pd and (dt_pd - cap_pd).total_seconds() <= 48 * 3600:
            matched_evs.append((r['file_id'], r['origin'], (dt_pd - cap_pd).total_seconds() / 3600))
    print(f"audit_at: {dt} (count={len(del_reqs[del_reqs['audit_at'] == dt])}) -> nearby evidence: {[e[0] for e in matched_evs]}")
