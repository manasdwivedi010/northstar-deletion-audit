import pandas as pd

df = pd.read_csv('dataset/evidence_files.csv')
periodic_origins = {'records_assurance_snapshot_bundle', 'service_resource_export', 'customer_data_inventory_capture', 'service_readback_logs', 'central_observability_export'}
remaining = df[~df['origin'].isin(periodic_origins)].sort_values('captured_at')
print(f"Total non-periodic evidence files: {len(remaining)}")
for idx, r in remaining.iterrows():
    print(f"  {r['file_id']} | {r['captured_at']} | {r['origin']} | {r['file_path']}")
