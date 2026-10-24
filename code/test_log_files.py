import glob
import os

log_files = glob.glob('dataset/evidence/logs/*.log')
print(f"Total log files: {len(log_files)}")

for lf in log_files:
    fname = os.path.basename(lf)
    with open(lf, 'r', encoding='utf-8') as f:
        first_line = f.readline().strip()
    print(f"{fname[:35]}: {first_line[:90]}")
