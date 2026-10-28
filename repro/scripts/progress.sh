#!/bin/zsh
# Usage: ./repro/scripts/progress.sh [pattern]   e.g. phi4-mini, tev1_4b
# Without a pattern, shows the most recently updated run.
pattern=${1:-}
d=$(ls -td runs/*${pattern}*/ 2>/dev/null | head -1)
if [[ -z "$d" || ! -f "$d/decisions.jsonl" ]]; then echo "no run found"; exit 1; fi
python3 -c "
import json, collections
rows = [json.loads(l) for l in open('${d}decisions.jsonl')]
if not rows:
    print('$d: no decisions yet'); raise SystemExit
c = collections.Counter(r['seed'] for r in rows)
last = rows[-1]
lat = sorted(r['latencyMs'] for r in rows[-50:] if r['latencyMs'] is not None)
print('$d')
print('games started:', len(c), '| decisions per seed:', dict(c))
print('current seed:', last['seed'], '| game time: %.0f s' % (last['askedTick']/30), '| median latency (last 50): %d ms' % lat[len(lat)//2])
"
