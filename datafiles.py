"""Writes Study 1 data files. Pure Python (no PsychoPy).

Per session (in data/):
  <base>.xlsx              the participant's own Excel file: summary, SPACE presses, M presses, targets,
                           slides, end-of-study answers, column guide
  <base>_trials.csv        one row per slide (practice/pilot and main)
  <base>_reports.csv       one row per SPACE press: timing, cue context + the 8 probe answers
  <base>_m_presses.csv     one row per M press: when, on which slide/phrase, hit / late hit / false alarm
  <base>_coding_BLIND.csv  sheet for blind coders: no condition, no timing, 6 most recent cues
  <base>_session.json      settings, seeds, cue order, demographics, end-of-study answers, computer, summary
and one row per session appended to data/all_sessions.csv. With config.BACKUP_DIR set, all of these
are copied there when the session ends.

Rows are written and flushed as they happen, so a crash loses at most the current slide (or the
thought report whose questions are on screen).
CSV files are UTF-8 with BOM (Excel shows Turkish characters) and comma-separated.
"""
import csv
import json
import secrets
import shutil
from datetime import datetime
from pathlib import Path

import config as C
from questions import POST, POST_COLS, POST_TEXT_COLS

PREV_N = 6          # previous cues listed in each report row (>= CODING_CUES, so every coded match maps back)
CODING_CUES = 6     # cues listed on the blind coding sheet (most recent first)

TRIAL_COLS = [
    "participant_id", "condition", "mode", "phase", "trial", "trial_type", "is_target",
    "cue_order", "cue_id", "cue_text", "cue_valence", "template",
    "onset_s", "onset_task_s", "duration_s", "interrupted_by_report", "report_id",
    "m_presses", "m_rt_s", "target_hit", "target_rt_s", "late_hit", "false_alarm",
]

REPORT_COLS = [
    "participant_id", "condition", "mode", "phase", "report_id", "report_index", "report_code",
    "trial", "trial_type", "trial_is_target", "task_time_s", "task_time_active_s", "time_into_trial_s",
    "cue_on_screen_id", "cue_on_screen_text", "cue_on_screen_valence",
    "last_cue_trial", "last_cue_id", "last_cue_text", "last_cue_valence",
    "trials_since_last_cue", "s_since_last_cue_onset", "cues_shown_so_far",
]
for _k in range(1, PREV_N + 1):
    REPORT_COLS += [f"prev{_k}_cue_trial", f"prev{_k}_cue_id", f"prev{_k}_cue_text", f"prev{_k}_cue_valence"]
REPORT_COLS += [
    "q1_description", "q1_private", "q2_intentionality", "q3_effort", "q4_trigger", "q5_relatedness",
    "q6_expectancy", "q7_vividness", "q8_specificity", "n_unanswered", "probe_duration_s",
]

# One row per M press. outcome: hit (on the target slide), late_hit (on the slide after it, within
# LATE_HIT_WINDOW_S), repeat (another press on a target already hit), false_alarm (no target).
M_PRESS_COLS = [
    "participant_id", "condition", "mode", "phase", "press_index", "trial", "trial_type",
    "time_into_trial_s", "task_time_s", "task_time_active_s", "outcome",
    "target_number", "target_trial", "rt_from_target_onset_s", "late_by_s",
    "cue_on_screen_order", "cue_on_screen_text", "last_cue_order", "last_cue_text", "trials_since_last_cue",
    "target_cue_order", "target_cue_text",
]

# One row per vertical-line target, made from the trials at the end of the session (target_rows()).
TARGET_COLS = [
    "participant_id", "condition", "mode", "phase", "target_number", "trial", "block", "template",
    "cue_on_slide_order", "cue_on_slide_text", "last_cue_order", "last_cue_text", "slides_since_last_cue",
    "outcome", "hit", "rt_s", "late_by_s", "slide_duration_s", "onset_s", "onset_task_s",
    "m_presses_on_slide", "interrupted_by_report",
]

CODING_COLS = (["report_code", "description", "private", "perceived_trigger", "cue_1_most_recent"]
               + [f"cue_{i}" for i in range(2, CODING_CUES + 1)]
               + ["CODER_specific_memory_0_1", "CODER_matching_cue_1_to_6_or_0_none", "CODER_notes"])

# Turkish guide to the columns, written as the last sheet of every participant's Excel file.
COLUMN_HELP = [
    ("ozet", "targets_on_time / targets_late / targets_missed", "Zamanında yakalanan, geç yakalanan ve "
     "kaçırılan dikey çizgi sayısı (ana görev)"),
    ("ozet", "mean_target_rt_s", "Yakalanan hedeflerde dikey çizginin çıkışından M basışına ortalama saniye"),
    ("ozet", "dropped_frame_share", "Slaytlar ekrandayken geç çizilen kare oranı (0.01'in üstü: bilgisayar yavaş)"),
    ("ozet", "post_...", "Deney sonu soruları (yanıtlar ve metinleri 'son_sorular' sayfasında)"),
    ("basislar", "report_index", "Kaçıncı BOŞLUK basışı (1, 2, 3 ...)"),
    ("basislar", "trial", "Basışın yapıldığı slayt (1-800)"),
    ("basislar", "trial_type", "C = slaytta ifade vardı, N = sadece çizgiler"),
    ("basislar", "time_into_trial_s", "Slayt (ve üzerindeki ifade) ekrana geldikten kaç saniye sonra basıldı (0-1.5)"),
    ("basislar", "cue_on_screen_text", "Basış anında ekranda olan ifade (boşsa ekranda ifade yoktu)"),
    ("basislar", "last_cue_text", "Basıştan önce görülen en son ifade (ekrandaki dahil)"),
    ("basislar", "trials_since_last_cue", "En son ifadeden bu yana kaç slayt geçti (0 = ifade hâlâ ekranda)"),
    ("basislar", "s_since_last_cue_onset", "En son ifadenin ekrana geldiği andan basışa kadar geçen saniye "
     "(önceki basışların soru ekranlarında geçen süre sayılmaz)"),
    ("basislar", "task_time_s", "Görevin başından basışa kadar geçen saniye (soru ekranları dahil)"),
    ("basislar", "task_time_active_s", "Aynısı, soru ekranlarında geçen süre hariç"),
    ("basislar", "prev1_cue_text ... prev6_cue_text", "Ondan önceki 6 ifade (1 = en yakın)"),
    ("basislar", "q1_description ... q8_specificity", "Basıştan hemen sonra sorulan 8 sorunun yanıtları"),
    ("basislar", "q1_private", "1 = katılımcı anı için 'Belirtmek istemiyorum' yazdı"),
    ("basislar", "probe_duration_s", "Bu basışın sorularını yanıtlamak için harcanan saniye"),
    ("m_basislari", "press_index", "Kaçıncı M basışı (alıştırma ve ana görev ayrı sayılır)"),
    ("m_basislari", "trial / time_into_trial_s", "Basışın yapıldığı slayt ve o slayt açıldıktan kaç saniye sonra"),
    ("m_basislari", "task_time_s", "Görevin başından itibaren kaçıncı saniyede basıldı"),
    ("m_basislari", "outcome", "hit = dikey çizgi ekrandayken; late_hit = çizgiden sonraki slaytta (geç); "
     "repeat = aynı hedefe ikinci basış; false_alarm = dikey çizgi yokken"),
    ("m_basislari", "target_number / target_trial", "Basışın ait olduğu hedef (1-15) ve hedefin slaytı"),
    ("m_basislari", "rt_from_target_onset_s", "Dikey çizgi ekrana geldikten kaç saniye sonra basıldı"),
    ("m_basislari", "late_by_s", "Geç basışta, dikey çizgi ekrandan kalktıktan kaç saniye sonra basıldı (zamanında: 0)"),
    ("m_basislari", "cue_on_screen_text / last_cue_order", "Basış anında ekrandaki ifade; en son görülen ifadenin "
     "sırası (kaçıncı kelime, 1-270) ve metni"),
    ("m_basislari", "target_cue_order / target_cue_text", "Hedef slaytında ekrandaki ifade (sırası ve metni)"),
    ("hedefler", "target_number / trial / block", "Hedef no (1-15), slaytı ve bloğu (1: 1-270, 2: 271-540, 3: 541-800)"),
    ("hedefler", "outcome", "on_time = zamanında; late = geç (sonraki slaytta); miss = kaçırıldı; "
     "not_scorable = M'ye basılmadan BOŞLUK ile kesildi"),
    ("hedefler", "rt_s / late_by_s", "Dikey çizginin çıkışından M basışına saniye; geçse çizgi kalktıktan sonraki saniye"),
    ("hedefler", "cue_on_slide_text / last_cue_order", "Hedef slaytındaki ifade; en son görülen ifadenin sırası ve metni"),
    ("slaytlar", "template", "Çizgi deseni: H1-H5 yatay, V1-V3 dikey (hedef)"),
    ("slaytlar", "onset_s", "Slaytın görevin başından itibaren ekrana geldiği saniye"),
    ("slaytlar", "interrupted_by_report / report_id", "Bu slaytta BOŞLUK'a basıldı (1) ve basışın kimliği"),
    ("slaytlar", "duration_s", "Slaytın ekranda kaldığı süre (BOŞLUK'a basıldıysa basış anına kadar)"),
    ("slaytlar", "target_hit / target_rt_s", "Dikey çizgi yakalandı mı (1/0) ve M'ye kaç saniyede basıldı"),
    ("slaytlar", "false_alarm", "Dikey çizgi yokken M'ye basıldı (1)"),
]

SESSION_LOG_COLS = [
    "participant_id", "condition", "mode", "status", "started_at", "finished_at", "experimenter",
    "age", "gender", "native_language", "education", "normal_vision", "eligible",
    "main_trials_run", "targets_hit", "targets_total", "false_alarms", "reports", "base_name", "note",
]

SUMMARY_COLS = (
    [c for c in SESSION_LOG_COLS if c != "base_name"]
    + ["targets_on_time", "targets_late", "targets_missed", "targets_not_scorable", "mean_target_rt_s",
       "m_presses_total", "reports_private", "post_questionnaire_complete"]
    + POST_COLS
    + ["condition_label", "frame_rate_hz", "dropped_frame_share", "screen_size_px", "psychopy_version",
       "computer", "version"]
)


def _open_csv(path, cols):
    f = open(path, "w", newline="", encoding="utf-8-sig")
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    f.flush()
    return f, w


def _round(v, nd=4):
    return round(v, nd) if isinstance(v, float) else v


def _num(v):
    try:
        return None if v in ("", None) else float(v)
    except (TypeError, ValueError):
        return None


def target_rows(trials):
    """One row per vertical-line target, from slide rows (dicts from the session, or read back from a
    _trials.csv, where every value is text)."""
    out, last, phase, k = [], None, None, 0
    for r in trials:
        if r["phase"] != phase:
            phase, last, k = r["phase"], None, 0
        if r.get("cue_id"):
            last = r
        if str(r.get("is_target")) != "1":
            continue
        k += 1
        trial = int(r["trial"])
        hit, late = str(r.get("target_hit")), str(r.get("late_hit"))
        rt, dur = _num(r.get("target_rt_s")), _num(r.get("duration_s"))
        if hit == "1":
            outcome = "late" if late == "1" else "on_time"
        else:
            outcome = "miss" if hit == "0" else "not_scorable"
        late_by = {"on_time": 0, "late": round(rt - dur, 4) if rt is not None and dur is not None else ""}
        block = next((n for n, (lo, hi) in enumerate(C.TARGET_BLOCKS, 1) if lo <= trial <= hi), "") \
            if phase == "main" else ""
        out.append({
            "participant_id": r["participant_id"], "condition": r["condition"], "mode": r["mode"],
            "phase": phase, "target_number": k, "trial": trial, "block": block, "template": r.get("template", ""),
            "cue_on_slide_order": r.get("cue_order", ""), "cue_on_slide_text": r.get("cue_text", ""),
            "last_cue_order": last.get("cue_order", "") if last else "",
            "last_cue_text": last.get("cue_text", "") if last else "",
            "slides_since_last_cue": trial - int(last["trial"]) if last else "",
            "outcome": outcome, "hit": {"on_time": 1, "late": 1, "miss": 0}.get(outcome, ""),
            "rt_s": "" if rt is None else rt, "late_by_s": late_by.get(outcome, ""),
            "slide_duration_s": "" if dur is None else dur,
            "onset_s": r.get("onset_s", ""), "onset_task_s": r.get("onset_task_s", ""),
            "m_presses_on_slide": r.get("m_presses", ""), "interrupted_by_report": r.get("interrupted_by_report", ""),
        })
    return out


def target_summary(targets):
    """Counts and mean RT over scored targets (main task, or both pilot blocks)."""
    t = [r for r in targets if r["phase"] in ("main", "pilot_A", "pilot_B")]
    count = lambda o: sum(r["outcome"] == o for r in t)
    rts = [float(r["rt_s"]) for r in t if r["outcome"] in ("on_time", "late") and r["rt_s"] != ""]
    return {"targets_on_time": count("on_time"), "targets_late": count("late"), "targets_missed": count("miss"),
            "targets_not_scorable": count("not_scorable"),
            "mean_target_rt_s": round(sum(rts) / len(rts), 4) if rts else ""}


class SessionWriter:
    def __init__(self, meta):
        """meta: dict with participant_id, condition, mode, experimenter, note, ... (saved to JSON)."""
        C.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.meta = dict(meta)
        self.meta.setdefault("started_at", datetime.now().isoformat(timespec="seconds"))
        stamp = self.meta["started_at"].replace(":", "-").replace("T", "_")
        prefix = "PILOT_" if self.meta.get("mode") == "pilot" else ""
        self.base = f"{prefix}S1_{self.meta['participant_id']}_{self.meta['condition']}_{stamp}"
        self.meta["base_name"] = self.base
        self.paths = {k: C.DATA_DIR / f"{self.base}_{k}" for k in
                      ("trials.csv", "reports.csv", "m_presses.csv", "coding_BLIND.csv", "session.json")}
        self._tf, self._tw = _open_csv(self.paths["trials.csv"], TRIAL_COLS)
        self._rf, self._rw = _open_csv(self.paths["reports.csv"], REPORT_COLS)
        self._mf, self._mw = _open_csv(self.paths["m_presses.csv"], M_PRESS_COLS)
        self.trials, self.reports, self.m_presses = [], [], []
        self.save_json()

    # ---- incremental writes -------------------------------------------------------------
    def write_trial(self, row):
        row = {k: _round(v) for k, v in row.items()}
        self.trials.append(row)
        self._tw.writerow(row)
        self._tf.flush()

    def write_report(self, row):
        row = {k: _round(v) for k, v in row.items()}
        self.reports.append(row)
        self._rw.writerow(row)
        self._rf.flush()
        self.save_json()

    def write_m_press(self, row):
        row = {k: _round(v) for k, v in row.items()}
        self.m_presses.append(row)
        self._mw.writerow(row)
        self._mf.flush()

    def new_report_code(self):
        return secrets.token_hex(4).upper()

    def save_json(self):
        with open(self.paths["session.json"], "w", encoding="utf-8") as f:
            json.dump(self.meta, f, ensure_ascii=False, indent=1, default=str)

    # ---- end of session -------------------------------------------------------------------
    def close(self, status):
        for f in (self._tf, self._rf, self._mf):
            f.close()
        self.meta["status"] = status
        self.meta["finished_at"] = datetime.now().isoformat(timespec="seconds")
        scored = [t for t in self.trials if t["phase"] in ("main", "pilot_A", "pilot_B")]
        # Targets cut short by a thought report before an M press have target_hit "" and are not scored.
        targets = [t for t in scored if t["is_target"] and t["target_hit"] in (0, 1)]
        self.targets = target_rows(self.trials)
        self.meta["summary"] = {
            "main_trials_run": len(scored),
            "targets_hit": sum(1 for t in targets if t["target_hit"] == 1),
            "targets_total": len(targets),
            "false_alarms": sum(1 for t in scored if t["false_alarm"] == 1),
            "reports": sum(1 for r in self.reports if r["phase"] != "practice"),
            "reports_private": sum(1 for r in self.reports if r["phase"] != "practice" and r.get("q1_private") == 1),
            "m_presses_total": sum(1 for m in self.m_presses if m["phase"] != "practice"),
            **target_summary(self.targets),
        }
        self._write_coding_sheet()
        self.save_json()
        self._append_session_log()
        try:
            self.meta["xlsx_written"] = self._write_participant_xlsx()
        except OSError as e:          # e.g. a file of the same name open in Excel on Windows
            self.meta["xlsx_written"] = f"FAILED: {e}"
        self.save_json()
        self.meta["backup"] = self._backup()
        if self.meta["backup"]:
            self.save_json()
            self._backup()          # once more, so the backup's session.json also says where it went

    def summary_row(self):
        d = self.meta.get("demographics") or {}
        post = self.meta.get("post_questionnaire") or {}
        return dict(self.meta, **d, **post, **self.meta.get("summary", {}))

    def _write_participant_xlsx(self):
        help_rows = [{"sayfa": a, "sutun": b, "anlami": c} for a, b, c in COLUMN_HELP]
        post = self.meta.get("post_questionnaire") or {}
        post_rows = [{"sutun": item[1], "soru": item[2], "yanit": post.get(item[1], "")} for item in POST]
        return export_xlsx(C.DATA_DIR / f"{self.base}.xlsx", {
            "ozet": ([self.summary_row()], SUMMARY_COLS),
            "basislar": (self.reports, REPORT_COLS),
            "m_basislari": (self.m_presses, M_PRESS_COLS),
            "hedefler": (self.targets, TARGET_COLS),
            "slaytlar": (self.trials, TRIAL_COLS),
            "son_sorular": (post_rows, ["sutun", "soru", "yanit"]),
            "sutun_aciklamalari": (help_rows, ["sayfa", "sutun", "anlami"]),
        })

    def _write_coding_sheet(self):
        # Practice reports are left out. Rows are shuffled so report order gives nothing away.
        rows = [r for r in self.reports if r["phase"] != "practice"]
        rows = sorted(rows, key=lambda r: r["report_code"])
        with open(self.paths["coding_BLIND.csv"], "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=CODING_COLS, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                out = {"report_code": r["report_code"], "description": r["q1_description"],
                       "private": r.get("q1_private", ""), "perceived_trigger": r["q4_trigger"]}
                for i, text in enumerate(r.get("_recent_cues", []), 1):
                    out["cue_1_most_recent" if i == 1 else f"cue_{i}"] = text
                w.writerow(out)

    def _append_session_log(self):
        """Adds this session to all_sessions.csv. If that file is locked (open in Excel on Windows), the
        line goes to a separate all_sessions_<base>.csv instead, so the session still ends normally."""
        path = C.DATA_DIR / "all_sessions.csv"
        for target in (path, C.DATA_DIR / f"all_sessions_{self.base}.csv"):
            try:
                new = not target.exists()
                with open(target, "a", newline="", encoding="utf-8-sig" if new else "utf-8") as f:
                    w = csv.DictWriter(f, fieldnames=SESSION_LOG_COLS, extrasaction="ignore")
                    if new:
                        w.writeheader()
                    w.writerow(self.summary_row())
                self.meta["session_log"] = target.name
                return
            except OSError as e:
                self.meta["session_log_error"] = str(e)

    def _backup(self):
        """Copies this session's files and all_sessions.csv to BACKUP_DIR. Returns where, or the error."""
        if not C.BACKUP_DIR:
            return None
        try:
            dest = Path(C.BACKUP_DIR)
            dest.mkdir(parents=True, exist_ok=True)
            for p in sorted(C.DATA_DIR.glob(f"{self.base}*")):
                shutil.copy2(p, dest / p.name)
            log = C.DATA_DIR / "all_sessions.csv"
            if log.exists():
                shutil.copy2(log, dest / "all_sessions.csv")
            return str(dest)
        except OSError as e:
            return f"FAILED: {e}"


def _is_text_column(col):
    # Identifiers and free text always stay text: "01" must not become 1, a code like "1E50" not 1e50.
    return col in ("participant_id", "condition", "base_name", "note", "computer") \
        or col.endswith(("_id", "_code", "_text")) or col in POST_TEXT_COLS \
        or col.startswith(("q1_desc", "q4_", "description", "perceived_trigger", "yanit", "soru"))


def _excel_value(v, col=""):
    """Numbers stay numbers in Excel (so formulas and pivot tables work); everything else is text."""
    if _is_text_column(col):
        return None if v in (None, "") else str(v)
    if isinstance(v, (list, tuple, dict)):
        return str(v)
    if isinstance(v, str):
        t = v.strip()
        if t in ("", "None"):
            return None
        try:
            return int(t) if t.lstrip("-").isdigit() else float(t)
        except ValueError:
            return v
    return v


def export_xlsx(path, sheets):
    """sheets: {sheet name: (rows as dicts, column list)}. Needs openpyxl (included in PsychoPy).
    Returns False (and writes nothing) if openpyxl is not installed."""
    try:
        import openpyxl
        from openpyxl.utils import get_column_letter
    except ImportError:
        return False
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for name, (rows, cols) in sheets.items():
        ws = wb.create_sheet(name[:31])
        ws.append(cols)
        for r in rows:
            ws.append([_excel_value(r.get(c), c) for c in cols])
        ws.freeze_panes = "A2"
        for i, c in enumerate(cols, 1):
            ws.column_dimensions[get_column_letter(i)].width = min(max(len(c) + 2, 10), 40)
    wb.save(path)
    return True
