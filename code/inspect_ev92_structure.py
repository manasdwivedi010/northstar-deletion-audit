import json

with open('dataset/evidence/records/service_resource_export_20260915_114455.json') as f:
    data = json.load(f)

for svc, content in data['service_exports'].items():
    print(f"Service: {svc}")
    for k, v in content.items():
        print(f"  key: {k} (len={len(v) if isinstance(v, list) else type(v)})")
        if isinstance(v, list) and len(v) > 0:
            print(f"    sample item keys: {list(v[0].keys())}")
            print(f"    sample item: {v[0]}")
