import json

with open('dataset/evidence/records/service_resource_export_20260915_114455.json') as f:
    data = json.load(f)

for svc, content in data['service_exports'].items():
    print(f"=== {svc} ===")
    for k, v in content.items():
        if isinstance(v, list):
            for item in v:
                subj = item.get('customer_reference') or item.get('subject_reference') or item.get('user_id') or item.get('email') or item.get('owner_email') or item.get('customer_email') or item.get('requester_email')
                res = item.get('resource_id')
                print(f"  {res}: subj={subj}")
