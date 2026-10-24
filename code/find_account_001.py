import pandas as pd

activity = pd.read_csv('dataset/system_activity.csv')
print(activity[activity['resource_id'] == 'account_001'])
print(activity[activity['details'].str.contains('account_001', na=False)])
