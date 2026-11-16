"""Checks the trial sequences against the ethics form. Runs without PsychoPy:  python3 test_design.py"""
import config as C
import design

results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(("PASS " if ok else "FAIL ") + name + (f"  ({detail})" if detail else ""))


cues = design.load_cues()
check("270 cues loaded from the final list", len(cues) == 270, C.CUE_FILE.name)
check("NEG_51 is 'KYK borcu'", {c.id: c.text for c in cues}.get("NEG_51") == "KYK borcu")
check("final list (11 Nov 2026) loaded: NEG_40 'Sınavlara çalışmak', NEU_53 'Ütü', NEU_86 'Şahıs'",
      {c.id: c.text for c in cues}.get("NEG_40") == "Sınavlara çalışmak" and {c.id: c.text for c in cues}.get("NEU_53") == "Ütü"
      and {c.id: c.text for c in cues}.get("NEU_86") == "Şahıs")
check("fixed order file shows the current wording", all(row["text"] == {c.id: c.text for c in cues}[row["cue_id"]]
      for row in __import__("csv").DictReader(open(C.CUE_ORDER_FILE, encoding="utf-8-sig"))))
for v in C.VALENCES:
    check(f"90 {v} cues", sum(c.valence == v for c in cues) == 90)
dupes = design.duplicate_phrases(cues)
check("cue phrases unique (no phrase twice in the 270 list)", not dupes, ", ".join(dupes))
check("duplicates fixed as in 270Cue_Words/cue_words_final_270.xlsx: POS_54 'Hediye vermek', POS_77 'Tiyatroya gitmek'",
      {c.id: c.text for c in cues}.get("POS_54") == "Hediye vermek"
      and {c.id: c.text for c in cues}.get("POS_77") == "Tiyatroya gitmek")

targets = design.target_positions()
check("15 target positions", len(targets) == 15, ", ".join(map(str, targets)))
for lo, hi in C.TARGET_BLOCKS:
    check(f"5 targets in trials {lo}-{hi}", sum(lo <= t <= hi for t in targets) == 5)

order = design.shuffled_cues(cues, seed=12345)
seqs = {c: design.build_main_sequence(c, order) for c in ("A", "B")}
for c, s in seqs.items():
    cue_trials = [t.trial for t in s if t.type == "C"]
    check(f"{c}: 800 trials", len(s) == 800)
    check(f"{c}: 270 cue trials, each cue once", len(cue_trials) == 270 and len({t.cue.id for t in s if t.cue}) == 270)
    check(f"{c}: 15 targets", sum(t.is_target for t in s) == 15)
    check(f"{c}: block-1 targets fall on cue trials", all(t.type == "C" for t in s if t.is_target and t.trial <= 270))
    check(f"{c}: cue order identical to the shuffled list", [t.cue.id for t in s if t.cue] == [x.id for x in order])
cA = [t.trial for t in seqs["A"] if t.type == "C"]
cB = [t.trial for t in seqs["B"] if t.type == "C"]
check("A: cues on consecutive trials 1-270", cA == list(range(1, 271)))
check("B: cues on odd trials 1-539", cB == list(range(1, 540, 2)))
check("A and B: identical target positions",
      [t.trial for t in seqs["A"] if t.is_target] == [t.trial for t in seqs["B"] if t.is_target])

tpls = design.templates()
check("5 horizontal + 3 vertical templates",
      sorted(tpls) == [f"H{k}" for k in range(1, 6)] + [f"V{k}" for k in range(1, 4)]
      and [t.vertical for t in tpls.values()].count(True) == 3)
seqA = [t.template for t in seqs["A"]]
check("A and B: identical template on every slide", seqA == [t.template for t in seqs["B"]])
check("templates: same for every participant (other cue order)",
      [t.template for t in design.build_main_sequence("B", design.shuffled_cues(cues, seed=999))] == seqA)
check("target slides show a vertical template, all others a horizontal one",
      all(tpls[t.template].vertical == t.is_target for s in seqs.values() for t in s))
check("each vertical template used 5 times",
      all(seqA.count(f"V{k}") == 5 for k in range(1, 4)), str({f"V{k}": seqA.count(f"V{k}") for k in range(1, 4)}))
check("pattern never repeats on consecutive slides", all(a != b for a, b in zip(seqA, seqA[1:])))
check("all 5 horizontal templates used", all(f"H{k}" in seqA for k in range(1, 6)),
      str({f"H{k}": seqA.count(f"H{k}") for k in range(1, 6)}))
for tid, tpl in tpls.items():
    n = len(tpl.lines)
    navy = sum(ln.color == "navy" for ln in tpl.lines)
    print(f"INFO {tid}: {n} lines, {navy} navy / {n - navy} black")
check("line count per template within LINES_PER_SLIDE",
      all(C.LINES_PER_SLIDE[0] <= len(t.lines) <= C.LINES_PER_SLIDE[1] for t in tpls.values()))
check("navy lines per template within NAVY_PER_SLIDE, the rest black",
      all(C.NAVY_PER_SLIDE[0] <= sum(ln.color == "navy" for ln in t.lines) <= C.NAVY_PER_SLIDE[1]
          and all(ln.color in ("navy", "black") for ln in t.lines) for t in tpls.values()))
check("H templates all horizontal, V templates all vertical",
      all(t.vertical == tid.startswith("V") for tid, t in tpls.items()))

boxes = [design.line_box(t.vertical, ln) for t in tpls.values() for ln in t.lines]
longest = max(len(c.text) for c in cues)
half_text = 0.6 * C.CUE_TEXT_HEIGHT * longest / 2      # generous width estimate of the longest phrase
check("lines stay clear of the phrase area in the middle",
      all(b[1] < -C.CUE_ZONE[0] or b[0] > C.CUE_ZONE[0] or b[3] < -C.CUE_ZONE[1] or b[2] > C.CUE_ZONE[1]
          for b in boxes),
      f"free zone ±{C.CUE_ZONE[0]} x ±{C.CUE_ZONE[1]}, longest phrase ({longest} letters) half-width ~{half_text:.3f}")
check("free zone is larger than the longest phrase", half_text < C.CUE_ZONE[0] and C.CUE_TEXT_HEIGHT < C.CUE_ZONE[1])
check("lines stay on screen (4:3 or wider)",
      all(abs(b[0]) < 0.66 and abs(b[1]) < 0.66 and abs(b[2]) < 0.5 and abs(b[3]) < 0.5 for b in boxes))
gaps_ok = all(not (a[0] - C.MIN_GAP + 1e-9 < b[1] and b[0] < a[1] + C.MIN_GAP - 1e-9
                   and a[2] - C.MIN_GAP + 1e-9 < b[3] and b[2] < a[3] + C.MIN_GAP - 1e-9)
              for t in tpls.values()
              for i, a in enumerate([design.line_box(t.vertical, ln) for ln in t.lines])
              for b in [design.line_box(t.vertical, ln) for ln in t.lines][i + 1:])
check(f"no two lines of a template closer than MIN_GAP ({C.MIN_GAP})", gaps_ok)

assign = [design.assign_condition(str(i)) for i in range(1, 101)]
check("IDs alternate A-B-A-B (odd = A, even = B)", assign == ["A", "B"] * 50, " ".join(assign[:6]) + " ...")
check("leading zeros do not matter ('07' = 7 = A)", design.assign_condition("07") == "A")
check("non-numeric ID (pilot) needs manual condition", design.assign_condition("P01") is None)

fixed = design.load_fixed_order(cues)
check(f"fixed order: at most {C.MAX_SAME_VALENCE_RUN} of one valence in a row",
      design.longest_valence_run(fixed) <= C.MAX_SAME_VALENCE_RUN, f"longest run {design.longest_valence_run(fixed)}")
check("fixed order file: all 270 cues, each once", len(fixed) == 270 and len({c.id for c in fixed}) == 270,
      C.CUE_ORDER_FILE.name)
check("fixed order is the same every time it is loaded",
      [c.id for c in design.load_fixed_order(design.load_cues())] == [c.id for c in fixed])
pilot = design.build_pilot_sequences(fixed)
check("pilot A: 10 cue slides", [t.type for t in pilot["A"]] == ["C"] * 10)
check("pilot B: C-N alternation over 10 slides", [t.type for t in pilot["B"]] == ["C", "N"] * 5)
check("pilot: one target per condition, on a cue slide",
      all(sum(t.is_target for t in p) == 1 and all(t.type == "C" for t in p if t.is_target) for p in pilot.values()))

prA, prB = design.build_practice_sequence("A"), design.build_practice_sequence("B")
check("practice A: phrase on every slide (C-C-C), 20 different phrases",
      [t.type for t in prA] == ["C"] * C.PRACTICE_TRIALS and len({t.cue.text for t in prA}) == C.PRACTICE_TRIALS)
check("practice B: C-N-C-N, 10 different phrases", [t.type for t in prB] == ["C", "N"] * (C.PRACTICE_TRIALS // 2)
      and len({t.cue.text for t in prB if t.cue}) == C.PRACTICE_TRIALS // 2)
check("practice: same targets and line patterns in A and B",
      [t.is_target for t in prA] == [t.is_target for t in prB] and [t.template for t in prA] == [t.template for t in prB]
      and [t.trial for t in prA if t.is_target] == C.PRACTICE_TARGETS)
cue_words = {w.lower() for c in cues for w in c.text.split()}
check("practice phrases are not in the 270 list and share no word with it (except 'kapı' in 'Kapı zili')",
      all(p not in {c.text for c in cues} for p in C.PRACTICE_PHRASES)
      and [p for p in C.PRACTICE_PHRASES if set(p.lower().split()) & cue_words] == ["Kapı zili"])

import re
src = (C.HERE / "study1_vigilance.py").read_text(encoding="utf-8") + (C.HERE / "questions.py").read_text(encoding="utf-8")
screen_texts = [t for t in re.findall(r'"((?:[^"\\]|\\.)*)"', src) if re.search("[çğıöşüÇĞİÖŞÜ]", t)]
check("no semicolon in any Turkish text shown to participants", not any(";" in t for t in screen_texts),
      f"{len(screen_texts)} Turkish strings checked")

import questions as Q
check("'belirtmek istemiyorum' recognised in any spelling",
      all(Q.is_private(t) for t in ("Belirtmek istemiyorum", "BELİRTMEK İSTEMİYORUM", "belirtmek  istemiyorum.",
                                    "belirtmek istemiyorm".replace("istemiyorm", "istemiyorum"), "belirtmek istemiyorum!"))
      and not any(Q.is_private(t) for t in ("", None, "annemle tatil", "belirtmek")))
check("end-of-study questions: study purpose asked first, before any question about the words",
      Q.POST[0][1] == "post_study_purpose" and not any("kelime" in item[2].lower() for item in Q.POST[:2]))
check("end-of-study questions include boredom, word reading and word attention",
      {"post_boredom", "post_words_read", "post_words_attention", "post_words_recall"} <= set(Q.POST_COLS))

from datafiles import target_rows, target_summary
fake = [dict(participant_id="T", condition="A", mode="main", phase="main", trial=str(t), cue_id=f"C{t}" if t < 4 else "",
             cue_order=str(t) if t < 4 else "", cue_text=f"w{t}" if t < 4 else "", is_target=str(int(t in (2, 4, 5, 6))),
             target_hit={2: "1", 4: "1", 5: "0", 6: ""}.get(t, ""), late_hit={2: "0", 4: "1"}.get(t, ""),
             target_rt_s={2: "0.5", 4: "1.8"}.get(t, ""), duration_s="1.5", onset_s="", onset_task_s="",
             m_presses="", interrupted_by_report={6: "1"}.get(t, "0")) for t in range(1, 8)]
tr = target_rows(fake)
check("target table: on time / late / miss / not scorable, delay and last phrase",
      [r["outcome"] for r in tr] == ["on_time", "late", "miss", "not_scorable"]
      and tr[1]["late_by_s"] == 0.3 and tr[0]["late_by_s"] == 0
      and tr[1]["last_cue_order"] == "3" and tr[1]["slides_since_last_cue"] == 1 and tr[1]["block"] == 1,
      str([(r["outcome"], r["rt_s"], r["late_by_s"], r["last_cue_text"]) for r in tr]))
check("target summary counts", target_summary(tr) == {"targets_on_time": 1, "targets_late": 1, "targets_missed": 1,
                                                    "targets_not_scorable": 1, "mean_target_rt_s": 1.15})

print("\nFirst 12 slides  A:", " ".join(t.type + ("*" if t.is_target else "") for t in seqs["A"][:12]))
print("                 B:", " ".join(t.type + ("*" if t.is_target else "") for t in seqs["B"][:12]))
print(f"\n{sum(results)}/{len(results)} checks passed")
raise SystemExit(0 if all(results) else 1)
