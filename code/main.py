"""
Northstar Shop Automated Deletion Audit Runner
Audits all requests in deletion_requests.csv and outputs output.csv.
"""
import os
import sys
import argparse
import json
import pandas as pd
import time

# Ensure code directory is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from audit_engine import DeletionAuditEngine

def natural_case_sort_key(cid: str):
    """Sort keys like case_01, case_33, case_100 in natural numeric order."""
    m = re.search(r'case_(\d+)', cid)
    return int(m.group(1)) if m else cid

import re

def main():
    parser = argparse.ArgumentParser(description="Run Northstar Shop Deletion Audit Agent")
    parser.add_argument("--dataset_dir", default=os.path.join(REPO_ROOT, "dataset"), help="Path to dataset directory")
    parser.add_argument("--input_csv", default=None, help="Path to input deletion requests CSV")
    parser.add_argument("--output_csv", default=os.path.join(REPO_ROOT, "output.csv"), help="Path to output CSV")
    args = parser.parse_args()

    input_path = args.input_csv or os.path.join(args.dataset_dir, "deletion_requests.csv")
    output_path = args.output_csv

    print(f"Initializing DeletionAuditEngine with dataset at: {args.dataset_dir}")
    t0 = time.time()
    engine = DeletionAuditEngine(args.dataset_dir)
    print(f"Engine initialized in {time.time() - t0:.2f} seconds.")

    print(f"Loading input requests from: {input_path}")
    requests_df = pd.read_csv(input_path)
    total_cases = len(requests_df)
    print(f"Found {total_cases} requests to audit.")

    results = []
    t_start = time.time()
    for idx, r in requests_df.iterrows():
        cid = r['case_id']
        status, steps = engine.audit_case(r)
        steps_json_str = json.dumps(steps, separators=(',', ':'))
        results.append({
            'case_id': cid,
            'deletion_status': status,
            'steps_json': steps_json_str
        })
        if (idx + 1) % 100 == 0 or (idx + 1) == total_cases:
            print(f"  Processed {idx + 1}/{total_cases} cases...")

    # Sort strictly by case_id (numeric/natural order as per problem spec: case_33 ... case_550)
    results_df = pd.DataFrame(results)
    results_df['sort_key'] = results_df['case_id'].apply(natural_case_sort_key)
    results_df = results_df.sort_values('sort_key').drop(columns=['sort_key'])

    # Write output.csv
    results_df.to_csv(output_path, index=False)
    print(f"Audit completed in {time.time() - t_start:.2f} seconds.")
    print(f"Successfully generated {output_path} with {len(results_df)} cases.")

if __name__ == "__main__":
    main()
