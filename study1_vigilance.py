# -*- coding: utf-8 -*-
"""Study 1 — Immediate vs subsequently retrieved involuntary autobiographical memories.

Self-caught vigilance task (Schlagman & Kvavilashvili, 2008) with two between-subjects conditions:
  A  continuous: the 270 cue phrases appear on trials 1-270 (C-C-C...), lines only afterwards
  B  short lag : each cue is followed by one cue-free trial (C-N-C-N... over trials 1-539)
Both conditions: 800 slides of 1.5 s, 15 vertical-line targets at identical positions.
Every slide shows a scatter of short lines, mostly black and a few navy (5 horizontal templates;
3 vertical templates on target slides), with the cue phrase, if any, as plain text in the middle.
Participants press M for vertical lines and SPACE whenever a thought comes to mind, at any point in
the 800 slides; the task then stops for the 8 thought-probe questions (ethics form, Appendix F) and
continues afterwards.

Run in PsychoPy Coder (open this file, press Run). Parameters are in config.py.
Modes:
  Main experiment : demographics -> instructions -> 20-slide practice -> 800-slide task
                    -> end-of-study questions -> end
  Pilot           : instructions -> 10 slides of condition A -> 10 slides of condition B
                    -> end-of-study questions -> end
Question texts are in questions.py.
"""
import csv
import platform
import re

from psychopy import __version__ as psychopy_version
from psychopy import core, event, gui, logging, visual
from psychopy.hardware import keyboard

import config as C
import design
from datafiles import PREV_N, CODING_CUES, SessionWriter
from questions import POST, PRIVATE_PHRASE, PROBE, is_private

logging.console.setLevel(logging.WARNING)

MODE_MAIN = "Ana deney"
MODE_PILOT = "Pilot (10 deneme x 2 koşul)"
COND_AUTO = "Otomatik (tek no = A, çift no = B)"
COND_MANUAL = {"A - Sürekli (C-C-C)": "A", "B - Kısa aralık (C-N-C-N)": "B"}

INSTRUCTIONS = (
    "Bu görevde ekranda art arda yatay çizgilerden oluşan desenler göreceksiniz. Zaman zaman çizgiler dikey "
    "olacaktır. Göreviniz, dikey çizgiler gördüğünüz her seferde olabildiğince hızlı bir şekilde M tuşuna "
    "basmaktır.\n\n"
    "Ekranın ortasında zaman zaman kelimeler de görebilirsiniz. Bunlarla ilgili herhangi bir şey yapmanız "
    "gerekmiyor. Lütfen bilinçli olarak bir şeyi aklınıza getirmeye çalışmayınız. Yalnızca çizgi görevine "
    "odaklanınız.\n\n"
    "Görev boyunca bazen aklınıza kendiliğinden düşünceler gelebilir. Görevin başından sonuna kadar, "
    "aklınıza bir düşüncenin geldiğini fark ettiğiniz her seferde BOŞLUK tuşuna basınız. Görev duracak ve "
    "aklınıza gelen şeyi birkaç kelimeyle yazmanız ve birkaç kısa soruyu yanıtlamanız istenecektir. Lütfen "
    "sizi ya da başka birini tanımlayabilecek isim, yer veya ayrıntı yazmayınız. Aklınıza gelen şey çok "
    f"özel bir anıysa yalnızca \"{PRIVATE_PHRASE}\" yazabilirsiniz. Ardından görev kaldığı yerden devam "
    "edecektir.\n\n"
    "Durmak istediğiniz herhangi bir anda deneyi yürüten araştırmacıya söyleyebilirsiniz."
)

class QuitRequested(Exception):
    pass


def sharp_text(win, text="", height=0.032, pos=(0, 0), width=1.3, box_height=None, color="black",
               align="center", bold=False):
    """Text drawn with TextBox2, which renders much sharper than TextStim (especially on Retina screens)."""
    return visual.TextBox2(win, text=text, font=C.FONT, units="height", letterHeight=height, pos=pos,
                           size=(width, box_height or height * 3), color=color, alignment=align,
                           anchor="center", fillColor=None, borderColor=None, padding=0, bold=bold)


# =============================================================================================
# Dialogs (shown before the full-screen window opens)
# =============================================================================================
def completed_main_sessions(pid):
    path = C.DATA_DIR / "all_sessions.csv"
    if not path.exists():
        return 0
    with open(path, encoding="utf-8-sig") as f:
        return sum(1 for r in csv.DictReader(f)
                   if r["participant_id"] == pid and r["mode"] == "main" and r["status"] == "completed")


def setup_dialog():
    while True:
        info = {"Katılımcı no": "", "Mod": [MODE_MAIN, MODE_PILOT],
                "Koşul": [COND_AUTO] + list(COND_MANUAL), "Araştırmacı": "", "Not": ""}
        dlg = gui.DlgFromDict(info, title="Study 1 - Araştırmacı", sortKeys=False)
        if not dlg.OK:
            core.quit()
        pid = info["Katılımcı no"].strip()
        mode = "pilot" if info["Mod"] == MODE_PILOT else "main"
        if not pid:
            gui.criticalDlg("Eksik bilgi", "Katılımcı numarası girin.")
            continue
        if not re.fullmatch(r"[\w-]+", pid):    # becomes part of file names: must work on Windows and macOS
            gui.criticalDlg("Katılımcı no", "Yalnızca harf, rakam, - ve _ kullanın (boşluk, / : * ? gibi işaretler olmadan).")
            continue
        if mode == "pilot":
            condition = "AB"
        elif info["Koşul"] == COND_AUTO:
            condition = design.assign_condition(pid)
            if condition is None:
                gui.criticalDlg("Koşul", "Otomatik atama için sayısal numara gerekir (1, 2, 3...). "
                                "Pilot numaraları için koşulu elle seçin.")
                continue
        else:
            condition = COND_MANUAL[info["Koşul"]]
        if mode == "main" and completed_main_sessions(pid):
            ok = gui.Dlg(title="Uyarı")
            ok.addText(f"{pid} numarası için tamamlanmış bir oturum zaten var. Yine de devam edilsin mi?")
            ok.show()
            if not ok.OK:
                continue
        assignment = "pilot" if mode == "pilot" else ("alternating" if info["Koşul"] == COND_AUTO else "manual")
        return {"participant_id": pid, "mode": mode, "condition": condition, "assignment": assignment,
                "experimenter": info["Araştırmacı"].strip(), "note": info["Not"].strip()}


def demographics_dialog():
    """Appendix A. Filled in by the participant before the task window opens."""
    choose = "Seçiniz"
    labels = {
        "age": "1. Yaş",
        "gender": "2. Cinsiyet",
        "native_language": "3. Ana dil",
        "native_language_other": "    Ana dil 'Diğer' ise belirtiniz",
        "education": "4. Eğitim durumu",
        "education_detail": "    Öğrenci ise bölüm ve sınıf / 'Diğer' ise belirtiniz",
        "normal_vision": "5. Görmeniz normal ya da düzeltilmiş (gözlük/lens) normal mi?",
    }
    choices = {
        "gender": [choose, "Kadın", "Erkek", "Diğer", "Belirtmek istemiyorum"],
        "native_language": [choose, "Türkçe", "Diğer"],
        "education": [choose, "Üniversite öğrencisi", "Mezun", "Diğer"],
        "normal_vision": [choose, "Evet", "Hayır"],
    }
    values = {k: "" for k in labels}
    while True:
        info = {labels[k]: (choices[k] if k in choices else values[k]) for k in labels}
        dlg = gui.DlgFromDict(info, title="Demografik Sorular", sortKeys=False)
        if not dlg.OK:
            raise QuitRequested()
        values = {k: str(info[labels[k]]).strip() for k in labels}
        age_ok = values["age"].isdigit()
        if not age_ok or any(values[k] == choose for k in choices):
            gui.criticalDlg("Eksik bilgi", "Lütfen tüm soruları yanıtlayınız (yaş sayı olmalıdır).")
            continue
        values["age"] = int(values["age"])
        return values


# =============================================================================================
# Experiment
# =============================================================================================
class Experiment:
    def __init__(self, win, writer, cues):
        self.win = win
        self.w = writer
        self.kb = keyboard.Keyboard()
        self.mouse = event.Mouse(visible=False, win=win)
        rate = win.getActualFrameRate(nIdentical=10, nMaxFrames=120, nWarmUpFrames=10)
        self.frame_rate = rate if rate else 60.0
        self.frame_dur = 1.0 / self.frame_rate
        writer.meta["frame_rate_hz"] = round(self.frame_rate, 2)
        self.report_count = {}
        self.block = None          # state of the block that is running (used when SPACE is pressed)
        self._build_stimuli()

    # ---- stimuli ---------------------------------------------------------------------------
    def _build_stimuli(self):
        win = self.win
        # One Rect per line of every template, built once (design.templates() has the layouts).
        self.patterns = {}
        for tid, tpl in design.templates().items():
            self.patterns[tid] = [
                visual.Rect(win, units="height", pos=(ln.x, ln.y),
                            width=C.PATTERN_LINE_WIDTH if tpl.vertical else ln.length,
                            height=ln.length if tpl.vertical else C.PATTERN_LINE_WIDTH,
                            fillColor=C.LINE_COLORS_RGB255[ln.color], colorSpace="rgb255", lineColor=None)
                for ln in tpl.lines]
        # Two text stimuli used in turn, so the next phrase is rendered while the current slide shows.
        # The phrase is plain text on the background: no frame, no fill.
        self.cue_text = [sharp_text(win, height=C.CUE_TEXT_HEIGHT, pos=C.CUE_POS, width=2 * C.CUE_ZONE[0],
                                    box_height=C.CUE_TEXT_HEIGHT * 2, color=C.CUE_COLOR, bold=C.CUE_BOLD)
                         for _ in range(2)]
        self.feedback = sharp_text(win, height=0.035, pos=(0, 0.465), width=1.0)
        self.feedback_on = False
        self.feedback_until = 0.0
        self.msg = sharp_text(win, height=0.032, width=1.3, box_height=0.8, align="left")
        self.small = sharp_text(win, height=0.025, pos=(0, -0.44), width=1.4, color=(-0.4, -0.4, -0.4))

    def _prepare_cue(self, trial, slot):
        if trial is not None and trial.cue is not None:
            self.cue_text[slot].text = trial.cue.text

    def _draw_slide(self, trial, slot):
        for line in self.patterns[trial.template]:
            line.draw()
        if trial.cue is not None:
            self.cue_text[slot].draw()
        if self.feedback_on and core.getTime() < self.feedback_until:
            self.feedback.draw()

    def _show_feedback(self, outcome):
        if not self.feedback_on or outcome is None:
            return
        text, color = {"hit": ("Doğru", (-1, 0.4, -1)),
                       "false_alarm": ("Dikey çizgi yoktu", (0.8, -0.6, -0.6)),
                       "miss": ("Dikey çizgiyi kaçırdınız", (0.8, -0.6, -0.6))}[outcome]
        self.feedback.text, self.feedback.color = text, color
        self.feedback_until = core.getTime() + C.FEEDBACK_S

    # ---- generic screens -------------------------------------------------------------------
    def show_text(self, text, footer="Devam etmek için BOŞLUK tuşuna basınız.", keys=("space",), min_s=0.0):
        """min_s: keys are ignored this long, so a SPACE pressed as the slides end cannot skip the screen."""
        self.msg.text = text
        self.small.text = footer
        t_ready = core.getTime() + min_s
        self.kb.clearEvents()
        while True:
            self.msg.draw()
            self.small.draw()
            self.win.flip()
            if core.getTime() < t_ready:
                self.kb.clearEvents()
                continue
            pressed = self.kb.getKeys(list(keys) + [C.QUIT_KEY], waitRelease=False)
            if any(k.name == C.QUIT_KEY for k in pressed):
                self.confirm_quit()
                self.kb.clearEvents()
            elif pressed:
                break
        self.win.flip()
        self.kb.clearEvents()
        event.clearEvents()

    def blank(self, seconds):
        t_end = core.getTime() + seconds
        while core.getTime() < t_end:
            self.win.flip()

    def confirm_quit(self):
        self.msg.text = ("ARAŞTIRMACI: Deney sonlandırılsın mı?\n\nSonlandırmak için ESC'ye tekrar basınız.\n"
                         "Devam etmek için BOŞLUK tuşuna basınız.\n\nŞimdiye kadarki veriler kaydedilmiştir.")
        self.kb.clearEvents()
        while True:
            self.msg.draw()
            self.win.flip()
            pressed = [k.name for k in self.kb.getKeys([C.QUIT_KEY, "space"], waitRelease=False)]
            if C.QUIT_KEY in pressed:
                raise QuitRequested()
            if "space" in pressed:
                self.kb.clearEvents()
                return

    # ---- running a block of slides --------------------------------------------------------
    def run_block(self, trials, phase, condition, breaks=()):
        """Runs the slides; writes one row per slide. SPACE stops the task, opens the questions and
        the task continues with the next slide."""
        b = self.block = {
            "trials": trials, "phase": phase, "condition": condition,
            "t0": None,           # onset of the first slide = time 0 of this block
            "task_onsets": {},    # trial number -> onset on the task clock (pauses excluded)
            "paused": 0.0,        # time spent outside the slide stream (questions, blanks, breaks)
            "target_no": {t.trial: k for k, t in enumerate((t for t in trials if t.is_target), 1)},
            "m_count": 0,
        }
        onsets = {}               # trial number -> absolute onset time
        pause_start = None        # when the current pause began
        prev_row = None           # previous slide's row, kept open for a late target hit
        self.feedback_on = phase in C.FEEDBACK_PHASES
        self.feedback_until = 0.0
        self._prepare_cue(trials[0], 0)
        self.kb.clearEvents()
        self._frames_start()
        for i, tr in enumerate(trials):
            slot = i % 2
            row = self._new_row(tr, phase, condition)
            self.win.callOnFlip(self.kb.clock.reset)
            self._draw_slide(tr, slot)
            onset = self.win.flip()
            if b["t0"] is None:
                b["t0"] = onset
            if pause_start is not None:
                b["paused"] += onset - pause_start
                pause_start = None
            onsets[tr.trial] = onset
            b["task_onsets"][tr.trial] = onset - b["t0"] - b["paused"]
            row["onset_s"] = onset - b["t0"]
            row["onset_task_s"] = b["task_onsets"][tr.trial]
            if prev_row is not None and prev_row["duration_s"] == "":
                prev_row["duration_s"] = onset - onsets[prev_row["trial"]]
            self._prepare_cue(trials[i + 1] if i + 1 < len(trials) else None, 1 - slot)

            event_type, rt = self._slide_loop(i, slot, onset, row, prev_row)

            if prev_row is not None:
                self.w.write_trial(prev_row)
                prev_row = None

            if event_type in ("report", "quit") and tr.is_target and row["target_hit"] != 1:
                # The slide was cut short before an M press: not a miss, just not scorable.
                row["target_hit"] = ""
            if event_type == "report":
                row["duration_s"] = rt
                row["interrupted_by_report"] = 1
                pause_start = onset + rt
                report = self._report_context(i, onset + rt - b["t0"], onset + rt - b["t0"] - b["paused"], rt)
                row["report_id"] = report["report_id"]
                self.w.write_trial(row)
                self._frames_pause()
                self.mouse.setVisible(True)
                self.run_probe(report)
                self.mouse.setVisible(False)
                self.w.write_report(report)
                if tr.trial in breaks and i + 1 < len(trials):
                    self._break_screen()
                else:
                    self.blank(C.RESUME_BLANK_S)
                self.kb.clearEvents()
                self._frames_start()
            elif event_type == "quit":
                row["duration_s"] = rt
                pause_start = onset + rt
                self.w.write_trial(row)
                self.confirm_quit()        # raises QuitRequested if confirmed
                self.blank(C.RESUME_BLANK_S)
                self.kb.clearEvents()
            elif tr.trial in breaks and i + 1 < len(trials):
                pause_start = self.win.flip()
                row["duration_s"] = pause_start - onset
                self.w.write_trial(row)
                self._break_screen()
            else:
                prev_row = row

        if prev_row is not None:
            prev_row["duration_s"] = self.win.flip() - onsets[prev_row["trial"]]
            self.w.write_trial(prev_row)
        self._frames_pause()

    # ---- frame timing: counts slide frames that came late (only while slides are on screen) ----
    def _frames_start(self):
        self.win.refreshThreshold = 1.5 * self.frame_dur
        self.win.recordFrameIntervals = True

    def _frames_pause(self):
        self.win.recordFrameIntervals = False

    def _slide_loop(self, i, slot, onset, row, prev_row):
        """Keeps slide i on screen until SLIDE_S has passed or SPACE/ESC is pressed. Returns (event, rt)."""
        tr = self.block["trials"][i]
        t_last = onset
        miss_pending = (self.feedback_on and prev_row is not None and prev_row["is_target"]
                        and prev_row["target_hit"] == 0)
        while True:
            # Practice/pilot feedback for a target that got no M press, once its late window has passed.
            if miss_pending and t_last - onset > C.LATE_HIT_WINDOW_S:
                miss_pending = False
                if prev_row["target_hit"] == 0:
                    self._show_feedback("miss")
            for k in self.kb.getKeys([C.TARGET_KEY, C.THOUGHT_KEY, C.QUIT_KEY], waitRelease=False):
                rt = k.rt
                if k.name == C.TARGET_KEY:
                    self._show_feedback(self._register_m(i, onset, row, prev_row, rt))
                elif k.name == C.THOUGHT_KEY:
                    return "report", max(rt, 0.0)
                elif k.name == C.QUIT_KEY:
                    return "quit", max(rt, 0.0)
            # Stop when the next flip would be at (or past) the end of the slide.
            if t_last + self.frame_dur >= onset + C.SLIDE_S - self.frame_dur / 2:
                return "done", None
            self._draw_slide(tr, slot)
            t_last = self.win.flip()

    def _register_m(self, i, onset, row, prev_row, rt):
        """Scores one M press on slide i and writes it to the M-press file.
        Returns 'hit', 'false_alarm' or None (repeat press on a target already hit) for the feedback."""
        b = self.block
        trials = b["trials"]
        if rt < 0 and prev_row is not None:     # pressed just before this slide appeared: previous slide
            pi, prow, before, prt = i - 1, prev_row, None, (prev_row["duration_s"] or C.SLIDE_S) + rt
        else:
            pi, prow, before, prt = i, row, prev_row, max(rt, 0.0)
        prow["m_presses"] += 1
        if prow["m_rt_s"] == "":
            prow["m_rt_s"] = prt
        target, target_rt = None, ""
        if prow["is_target"]:
            target, target_rt = prow, prt
            if prow["target_hit"] != 1:
                prow["target_hit"], prow["target_rt_s"], prow["late_hit"] = 1, prt, 0
                outcome = "hit"
            else:
                outcome = "repeat"
        elif (before is not None and before["is_target"] and before["target_hit"] == 0
              and prt <= C.LATE_HIT_WINDOW_S):
            target, target_rt = before, (before["duration_s"] or C.SLIDE_S) + prt
            before["target_hit"], before["late_hit"], before["target_rt_s"] = 1, 1, target_rt
            outcome = "late_hit"
        else:
            prow["false_alarm"] = 1
            outcome = "false_alarm"

        t_abs = onset + rt
        tr = trials[pi]
        last = next((t for t in reversed(trials[: pi + 1]) if t.cue is not None), None)
        tgt = next(t for t in trials if t.trial == target["trial"]) if target else None
        b["m_count"] += 1
        self.w.write_m_press({
            "participant_id": self.w.meta["participant_id"], "condition": b["condition"],
            "mode": self.w.meta["mode"], "phase": b["phase"], "press_index": b["m_count"],
            "trial": tr.trial, "trial_type": tr.type, "time_into_trial_s": prt,
            "task_time_s": t_abs - b["t0"], "task_time_active_s": t_abs - b["t0"] - b["paused"],
            "outcome": outcome,
            "target_number": b["target_no"][tgt.trial] if tgt else "", "target_trial": tgt.trial if tgt else "",
            "rt_from_target_onset_s": target_rt,
            "late_by_s": prt if outcome == "late_hit" else (0 if tgt else ""),
            "cue_on_screen_order": tr.cue_order or "", "cue_on_screen_text": tr.cue.text if tr.cue else "",
            "last_cue_order": (last.cue_order or "") if last else "", "last_cue_text": last.cue.text if last else "",
            "trials_since_last_cue": tr.trial - last.trial if last else "",
            "target_cue_order": (tgt.cue_order or "") if tgt else "",
            "target_cue_text": tgt.cue.text if tgt and tgt.cue else "",
        })
        return {"hit": "hit", "late_hit": "hit", "false_alarm": "false_alarm"}.get(outcome)

    def _new_row(self, tr, phase, condition):
        return {
            "participant_id": self.w.meta["participant_id"], "condition": condition,
            "mode": self.w.meta["mode"], "phase": phase, "trial": tr.trial, "trial_type": tr.type,
            "is_target": int(tr.is_target), "cue_order": tr.cue_order if tr.cue_order else "",
            "cue_id": tr.cue.id if tr.cue else "", "cue_text": tr.cue.text if tr.cue else "",
            "cue_valence": tr.cue.valence if tr.cue else "",
            "template": tr.template,
            "onset_s": "", "onset_task_s": "", "duration_s": "", "interrupted_by_report": 0, "report_id": "",
            "m_presses": 0, "m_rt_s": "", "target_hit": 0 if tr.is_target else "",
            "target_rt_s": "", "late_hit": "", "false_alarm": 0,
        }

    def _break_screen(self):
        self.show_text("Mola\n\nKısa bir ara verebilirsiniz. Hazır olduğunuzda göreve devam etmek için "
                       "BOŞLUK tuşuna basınız.", footer="")
        self.blank(C.RESUME_BLANK_S)

    # ---- thought report --------------------------------------------------------------------
    def _report_context(self, i, t_rel, t_task, rt):
        """Cue context of a SPACE press on slide i. t_rel: seconds since the block's first slide;
        t_task: the same on the task clock, which stops while questions, blanks and breaks are on screen,
        so time since a cue never includes time spent answering an earlier report.
        rt: seconds since slide i appeared."""
        b = self.block
        trials, phase, condition, task_onsets = b["trials"], b["phase"], b["condition"], b["task_onsets"]
        tr = trials[i]
        shown = [t for t in trials[: i + 1] if t.cue is not None]      # cues up to and including now
        on_screen = tr if tr.cue is not None else None
        before = shown[:-1] if on_screen else shown
        last = shown[-1] if shown else None
        n = self.report_count.get(phase, 0) + 1
        self.report_count[phase] = n
        rep = {
            "participant_id": self.w.meta["participant_id"], "condition": condition,
            "mode": self.w.meta["mode"], "phase": phase,
            "report_id": f"{'PR' if phase == 'practice' else 'R'}{n:03d}" + ("" if phase in ("main", "practice") else f"_{phase}"),
            "report_code": self.w.new_report_code(),
            "trial": tr.trial, "trial_type": tr.type, "trial_is_target": int(tr.is_target),
            "report_index": n,
            "task_time_s": t_rel, "task_time_active_s": t_task, "time_into_trial_s": rt,
            "cue_on_screen_id": on_screen.cue.id if on_screen else "",
            "cue_on_screen_text": on_screen.cue.text if on_screen else "",
            "cue_on_screen_valence": on_screen.cue.valence if on_screen else "",
            "last_cue_trial": last.trial if last else "", "last_cue_id": last.cue.id if last else "",
            "last_cue_text": last.cue.text if last else "", "last_cue_valence": last.cue.valence if last else "",
            "trials_since_last_cue": tr.trial - last.trial if last else "",
            "s_since_last_cue_onset": t_task - task_onsets[last.trial] if last else "",
            "cues_shown_so_far": len(shown),
            "_recent_cues": [t.cue.text for t in reversed(shown[-CODING_CUES:])],
        }
        for k in range(1, PREV_N + 1):
            t = before[-k] if len(before) >= k else None
            rep[f"prev{k}_cue_trial"] = t.trial if t else ""
            rep[f"prev{k}_cue_id"] = t.cue.id if t else ""
            rep[f"prev{k}_cue_text"] = t.cue.text if t else ""
            rep[f"prev{k}_cue_valence"] = t.cue.valence if t else ""
        return rep

    def run_probe(self, report):
        t_start = core.getTime()
        unanswered = 0
        self.blank(0.2)
        for n, item in enumerate(PROBE, 1):
            if item[0] == "text":
                report[item[1]] = self.ask_text(f"{n}. {item[2]}")
            else:
                answer = self.ask_likert(f"{n}. {item[2]}", item[3], item[4])
                report[item[1]] = answer
                unanswered += answer == ""
        report["q1_private"] = is_private(report.get("q1_description"))
        report["n_unanswered"] = unanswered
        report["probe_duration_s"] = core.getTime() - t_start

    def run_post_questionnaire(self):
        """End-of-study questions (questions.POST), once, after the last slide. Saved in session.json."""
        answers = {}
        self.w.meta["post_questionnaire"] = answers
        self.show_text("Görev tamamlandı.\n\nSon olarak çalışma hakkında birkaç soru soracağız.",
                       footer="Devam etmek için BOŞLUK tuşuna basınız.", min_s=1.0)
        self.mouse.setVisible(True)
        for n, item in enumerate(POST, 1):
            if item[0] == "text":
                answers[item[1]] = self.ask_text(f"{n}. {item[2]}")
            else:
                answers[item[1]] = self.ask_likert(f"{n}. {item[2]}", item[3], item[4])
            self.w.save_json()
        self.mouse.setVisible(False)

    def ask_text(self, prompt):
        question = sharp_text(self.win, prompt, height=0.034, pos=(0, 0.22), box_height=0.15)
        box = visual.TextBox2(self.win, text="", font=C.FONT, units="height", pos=(0, 0.02),
                              size=(1.2, 0.22), letterHeight=0.032, color="black", fillColor="white",
                              borderColor="black", editable=True, alignment="top-left")
        button = visual.Rect(self.win, width=0.26, height=0.07, pos=(0, -0.22), units="height",
                             fillColor=(-0.6, -0.3, 0.3), lineColor=None)
        label = sharp_text(self.win, "Devam", height=0.03, pos=(0, -0.22), width=0.26, color="white")
        hint = sharp_text(self.win, "Yazmayı bitirince ENTER tuşuna basınız ya da Devam'a tıklayınız.",
                          height=0.024, pos=(0, -0.32), color=(-0.4, -0.4, -0.4))
        event.clearEvents()
        self.kb.clearEvents()
        box.hasFocus = True
        while True:
            for s in (question, box, button, label, hint):
                s.draw()
            self.win.flip()
            if "\n" in box.text or "\r" in box.text or self.mouse.isPressedIn(button, buttons=[0]):
                break
            if any(k.name == C.QUIT_KEY for k in self.kb.getKeys([C.QUIT_KEY], waitRelease=False)):
                self.confirm_quit()
        self._wait_mouse_release()
        text = box.text.replace("\r", " ").replace("\n", " ").strip()
        box.hasFocus = False
        self.kb.clearEvents()
        return text

    def ask_likert(self, prompt, low, high):
        question = sharp_text(self.win, prompt, height=0.034, pos=(0, 0.22), box_height=0.15)
        xs = [-0.4, -0.2, 0.0, 0.2, 0.4]
        boxes = [visual.Rect(self.win, width=0.14, height=0.11, pos=(x, 0.02), units="height",
                             fillColor="white", lineColor="black", lineWidth=2) for x in xs]
        nums = [sharp_text(self.win, str(v), height=0.045, pos=(x, 0.02), width=0.14)
                for v, x in zip(range(1, 6), xs)]
        anchors = [sharp_text(self.win, f"1 = {low}", height=0.024, pos=(xs[0], -0.11), width=0.3, box_height=0.08),
                   sharp_text(self.win, f"5 = {high}", height=0.024, pos=(xs[-1], -0.11), width=0.3, box_height=0.08)]
        hint = sharp_text(self.win, "1-5 tuşlarından birine basınız ya da bir kutuya tıklayınız.",
                          height=0.024, pos=(0, -0.2), color=(-0.4, -0.4, -0.4))
        skip = visual.Rect(self.win, width=0.26, height=0.06, pos=(0, -0.32), units="height",
                           fillColor=(0.6, 0.6, 0.6), lineColor=None)
        skip_label = sharp_text(self.win, "Boş bırak", height=0.026, pos=(0, -0.32), width=0.26)
        key_map = {str(v): v for v in range(1, 6)}
        key_map.update({f"num_{v}": v for v in range(1, 6)})
        self.kb.clearEvents()
        answer = None
        while answer is None:
            for s in [question, *boxes, *nums, *anchors, hint, skip, skip_label]:
                s.draw()
            self.win.flip()
            for k in self.kb.getKeys(list(key_map) + [C.QUIT_KEY], waitRelease=False):
                if k.name == C.QUIT_KEY:
                    self.confirm_quit()
                elif k.name in key_map:
                    answer = key_map[k.name]
            for v, b in enumerate(boxes, 1):
                if self.mouse.isPressedIn(b, buttons=[0]):
                    answer = v
            if answer is None and self.mouse.isPressedIn(skip, buttons=[0]):
                answer = ""
        if answer != "":                                   # brief highlight of the choice
            boxes[answer - 1].fillColor = (0.4, 0.6, 1.0)
            for _ in range(int(0.25 * self.frame_rate)):
                for s in [question, *boxes, *nums, *anchors, hint, skip, skip_label]:
                    s.draw()
                self.win.flip()
        self._wait_mouse_release()
        self.kb.clearEvents()
        return answer

    def _wait_mouse_release(self):
        while any(self.mouse.getPressed()):
            self.win.flip()


# =============================================================================================
# Main
# =============================================================================================
def check_psychopy_version():
    """Warns (but lets the experimenter continue) if this PsychoPy is much older than the tested one."""
    try:
        year = int(psychopy_version.split(".")[0])
    except ValueError:
        return
    if year < C.MIN_PSYCHOPY_YEAR:
        dlg = gui.Dlg(title="PsychoPy sürümü")
        dlg.addText(f"Bu bilgisayarda PsychoPy {psychopy_version} var. Deney {C.TESTED_PSYCHOPY} ile test edildi.\n"
                    "Aynı sürümü kurmanız önerilir. Yine de devam edilsin mi?")
        dlg.show()
        if not dlg.OK:
            core.quit()


def main():
    check_psychopy_version()
    setup = setup_dialog()
    cues = design.load_cues()
    dupes = design.duplicate_phrases(cues)
    if dupes:
        print("WARNING: duplicate cue phrases in the lists:", ", ".join(dupes))

    meta = dict(setup)
    meta.update({
        "study": C.STUDY_NAME, "version": C.VERSION,
        "condition_label": C.CONDITIONS[setup["condition"]]["label"] if setup["condition"] in C.CONDITIONS
        else "Pilot: A then B",
        "cue_list_fingerprint": design.cue_list_fingerprint(cues), "duplicate_cue_phrases": dupes,
        "slide_s": C.SLIDE_S, "total_trials": C.TOTAL_TRIALS, "target_positions": design.target_positions(),
        "breaks_after_trials": C.BREAKS_AFTER_TRIALS, "templates": sorted(design.templates()),
        "template_seed": C.TEMPLATE_SEED, "template_order_seed": C.TEMPLATE_ORDER_SEED,

        "demographics": None, "eligible": None, "status": "started",
    })
    cue_order = design.load_fixed_order(cues)        # same order for everyone (cue_order_fixed.csv)
    meta["cue_order_file"] = C.CUE_ORDER_FILE.name
    meta["cue_order"] = [c.id for c in cue_order]

    if setup["mode"] == "main":
        try:
            demo = demographics_dialog()
        except QuitRequested:
            core.quit()
        meta["demographics"] = demo
        meta["eligible"] = (C.MIN_AGE <= demo["age"] <= C.MAX_AGE and demo["native_language"] == "Türkçe"
                            and demo["normal_vision"] == "Evet")

    meta.update({"psychopy_version": psychopy_version, "python_version": platform.python_version(),
                 "os": platform.platform(), "computer": platform.node()})
    writer = SessionWriter(meta)
    win = visual.Window(fullscr=True, color=C.BACKGROUND_RGB255, colorSpace="rgb255", units="height",
                        allowGUI=False)
    win.mouseVisible = False
    writer.meta["screen_size_px"] = list(win.size)
    exp = Experiment(win, writer, cues)
    status = "completed"
    try:
        exp.show_text(INSTRUCTIONS, footer="Hazır olduğunuzda BOŞLUK tuşuna basınız.")
        if setup["mode"] == "main":
            exp.show_text("Önce kısa bir alıştırma yapacaksınız.")
            exp.run_block(design.build_practice_sequence(setup["condition"]), "practice", setup["condition"])
            exp.show_text("Alıştırma tamamlandı.\n\nŞimdi asıl görev başlayacak. Görev yaklaşık 20 dakika sürecektir.\n\n"
                          "Hatırlatma: görevin başından sonuna kadar, dikey çizgiler gördüğünüzde M, aklınıza "
                          "kendiliğinden bir düşünce geldiğinde BOŞLUK tuşuna basınız. BOŞLUK'a bastığınızda görev "
                          "duracak ve birkaç soru sorulacak, ardından kaldığı yerden devam edecektir. Kelimelerle "
                          "ilgili bir şey yapmanız gerekmiyor.\n\n"
                          "Sorunuz varsa lütfen şimdi araştırmacıya sorunuz.",
                          footer="Asıl görevi başlatmak için BOŞLUK tuşuna basınız.", min_s=1.0)
            trials = design.build_main_sequence(setup["condition"], cue_order)
            exp.run_block(trials, "main", setup["condition"], breaks=C.BREAKS_AFTER_TRIALS)
        else:
            pilot = design.build_pilot_sequences(cue_order)
            writer.meta["pilot_cues"] = {k: [t.cue.id for t in v if t.cue] for k, v in pilot.items()}
            exp.show_text("PİLOT – Bölüm 1: Sürekli koşul (A)\nHer slaytta bir ifade görünür (C-C-C...).",
                          footer="Başlatmak için BOŞLUK tuşuna basınız.")
            exp.run_block(pilot["A"], "pilot_A", "A")
            exp.show_text("PİLOT – Bölüm 2: Kısa aralık koşulu (B)\nİfadeler arasında birer boş slayt vardır (C-N-C-N...).",
                          footer="Başlatmak için BOŞLUK tuşuna basınız.", min_s=1.0)
            exp.run_block(pilot["B"], "pilot_B", "B")
    except QuitRequested:
        status = "aborted"
    frames = len(win.frameIntervals)
    writer.meta["frames_recorded"] = frames
    writer.meta["dropped_frames"] = win.nDroppedFrames
    writer.meta["dropped_frame_share"] = round(win.nDroppedFrames / frames, 4) if frames else ""
    if status == "completed":
        try:
            exp.run_post_questionnaire()
            writer.meta["post_questionnaire_complete"] = 1
        except QuitRequested:
            writer.meta["post_questionnaire_complete"] = 0     # the 800 slides are complete; status stays

    writer.close(status)
    # The participant sees only a thank-you message; performance is never shown on screen.
    exp.msg.text = "Görev tamamlandı.\n\nKatılımınız için teşekkür ederiz. Lütfen araştırmacıya haber veriniz."
    exp.msg.alignment = "center"
    exp.small.text = ""
    exp.kb.clearEvents()
    while not exp.kb.getKeys([C.QUIT_KEY], waitRelease=False):
        exp.msg.draw()
        exp.small.draw()
        win.flip()
    win.close()
    # Summary for the experimenter only (PsychoPy Coder output panel / terminal).
    s = writer.meta["summary"]
    print(f"\nSession {writer.meta['participant_id']} ({writer.meta['condition']}, {status}): "
          f"targets {s['targets_hit']}/{s['targets_total']}, false alarms {s['false_alarms']}, "
          f"reports {s['reports']}" + ("  -- NOT ELIGIBLE (age/language/vision)" if writer.meta.get("eligible") is False else ""))
    share = writer.meta.get("dropped_frame_share")
    if share != "" and share > C.MAX_DROPPED_FRAME_SHARE:
        print(f"WARNING: {share:.1%} of slide frames came late on this computer. Close other programs "
              "or use a faster computer.")
    print(f"Data saved in {C.DATA_DIR} as {writer.base}_*")
    if writer.meta.get("backup"):
        print(f"Backup copy: {writer.meta['backup']}")
    core.quit()


if __name__ == "__main__":
    main()
