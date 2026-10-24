import pandas as pd

sample_reqs = pd.read_csv('dataset/sample_deletion_requests.csv')
del_reqs = pd.read_csv('dataset/deletion_requests.csv')
all_reqs = pd.concat([sample_reqs, del_reqs], ignore_index=True)

activity = pd.read_csv('dataset/system_activity.csv')
del_worker_acts = activity[(activity['source_system'] == 'deletion_worker') & (activity['target_system'] == 'account_service')]
print(f"Total deletion worker -> account_service activities: {len(del_worker_acts)}")
print(f"Total requests: {len(all_reqs)}")

# For each request, find deletion worker activity between requested_at and reported_at + 1h
matches = []
no_matches = []
for idx, r in all_reqs.iterrows():
    req_time = r['requested_at']
    rep_time = r['reported_at']
    # activities between requested_at and reported_at
    acts = del_worker_acts[(del_worker_acts['event_time'] >= req_time) & (del_worker_acts['event_time'] <= rep_time)]
    if len(acts) == 0:
        # try slightly wider window
        acts = del_worker_acts[(del_worker_acts['event_time'] >= req_time) & (del_worker_acts['event_time'] <= '2026-10-30')]
    if len(acts) > 0:
        matches.append((r['case_id'], len(acts), acts.iloc[0]['resource_id'], acts.iloc[0]['event_time']))
    else:
        no_matches.append((r['case_id'], r['reported_status'], r['request_text']))

print(f"Matches: {len(matches)}")
print(f"No matches: {len(no_matches)}")
if no_matches:
    print("Sample no matches:", no_matches[:10])
