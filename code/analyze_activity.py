import pandas as pd

activity = pd.read_csv('dataset/system_activity.csv')

for et in ['DELETE_RECORD', 'ANONYMIZE_RECORD', 'REDACT_RECORD', 'DISABLE_DATA_FLOW', 'BLOCK_RESTORE', 'RETAIN_RECORD', 'CREATE_EXPORT', 'INDEX_RECORD', 'CHECK_DATA_FLOW', 'CHECK_RESTORE_ACCESS', 'LINK_RESOURCE_IDENTITY', 'RESTORE_BACKUP']:
    sub = activity[activity['event_type'] == et]
    print(f"\n=== Event Type: {et} ({len(sub)} rows) ===")
    for idx, r in sub.head(4).iterrows():
        print(f"  {r['event_time']} | {r['source_system']} -> {r['target_system']} | res={r['resource_id']} | res_result={r['reported_result']} | {r['details']}")
