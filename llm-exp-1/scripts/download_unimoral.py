"""
Download UniMoral dataset and profile the English Reddit-derived dilemmas.
Outputs: scenario counts, annotator counts, entropy distribution, sample action pairs.
"""
import json
import math
import os
from pathlib import Path
from collections import Counter, defaultdict

print("Loading UniMoral dataset from HuggingFace...")
from datasets import load_dataset

ds = load_dataset("shivaniku/UniMoral")
print(f"Dataset splits: {list(ds.keys())}")

# Inspect available splits and columns
for split_name in ds:
    split = ds[split_name]
    print(f"\n=== Split: {split_name} ===")
    print(f"  Rows: {len(split)}")
    print(f"  Columns: {split.column_names}")
    # Show first record
    if len(split) > 0:
        rec = split[0]
        print(f"  Sample record keys: {list(rec.keys())}")
        for k, v in rec.items():
            val_str = str(v)
            if len(val_str) > 200:
                val_str = val_str[:200] + "..."
            print(f"    {k}: {val_str}")

# Save raw data for offline use
out_dir = Path("data/raw/unimoral")
out_dir.mkdir(parents=True, exist_ok=True)

for split_name in ds:
    split = ds[split_name]
    out_path = out_dir / f"{split_name}.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        for i in range(len(split)):
            rec = split[i]
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"\nSaved {len(split)} records to {out_path}")
