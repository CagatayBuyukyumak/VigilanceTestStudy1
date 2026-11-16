"""After blind coding: join the coders' decisions back to the reports and classify every memory.

Workflow
  1. python3 combine_data.py                 -> data/combined/coding_BLIND_all.csv
  2. Coders fill the CODER_ columns (in Excel is fine; save as .xlsx or .csv):
       CODER_specific_memory_0_1             1 = specific personal memory, 0 = not
       CODER_matching_cue_1_to_6_or_0_none   which listed cue the memory matches (cue_1 = most recent), 0 = none
  3. python3 merge_coding.py FINAL.xlsx [SECOND_CODER.xlsx]
       FINAL        the resolved coding used for the analysis
       SECOND_CODER optional: an independent second coding; agreement (Cohen's kappa) is computed between
                    the two files and the disagreements are written out for discussion

Writes to data/combined/:
  reports_coded.csv        reports_all.csv + coder decisions + matched cue + memory_type + inclusion flags
  participants_coded.csv   participants.csv + counts of immediate / subsequent / no-match memories
  Study1_coded.xlsx        both, as Excel sheets
  coding_disagreements.csv only with a second coder

memory_type (for reports the coder matched to a cue):
  immediate   the matched cue is the one on screen when SPACE was pressed
  subsequent  the matched cue was shown on an earlier slide
  no_match    coder found no matching cue
Lag columns give the distance from the matched cue to the report in cues, slides and seconds; the
seconds are on the task clock, which stops while the questions are on screen.
"""
import csv
import sys
from collections import Counter

import config as C
from datafiles import CODING_CUES, PREV_N, export_xlsx

# Inclusion rules from the proposal ("specific personal memories reported as unintentional").
# Decide the cut-offs with your supervisor before looking at the results.
INTENTIONALITY_MAX = 2     # q2 1-5 (1 = definitely no): 1-2 counts as unintentional
USE_CODER_SPECIFICITY = True   # True: coder's 0/1 decides "specific"; False: participant q8 >= 4

MATCH_COL = "CODER_matching_cue_1_to_6_or_0_none"
SPEC_COL = "CODER_specific_memory_0_1"
COMBINED = C.DATA_DIR / "combined"


def read_table(path):
    path = str(path)
    if path.lower().endswith(".xlsx"):
        import openpyxl
        ws = openpyxl.load_workbook(path, data_only=True).active
        rows = list(ws.iter_rows(values_only=True))
        head = [str(h) if h is not None else "" for h in rows[0]]
        return [{h: ("" if v is None else str(v).strip()) for h, v in zip(head, r)} for r in rows[1:]
                if any(v not in (None, "") for v in r)]
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [{k: (v or "").strip() for k, v in r.items()} for r in csv.DictReader(f)]


def write_csv(path, rows, cols):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def as_int(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def cohen_kappa(a, b):
    n = len(a)
    if n == 0:
        return None
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


if len(sys.argv) < 2:
    raise SystemExit(__doc__)
final = {r["report_code"]: r for r in read_table(sys.argv[1])}
reports = read_table(COMBINED / "reports_all.csv")
trials = read_table(COMBINED / "trials_all.csv")
people = read_table(COMBINED / "participants.csv")

# Cue onsets on the task clock, to compute the lag in seconds.
cue_onset = {(t["participant_id"], t["phase"], t["trial"]): t["onset_task_s"] for t in trials if t["cue_id"]}

missing = [r["report_code"] for r in reports if r["report_code"] not in final]
if missing:
    print(f"WARNING: {len(missing)} reports have no coding yet (e.g. {missing[:3]}); they stay uncoded.")

out = []
for r in reports:
    c = final.get(r["report_code"], {})
    row = dict(r)
    match = as_int(c.get(MATCH_COL))
    spec = as_int(c.get(SPEC_COL))
    row["coder_specific"] = "" if spec is None else spec
    row["coder_match_rank"] = "" if match is None else match
    # The coder's cue list = cue on screen (if any) followed by the earlier cues, most recent first.
    recent = []
    if r["cue_on_screen_id"]:
        recent.append((r["trial"], r["cue_on_screen_id"], r["cue_on_screen_text"], r["cue_on_screen_valence"]))
    for k in range(1, PREV_N + 1):
        if r.get(f"prev{k}_cue_id"):
            recent.append((r[f"prev{k}_cue_trial"], r[f"prev{k}_cue_id"], r[f"prev{k}_cue_text"],
                           r[f"prev{k}_cue_valence"]))
    recent = recent[:CODING_CUES]

    row.update({"matched_cue_trial": "", "matched_cue_id": "", "matched_cue_text": "", "matched_cue_valence": "",
                "lag_cues": "", "lag_slides": "", "lag_s": "", "memory_type": ""})
    if match is None:
        row["memory_type"] = "uncoded"
    elif match == 0:
        row["memory_type"] = "no_match"
    elif 1 <= match <= len(recent):
        trial, cid, text, val = recent[match - 1]
        onset = cue_onset.get((r["participant_id"], r["phase"], trial))
        on_screen = bool(r["cue_on_screen_id"]) and match == 1
        row.update({
            "matched_cue_trial": trial, "matched_cue_id": cid, "matched_cue_text": text, "matched_cue_valence": val,
            "lag_cues": match - 1,          # how many cues appeared after the matched one (0 = most recent)
            "lag_slides": int(r["trial"]) - int(trial),
            "lag_s": round(float(r["task_time_active_s"]) - float(onset), 3) if onset not in (None, "") else "",
            "memory_type": "immediate" if on_screen else "subsequent",
        })
    else:
        row["memory_type"] = "invalid_code"
        print(f"WARNING: report {r['report_code']}: match code {match} but only {len(recent)} cues were listed")

    q2, q8 = as_int(r["q2_intentionality"]), as_int(r["q8_specificity"])
    row["unintentional"] = "" if q2 is None else int(q2 <= INTENTIONALITY_MAX)
    specific = spec if USE_CODER_SPECIFICITY else (None if q8 is None else int(q8 >= 4))
    row["specific"] = "" if specific is None else specific
    row["include_main_analysis"] = int(row["unintentional"] == 1 and row["specific"] == 1
                                       and row["memory_type"] in ("immediate", "subsequent"))
    out.append(row)

extra = ["report_code", "coder_specific", "coder_match_rank", "matched_cue_trial", "matched_cue_id",
         "matched_cue_text", "matched_cue_valence", "lag_cues", "lag_slides", "lag_s", "memory_type",
         "unintentional", "specific", "include_main_analysis"]
cols = list(reports[0]) + [c for c in extra if c not in reports[0]] if reports else extra
write_csv(COMBINED / "reports_coded.csv", out, cols)

# Per participant counts, among memories included in the main analysis.
for p in people:
    mine = [r for r in out if r["participant_id"] == p["participant_id"] and r["include_main_analysis"] == 1]
    n_imm = sum(r["memory_type"] == "immediate" for r in mine)
    n_sub = sum(r["memory_type"] == "subsequent" for r in mine)
    p.update({"n_included": len(mine), "n_immediate": n_imm, "n_subsequent": n_sub,
              "prop_subsequent": round(n_sub / len(mine), 3) if mine else ""})
p_cols = list(people[0]) if people else []
write_csv(COMBINED / "participants_coded.csv", people, p_cols)
export_xlsx(COMBINED / "Study1_coded.xlsx", {"participants": (people, p_cols), "reports": (out, cols)})

print(f"{len(out)} reports: " + ", ".join(f"{k} {v}" for k, v in Counter(r["memory_type"] for r in out).items()))
print(f"Included in main analysis: {sum(r['include_main_analysis'] for r in out)}")

if len(sys.argv) > 2:
    second = {r["report_code"]: r for r in read_table(sys.argv[2])}
    both = [k for k in final if k in second]
    dis = []
    for col in (MATCH_COL, SPEC_COL):
        a = [final[k].get(col, "") for k in both]
        b = [second[k].get(col, "") for k in both]
        agree = sum(x == y for x, y in zip(a, b))
        kappa = cohen_kappa(a, b)
        print(f"{col}: {agree}/{len(both)} agree ({agree / len(both):.0%}), Cohen's kappa = "
              f"{'n/a' if kappa is None else round(kappa, 3)}")
        dis += [{"report_code": k, "column": col, "file_1": x, "file_2": y,
                 "description": final[k].get("description", "")} for k, x, y in zip(both, a, b) if x != y]
    write_csv(COMBINED / "coding_disagreements.csv", dis, ["report_code", "column", "file_1", "file_2", "description"])
    print(f"{len(dis)} disagreements written to coding_disagreements.csv")
