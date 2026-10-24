import json

with open('dataset/evidence/records/service_resource_export_20260915_114455.json') as f:
    data = json.load(f)

for svc, items in data['service_exports'].items():
    print(f"Service: {svc}, type: {type(items)}")
    if isinstance(items, dict):
        print(f"  dict keys: {list(items.keys())[:5]}")
        first_key = list(items.keys())[0]
        print(f"  sample entry [{first_key}]: {items[first_key]}")
    elif isinstance(items, list):
        print(f"  list len: {len(items)}, first item: {items[0]}")
