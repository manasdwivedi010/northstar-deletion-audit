import pandas as pd

df = pd.read_csv('dataset/system_activity.csv')
for i in range(3595, 3625):
    r = df.loc[i]
    print(f"{r['activity_id']} | {r['event_time']} | {r['target_system']} | {r['resource_id']} | {r['event_type']} | {r['details']}")
