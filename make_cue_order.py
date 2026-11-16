"""Create the ONE fixed presentation order of the 270 cue phrases (cue_order_fixed.csv).

Every participant, in both conditions, sees the phrases in this order. The order is random except
that no valence appears more than MAX_SAME_VALENCE_RUN (3) times in a row.
Run this only once, before data collection; it refuses to overwrite an existing order unless you
add --overwrite.

    python3 make_cue_order.py
"""
import csv
import sys
from collections import Counter

import config as C
import design

if C.CUE_ORDER_FILE.exists() and "--overwrite" not in sys.argv:
    raise SystemExit(f"{C.CUE_ORDER_FILE.name} already exists. Add --overwrite only if data collection "
                     "has not started yet.")

cues = design.load_cues()
order = design.constrained_order(cues, C.CUE_ORDER_SEED)

with open(C.CUE_ORDER_FILE, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["position", "cue_id", "valence", "text"])
    for i, c in enumerate(order, 1):
        w.writerow([i, c.id, c.valence, c.text])

thirds = [Counter(c.valence for c in order[i:i + 90]) for i in (0, 90, 180)]
print(f"Wrote {C.CUE_ORDER_FILE.name} (seed {C.CUE_ORDER_SEED})")
print(f"Longest run of one valence: {design.longest_valence_run(order)} (limit {C.MAX_SAME_VALENCE_RUN})")
print("Valences per third of the list:", [dict(t) for t in thirds])
