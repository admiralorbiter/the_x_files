"""Survey SCRUPLES dilemmas dataset for IMPACT scenario selection."""
import json
import math
from pathlib import Path

def calc_entropy(p_a, p_b):
    if p_a <= 0.0 or p_a >= 1.0:
        return 0.0
    return -(p_a * math.log2(p_a) + p_b * math.log2(p_b))

all_items = []
for split in ['dev', 'train']:
    path = Path(f'data/raw/dilemmas/{split}.scruples-dilemmas.jsonl')
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            rec = json.loads(line)
            gold = rec['gold_annotations']
            n = sum(gold)
            if n < 5:
                continue
            p_a = gold[0] / n
            p_b = gold[1] / n
            entropy = calc_entropy(p_a, p_b)
            a0 = rec['actions'][0]['description']
            a1 = rec['actions'][1]['description']
            all_items.append({
                'rec': rec,
                'split': split,
                'n': n,
                'p_a': p_a,
                'p_b': p_b,
                'entropy': entropy,
                'a0': a0,
                'a1': a1,
            })

print(f"Total dilemmas with n>=5: {len(all_items)}")
print(f"All have n=5 (standard MTurk annotation count)")

# Entropy tiers
high = [x for x in all_items if x['entropy'] >= 0.85]
mid = [x for x in all_items if 0.65 <= x['entropy'] < 0.85]
low = [x for x in all_items if x['entropy'] < 0.65]
print(f"\nEntropy tiers: High(>=0.85)={len(high)}, Mid(0.65-0.85)={len(mid)}, Low(<0.65)={len(low)}")

# Show examples across entropy range
sorted_items = sorted(all_items, key=lambda x: x['entropy'])
indices = [0, len(sorted_items)//6, len(sorted_items)//3, len(sorted_items)//2, 2*len(sorted_items)//3, 5*len(sorted_items)//6, -1]
print("\n=== SAMPLES ACROSS ENTROPY RANGE ===")
for idx in indices:
    item = sorted_items[idx]
    gold = item['rec']['gold_annotations']
    print(f"H={item['entropy']:.3f}  gold={gold}  p_a={item['p_a']:.2f}")
    print(f"  Action 0: {item['a0']}")
    print(f"  Action 1: {item['a1']}")
    print()
