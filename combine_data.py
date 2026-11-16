"""Merge all Study 1 sessions into analysis-ready files (plain Python, no PsychoPy needed).

    python3 combine_data.py                 # main-experiment sessions only
    python3 combine_data.py --include-pilot # also pilot sessions

Writes to data/combined/:
  trials_all.csv       every main-task slide of every participant (long format)
  reports_all.csv      every thought report with its cue context and probe answers
  m_presses_all.csv    every M press: slide, second, hit / late hit / false alarm, delay, phrase on screen
  targets_all.csv      every vertical-line target: on time / late / missed, RT, delay, phrase on the slide
  participants.csv     one row per session: condition, demographics, target accuracy, report counts,
                       end-of-study answers, computer
  coding_BLIND_all.csv all reports for the blind coders, shuffled across participants
  Study1_data.xlsx     all of the above except the coding sheet, one Excel sheet each
Read them in R (read.csv), SPSS, jamovi, Excel or pandas (pd.read_csv).
"""
import csv
import json
import random
import sys
from collections import Counter

import config as C
from datafiles import (CODING_COLS, M_PRESS_COLS, REPORT_COLS, TARGET_COLS, TRIAL_COLS, export_xlsx,
                       target_rows, target_summary)
from questions import POST_COLS

include_pilot = "--include-pilot" in sys.argv
out_dir = C.DATA_DIR / "combined"
out_dir.mkdir(parents=True, exist_ok=True)


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, cols):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


trials, reports, coding, people, m_presses, all_targets = [], [], [], [], [], []
for meta_path in sorted(C.DATA_DIR.glob("*_session.json")):
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if meta.get("mode") == "pilot" and not include_pilot:
        continue
    base = meta_path.name[: -len("_session.json")]
    t_rows = [r for r in read_csv(C.DATA_DIR / f"{base}_trials.csv") if r["phase"] != "practice"]
    r_rows = [r for r in read_csv(C.DATA_DIR / f"{base}_reports.csv") if r["phase"] != "practice"]
    trials += t_rows
    reports += r_rows
    m_path = C.DATA_DIR / f"{base}_m_presses.csv"           # sessions from v2.2 on
    if m_path.exists():
        m_presses += [r for r in read_csv(m_path) if r["phase"] != "practice"]
    t_targets = target_rows(t_rows)
    all_targets += t_targets
    coding += read_csv(C.DATA_DIR / f"{base}_coding_BLIND.csv")

    targets = [r for r in t_rows if r["is_target"] == "1" and r["target_hit"] in ("0", "1")]  # scorable only
    hits = [r for r in targets if r["target_hit"] == "1"]
    rts = [float(r["target_rt_s"]) for r in hits if r["target_rt_s"]]
    demo = meta.get("demographics") or {}
    post = meta.get("post_questionnaire") or {}
    by_type = Counter(r["trial_type"] for r in r_rows)
    people.append({
        "participant_id": meta["participant_id"], "condition": meta["condition"], "mode": meta["mode"],
        "status": meta.get("status"), "started_at": meta.get("started_at"), "eligible": meta.get("eligible"),
        **{k: demo.get(k, "") for k in ("age", "gender", "native_language", "native_language_other",
                                        "education", "education_detail", "normal_vision")},
        "slides_run": len(t_rows), "targets_total": len(targets), "targets_hit": len(hits),
        "hit_rate": round(len(hits) / len(targets), 3) if targets else "",
        "mean_target_rt_s": round(sum(rts) / len(rts), 3) if rts else "",
        "false_alarms": sum(r["false_alarm"] == "1" for r in t_rows),
        "n_reports": len(r_rows), "n_reports_on_cue_slide": by_type["C"], "n_reports_on_cuefree_slide": by_type["N"],
        "n_reports_intentionality_le2": sum(r["q2_intentionality"] not in ("", None) and int(r["q2_intentionality"]) <= 2
                                            for r in r_rows),
        "n_reports_specificity_ge4": sum(r["q8_specificity"] not in ("", None) and int(r["q8_specificity"]) >= 4
                                         for r in r_rows),
        "n_reports_private": sum(r.get("q1_private") == "1" for r in r_rows),
        **target_summary(t_targets),
        **{k: post.get(k, "") for k in POST_COLS},
        "post_questionnaire_complete": meta.get("post_questionnaire_complete", ""),
        "dropped_frame_share": meta.get("dropped_frame_share", ""), "computer": meta.get("computer", ""),
        "psychopy_version": meta.get("psychopy_version", ""), "version": meta.get("version", ""),
        "frame_rate_hz": meta.get("frame_rate_hz"), "cue_list_fingerprint": meta.get("cue_list_fingerprint"),
        "experimenter": meta.get("experimenter"), "note": meta.get("note"), "base_name": base,
    })

random.Random(1).shuffle(coding)
write_csv(out_dir / "trials_all.csv", trials, TRIAL_COLS)
write_csv(out_dir / "reports_all.csv", reports, REPORT_COLS)
people_cols = list(people[0]) if people else ["participant_id"]
write_csv(out_dir / "participants.csv", people, people_cols)
write_csv(out_dir / "coding_BLIND_all.csv", coding, CODING_COLS)
write_csv(out_dir / "m_presses_all.csv", m_presses, M_PRESS_COLS)
write_csv(out_dir / "targets_all.csv", all_targets, TARGET_COLS)
xlsx_ok = export_xlsx(out_dir / "Study1_data.xlsx", {
    "participants": (people, people_cols), "reports": (reports, REPORT_COLS), "m_presses": (m_presses, M_PRESS_COLS),
    "targets": (all_targets, TARGET_COLS), "trials": (trials, TRIAL_COLS)})

fingerprints = {p["cue_list_fingerprint"] for p in people}
print(f"{len(people)} sessions, {len(trials)} slides, {len(reports)} reports, {len(m_presses)} M presses, "
      f"{len(all_targets)} targets -> {out_dir}")
if not xlsx_ok:
    print("(Study1_data.xlsx not written: openpyxl missing. Run this script from PsychoPy to get it.)")
print("Sessions per condition:", dict(Counter(p["condition"] for p in people)))
if len(fingerprints) > 1:
    print("WARNING: sessions used different versions of the cue lists:", fingerprints)
