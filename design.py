"""Trial sequences, cue loading and condition assignment for Study 1.

Pure Python (no PsychoPy), so it can be checked with test_design.py on any computer.
"""
import csv
import hashlib
import random
from dataclasses import dataclass
from typing import List, Optional

import config as C


@dataclass
class Cue:
    id: str          # e.g. POS_07, NEU_15, NEG_90 (as in stimuli/cue_words_final_270.xlsx)
    valence: str     # positive / neutral / negative / practice
    text: str


@dataclass
class Trial:
    trial: int                   # 1-based position within the block
    type: str                    # "C" = cue phrase + lines, "N" = lines only
    is_target: bool              # vertical-line template instead of a horizontal one
    cue: Optional[Cue] = None
    cue_order: Optional[int] = None   # 1..270: which cue of the participant's sequence this is
    template: str = ""                # line pattern shown on this slide: H1-H5 or V1-V3


@dataclass
class PatternLine:
    x: float
    y: float
    length: float
    color: str                   # a key of C.LINE_COLORS_RGB255


@dataclass
class Template:
    id: str                      # H1..H5 (horizontal lines) or V1..V3 (vertical lines, targets)
    vertical: bool
    lines: List[PatternLine]


def load_cues() -> List[Cue]:
    with open(C.CUE_FILE, encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f, delimiter="\t") if (r.get("cue_id") or "").strip()]
    cues = [Cue(r["cue_id"].strip(), r["valence"].strip(), r["word"].strip()) for r in rows]
    if len(cues) != C.N_CUES:
        raise ValueError(f"{C.CUE_FILE.name}: expected {C.N_CUES} phrases, found {len(cues)}")
    if len({c.id for c in cues}) != len(cues):
        raise ValueError(f"{C.CUE_FILE.name}: cue_id values are not unique")
    for v in C.VALENCES:
        n = sum(c.valence == v for c in cues)
        if n != C.CUES_PER_VALENCE:
            raise ValueError(f"{C.CUE_FILE.name}: expected {C.CUES_PER_VALENCE} {v} phrases, found {n}")
    return cues


def cue_list_fingerprint(cues: List[Cue]) -> str:
    """Short hash of the cue lists, saved with every session so list versions can be told apart."""
    joined = "\n".join(f"{c.id}\t{c.text}" for c in cues)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:12]


def duplicate_phrases(cues: List[Cue]) -> List[str]:
    seen, dupes = set(), []
    for c in cues:
        if c.text in seen and c.text not in dupes:
            dupes.append(c.text)
        seen.add(c.text)
    return dupes


def assign_condition(participant_id: str) -> Optional[str]:
    """Alternating assignment for numeric IDs (odd -> A, even -> B); None for non-numeric IDs."""
    pid = str(participant_id).strip()
    if not pid.isdigit() or int(pid) < 1:
        return None
    return "A" if int(pid) % 2 == 1 else "B"


def target_positions() -> List[int]:
    """Centres of TARGETS_PER_BLOCK equal segments in each block (identical for A and B)."""
    out = []
    for start, end in C.TARGET_BLOCKS:
        step = (end - start + 1) / C.TARGETS_PER_BLOCK
        out += [start - 1 + int(step * (k + 0.5) + 0.5) for k in range(C.TARGETS_PER_BLOCK)]
    return out


_TEMPLATES = None


def line_box(vertical: bool, ln: PatternLine, pad: float = 0.0) -> tuple:
    """(left, right, bottom, top) of a line, widened by pad on every side."""
    w, h = (C.PATTERN_LINE_WIDTH, ln.length) if vertical else (ln.length, C.PATTERN_LINE_WIDTH)
    return ln.x - w / 2 - pad, ln.x + w / 2 + pad, ln.y - h / 2 - pad, ln.y + h / 2 + pad


def _boxes_meet(a, b) -> bool:
    return a[0] < b[1] and b[0] < a[1] and a[2] < b[3] and b[2] < a[3]


def templates() -> dict:
    """The 5 horizontal and 3 vertical line patterns, {id: Template}. Built once from TEMPLATE_SEED.
    Each template scatters a random number of lines (LINES_PER_SLIDE) over the screen, at least
    MIN_GAP apart and clear of the phrase box; NAVY_PER_SLIDE of them are navy, the rest black."""
    global _TEMPLATES
    if _TEMPLATES is None:
        rng = random.Random(C.TEMPLATE_SEED)
        cue_zone = (-C.CUE_ZONE[0], C.CUE_ZONE[0], -C.CUE_ZONE[1], C.CUE_ZONE[1])
        out = {}
        for vertical, count, prefix in ((False, C.N_H_TEMPLATES, "H"), (True, C.N_V_TEMPLATES, "V")):
            for k in range(1, count + 1):
                n = rng.randint(*C.LINES_PER_SLIDE)
                lines, boxes = [], []
                while len(lines) < n:
                    ln = PatternLine(round(rng.uniform(*C.FIELD_X), 4), round(rng.uniform(*C.FIELD_Y), 4),
                                     round(rng.uniform(*C.PATTERN_LINE_LENGTH), 4), "black")
                    box = line_box(vertical, ln)
                    if (box[0] < C.FIELD_X[0] or box[1] > C.FIELD_X[1] or box[2] < C.FIELD_Y[0]
                            or box[3] > C.FIELD_Y[1] or _boxes_meet(line_box(vertical, ln, C.MIN_GAP), cue_zone)
                            or any(_boxes_meet(line_box(vertical, ln, C.MIN_GAP), b) for b in boxes)):
                        continue
                    lines.append(ln)
                    boxes.append(box)
                for ln in rng.sample(lines, rng.randint(*C.NAVY_PER_SLIDE)):
                    ln.color = "navy"
                out[f"{prefix}{k}"] = Template(f"{prefix}{k}", vertical, lines)
        _TEMPLATES = out
    return _TEMPLATES


def template_sequence(is_target: List[bool], seed: int = C.TEMPLATE_ORDER_SEED) -> List[str]:
    """Template id for every slide. Ordinary slides get a horizontal template different from the
    previous slide's; target slides get the vertical templates, each used equally often.
    Depends only on the target positions and the seed, so A and B get the same sequence."""
    rng = random.Random(seed)
    h_ids = [f"H{k}" for k in range(1, C.N_H_TEMPLATES + 1)]
    v_ids = [f"V{k % C.N_V_TEMPLATES + 1}" for k in range(sum(is_target))]
    rng.shuffle(v_ids)
    v_iter = iter(v_ids)
    out, prev = [], None
    for target in is_target:
        tid = next(v_iter) if target else rng.choice([h for h in h_ids if h != prev])
        out.append(tid)
        prev = tid
    return out


def _apply_templates(trials: List[Trial], seed: int = C.TEMPLATE_ORDER_SEED) -> List[Trial]:
    for tr, tid in zip(trials, template_sequence([t.is_target for t in trials], seed)):
        tr.template = tid
    return trials


def load_fixed_order(cues: List[Cue]) -> List[Cue]:
    """The fixed presentation order from CUE_ORDER_FILE, matched to the current lists by cue id.
    If a phrase's wording was edited in the .txt files after the order was made, the new wording is
    used in the same position."""
    if not C.CUE_ORDER_FILE.exists():
        raise FileNotFoundError(f"{C.CUE_ORDER_FILE.name} not found: run make_cue_order.py once first.")
    by_id = {c.id: c for c in cues}
    with open(C.CUE_ORDER_FILE, encoding="utf-8-sig", newline="") as f:
        ids = [row["cue_id"] for row in csv.DictReader(f)]
    if sorted(ids) != sorted(by_id):
        raise ValueError(f"{C.CUE_ORDER_FILE.name} does not contain exactly the 270 current cue ids.")
    return [by_id[i] for i in ids]


def longest_valence_run(order: List[Cue]) -> int:
    longest = run = 1
    for a, b in zip(order, order[1:]):
        run = run + 1 if a.valence == b.valence else 1
        longest = max(longest, run)
    return longest


def constrained_order(cues: List[Cue], seed: int, max_run: int = C.MAX_SAME_VALENCE_RUN) -> List[Cue]:
    """Random order in which no valence appears more than max_run times in a row.
    Each step picks a valence (weighted by how many of it are left, so the three run out together),
    then a random phrase of that valence. Restarts in the rare case it paints itself into a corner."""
    rng = random.Random(seed)
    while True:
        pools = {v: [c for c in cues if c.valence == v] for v in C.VALENCES}
        for p in pools.values():
            rng.shuffle(p)
        order, run_v, run_n = [], None, 0
        while any(pools.values()):
            allowed = [v for v, p in pools.items() if p and not (v == run_v and run_n >= max_run)]
            if not allowed:
                break
            v = rng.choices(allowed, weights=[len(pools[a]) for a in allowed])[0]
            order.append(pools[v].pop())
            run_n = run_n + 1 if v == run_v else 1
            run_v = v
        if len(order) == len(cues):
            return order


def shuffled_cues(cues: List[Cue], seed: int) -> List[Cue]:
    order = list(cues)
    random.Random(seed).shuffle(order)
    return order


def build_main_sequence(condition: str, cue_order: List[Cue]) -> List[Trial]:
    gap = C.CONDITIONS[condition]["cue_gap"]
    targets = set(target_positions())
    trials = [Trial(t, "N", t in targets) for t in range(1, C.TOTAL_TRIALS + 1)]
    for i, cue in enumerate(cue_order):
        tr = trials[i * (gap + 1)]
        tr.type, tr.cue, tr.cue_order = "C", cue, i + 1
    return _apply_templates(trials)


def build_practice_sequence(condition: str) -> List[Trial]:
    """Practice in the participant's own rhythm: A = phrase on every slide (C-C-C),
    B = phrase on every other slide (C-N-C-N). Each practice phrase appears once."""
    gap = C.CONDITIONS[condition]["cue_gap"]
    phrases = iter(C.PRACTICE_PHRASES)
    trials, k = [], 0
    for t in range(1, C.PRACTICE_TRIALS + 1):
        cue = None
        if (t - 1) % (gap + 1) == 0:
            k += 1
            cue = Cue(f"PRAC{k:02d}", "practice", next(phrases))
        trials.append(Trial(t, "C" if cue else "N", t in C.PRACTICE_TARGETS, cue, k if cue else None))
    return _apply_templates(trials)


def build_pilot_sequences(order: List[Cue]):
    """Short versions of both conditions: A shows phrases 1-10 of the fixed order, B the next ones."""
    n = C.PILOT_TRIALS_PER_CONDITION
    out = {}
    used = 0
    for cond in ("A", "B"):
        gap = C.CONDITIONS[cond]["cue_gap"]
        trials = [Trial(t, "N", t in C.PILOT_TARGETS) for t in range(1, n + 1)]
        k = 0
        for idx in range(0, n, gap + 1):
            trials[idx].type, trials[idx].cue, trials[idx].cue_order = "C", order[used], k + 1
            used += 1
            k += 1
        out[cond] = _apply_templates(trials)
    return out
