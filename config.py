"""Study 1 parameters: continuous vs short-lag cue presentation in a self-caught vigilance task.

Design source: ethics form, item 6 (Ethics/MyDraft/Cagataystudy1EthicsFinal.docx, 11 Oct 2026).
Change values here, not in the task code.
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent

STUDY_NAME = "Study1_ContinuousVsShortLag"
VERSION = "2.4.0"   # 2.4: final cue list, Windows/Mac hardening; 2.3: practice follows the condition; 2.2: plain half-size phrase,
                    # post-task questions, M-press log, backup copy

# ---- Cue phrases (final Turkish list, read at start-up) ------------------------------------
# Tab-separated: cue_id, valence, word (stimuli/cue_words_psychopy.txt = cue_words_final_270.xlsx).
CUE_FILE = HERE / "stimuli" / "cue_words_psychopy.txt"
VALENCES = ("positive", "neutral", "negative")
CUES_PER_VALENCE = 90
# ONE fixed presentation order, the same for every participant and both conditions.
# Created once by make_cue_order.py (from CUE_ORDER_SEED); the experiment only reads it.
CUE_ORDER_FILE = HERE / "cue_order_fixed.csv"
CUE_ORDER_SEED = 20261014
MAX_SAME_VALENCE_RUN = 3      # never more than 3 phrases of the same valence in a row

# ---- Trial structure -----------------------------------------------------------------------
TOTAL_TRIALS = 800            # both conditions
N_CUES = 270                  # same 270 phrases in both conditions, in the fixed order of CUE_ORDER_FILE
CONDITIONS = {
    "A": {"label": "A - Continuous (C-C-C...)", "cue_gap": 0},   # cues on trials 1-270
    "B": {"label": "B - Short lag (C-N-C-N...)", "cue_gap": 1},  # cues on trials 1, 3, ..., 539
}
# 15 vertical targets: 5 evenly spaced inside each block, same positions in both conditions.
# Block 1 positions (27, 81, 135, 189, 243) are odd, so they fall on cue trials in both conditions.
TARGET_BLOCKS = [(1, 270), (271, 540), (541, 800)]
TARGETS_PER_BLOCK = 5

# ---- Timing ----------------------------------------------------------------------------------
SLIDE_S = 1.5                 # per slide, as in Schlagman & Kvavilashvili (2008); 800 x 1.5 s = 20 min
LATE_HIT_WINDOW_S = 1.0       # an M press this early in the slide after a target still counts as a hit
RESUME_BLANK_S = 1.0          # blank screen after a thought report (or a cancelled ESC stop), before the next slide
# Rest break shown after these trial numbers (e.g. [540], after the last cue in both conditions).
# Empty = no break: the 800 slides run without interruption.
BREAKS_AFTER_TRIALS = []

# ---- Practice (before the main task) ----------------------------------------------------------
# The practice follows the participant's condition, so they learn the rhythm of their own task:
# A shows a phrase on every slide (C-C-C, 20 phrases), B on every other slide (C-N-C-N, the first 10).
# Practice phrases are neutral and not in the 270 list.
PRACTICE_TRIALS = 20
PRACTICE_TARGETS = [6, 15]
PRACTICE_PHRASES = ["Ahşap sandalye", "Kapı zili", "Gazete", "Saksı", "Kahve fincanı",
                    "Merdiven korkuluğu", "Takvim", "Şemsiye", "Priz", "Cetvel",
                    "Anahtarlık", "Silgi", "Bardak altlığı", "Askılık", "Televizyon kumandası",
                    "Musluk", "Raf", "Tabure", "Çekmece", "Kaşık"]

# ---- Pilot mode: a short run of BOTH conditions, back to back -------------------------------
PILOT_TRIALS_PER_CONDITION = 10
PILOT_TARGETS = [5]           # trial 5 is a cue trial in both A and B

# ---- Keys -------------------------------------------------------------------------------------
TARGET_KEY = "m"
THOUGHT_KEY = "space"
QUIT_KEY = "escape"           # asks for confirmation, then saves everything collected so far

# ---- Assignment -------------------------------------------------------------------------------
# Numeric participant IDs alternate: odd -> A, even -> B (1 = A, 2 = B, 3 = A ...), so the groups
# are always equal within 1. Non-numeric IDs (e.g. "P01") need a manual condition.

# ---- Eligibility (ethics form item 7) ---------------------------------------------------------
MIN_AGE, MAX_AGE = 18, 25

# ---- Display (PsychoPy 'height' units: screen height = 1) ------------------------------------
BACKGROUND_RGB255 = (217, 217, 217)
CUE_POS = (0, 0)              # the cue phrase sits in the middle of the screen, as plain text (no box)
CUE_TEXT_HEIGHT = 0.025       # letter height (0.05 until v2.1; halved)
CUE_COLOR = "black"
CUE_BOLD = False

# Every slide shows short lines scattered at random places (never touching each other or the phrase
# box), mostly black with a few navy ones, as in the GMWA2 draft (Unity) program, which draws a random
# number of lines between liczba_linii_min/max with liczba_kolorowych_min/max of them coloured.
# 5 horizontal templates are used on ordinary slides (a different one from the previous slide every
# time), 3 vertical templates on the 15 target slides (each used 5 times). Template layouts and the
# order in which they appear come from fixed seeds: identical for every participant and both groups.
N_H_TEMPLATES = 5
N_V_TEMPLATES = 3
LINES_PER_SLIDE = (25, 35)    # min, max number of lines on one template (drawn once per template)
NAVY_PER_SLIDE = (4, 8)       # min, max number of those lines that are navy; the rest are black
FIELD_X = (-0.62, 0.62)       # area the lines are scattered in (fits 4:3, 16:10 and 16:9 screens)
FIELD_Y = (-0.44, 0.44)
CUE_ZONE = (0.56, 0.08)       # half width, half height of the central area kept free of lines (kept from
                              # v2.1 so the 8 line layouts stay exactly as piloted)
PATTERN_LINE_LENGTH = (0.05, 0.08)   # each line's length is drawn from this range
PATTERN_LINE_WIDTH = 0.007
MIN_GAP = 0.025               # minimum free space around every line
LINE_COLORS_RGB255 = {"black": (0, 0, 0), "navy": (0, 0, 128)}
TEMPLATE_SEED = 4242          # layouts of the 8 templates; change only before data collection starts
TEMPLATE_ORDER_SEED = 4243    # which template appears on which slide

# Feedback on M presses ("Doğru" / "Dikey çizgi yoktu" / "Dikey çizgiyi kaçırdınız").
# Shown only in these phases, never in the main task (the original paradigm gives no feedback).
FEEDBACK_PHASES = ("practice", "pilot_A", "pilot_B")
FEEDBACK_S = 0.8
FONT = "Arial"

# ---- Output -------------------------------------------------------------------------------------
DATA_DIR = HERE / "data"
# Second copy of every session's files, made when the session ends (e.g. a synced university OneDrive /
# Google Drive folder or an encrypted USB stick). None = no copy. Example:
#   BACKUP_DIR = Path.home() / "OneDrive - Bilkent" / "Study1_backup"
BACKUP_DIR = None
# Warn the experimenter if more than this share of main-task frames came late (slow computer).
MAX_DROPPED_FRAME_SHARE = 0.01

# ---- Software -------------------------------------------------------------------------------------
TESTED_PSYCHOPY = "2026.2.4"   # version the task was built and tested with (macOS); same on every computer
MIN_PSYCHOPY_YEAR = 2024       # older PsychoPy versions get a warning at start-up
