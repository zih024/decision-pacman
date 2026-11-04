#!/usr/bin/env python3
"""Compare per-state choices between training weights (score_mlx/score_hf) and the served model (score_ollama).

Usage: python3 repro/scripts/parity.py TRAINING_JSON SERVED_JSON
"""
import json
import sys


def load_rows(path):
    d = json.load(open(path))
    rows = d["details"] if isinstance(d, dict) else d
    return {(r["seed"], r["tick"]): r["probabilities"] for r in rows}


def argmax(p):
    return max(p, key=p.get)


a, b = load_rows(sys.argv[1]), load_rows(sys.argv[2])
keys = sorted(set(a) & set(b))
same, max_diff, gaps = 0, 0.0, []
for k in keys:
    pa, pb = a[k], b[k]
    if argmax(pa) == argmax(pb):
        same += 1
    else:
        top = sorted(pa.values(), reverse=True)
        gaps.append((k, argmax(pa), argmax(pb), round(top[0] - top[1], 4)))
    max_diff = max(max_diff, max(abs(pa[o] - pb[o]) for o in pa))

print(f"states compared: {len(keys)}")
print(f"same choice: {same}/{len(keys)}")
print(f"max |prob difference| on any option: {max_diff:.4f}")
for k, ca, cb, gap in gaps:
    print(f"  disagree at seed {k[0]} tick {k[1]}: training={ca}, served={cb}, training top-2 gap={gap}")
