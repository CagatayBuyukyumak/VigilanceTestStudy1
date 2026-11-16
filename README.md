# Study 1: continuous vs short-lag self-caught vigilance task

PsychoPy implementation of Study 1 as described in the ethics form (`Ethics/MyDraft/Cagataystudy1EthicsFinal.docx`, item 6).

| | Group A: Continuous | Group B: Short lag |
|---|---|---|
| Slides | 800 × 1.5 s | 800 × 1.5 s |
| Cue phrases | 270, on trials 1–270 (C‑C‑C…) | 270, on trials 1, 3, …, 539 (C‑N‑C‑N…) |
| After the cues | lines only up to 800 | lines only up to 800 |
| Vertical targets | 15, at trials 27, 81, 135, 189, 243 · 297, 351, 405, 459, 513 · 566, 618, 670, 722, 774 | same positions |

| Block | Target slides | Group A | Group B |
|---|---|---|---|
| 1–270 | 27, 81, 135, 189, 243 | phrase on the slide | phrase on the slide |
| 271–540 | 297, 351, 405, 459, 513 | no phrase (A's phrases end at 270) | phrase on the slide |
| 541–800 | 566, 618, 670, 722, 774 | no phrase | no phrase |

**What the participant sees (v2.2).** Every slide shows 25–35 short lines scattered at random places over the screen, never touching each other, mostly black with 4–8 navy ones, following the logic of the GMWA2 draft program (a random number of lines between a minimum and a maximum, a few of them coloured, no overlaps). The cue phrase, when there is one, is plain black text in the middle (no frame, no white background; letter height 0.025, half of v2.1), and no line enters the central area. Ordinary slides use one of 5 horizontal templates (never the same one twice in a row); the 15 target slides use one of 3 vertical templates (each 5 times). The template on each slide is fixed (`template` column), identical for every participant and both groups. All 8 templates are in `slide_previews/`.

**SPACE stops the task.** Throughout the 800 slides, participants press SPACE whenever a thought comes to mind. The slide stops at once, the description and the 7 questions appear, and after a 1-s blank the task continues with the next slide. If a memory is too private to describe, participants type *Belirtmek istemiyorum* (instructions and question 1 say so); such reports get `q1_private = 1`.

**End-of-study questions** (after the 800 slides, `questions.POST`): what the study was about (asked first, before any question mentions the words), how boring it was, which words they remember, how often they read the words, how much the words caught their attention, how much the words triggered their thoughts, and whether they used the words to remember things on purpose. All question texts are in `questions.py`; they should be added to the ethics form as a new appendix.

Cue phrases come from `stimuli/cue_words_psychopy.txt` (tab-separated `cue_id`, `valence`, `word`; identical to `stimuli/cue_words_final_270.xlsx`): 90 positive, 90 neutral, 90 negative, with ids `POS_01` … `NEG_90`. The list was revised in November 2026 (33 phrases reworded, plus the two earlier fixes of duplicated phrases: POS_54 *Hediye vermek*, POS_77 *Tiyatroya gitmek*; same ids and valences, every phrase now unique); the final version of 11 November 2026 also changed NEU_53 to *Ütü* and NEU_86 to *Şahıs*. Earlier lists and order files are kept in `stimuli/_eski_liste_v1/` (October) and `stimuli/_eski_liste_v2_10kasim/` (10 November). Because ids and valences did not change, the presentation order stayed the same and only the text column of `cue_order_fixed.csv` was refreshed.

They are shown in **one fixed order**, the same for every participant and both groups. The order is random except that no valence appears more than 3 times in a row. It is stored in `cue_order_fixed.csv` (position, cue id, valence, text), which you can open in Excel or put in the thesis appendix. It was made once by `make_cue_order.py`, which refuses to overwrite it unless given `--overwrite`. Only regenerate it before data collection starts. If you correct a phrase's wording in the stimuli file, the corrected wording appears in the same position. Each session saves a fingerprint of the list, so you can tell which version a session used.

## 1. Install (once) — Windows and macOS

The same files run on Windows 10/11 and macOS: the code has no system-specific parts, reads and writes every file as UTF-8, and copes with Windows file locks. It was built and tested on **macOS with PsychoPy 2026.2.4**; before collecting data on a Windows computer, run `test_design.py` and one *Pilot* there. Install the same PsychoPy version on every computer (an older one gives a warning at start-up).

1. Download **PsychoPy Standalone 2026.2.4** for your system from <https://www.psychopy.org/download.html>.
   - **Windows:** run the installer (`.exe`).
   - **macOS:** drag PsychoPy to Applications. On first launch allow PsychoPy under *System Settings → Privacy & Security → Input Monitoring* and *Accessibility*, then restart it. Without this permission key presses are not recorded.
2. Unzip the `Study1_Experiment` folder somewhere you can write to, e.g. *Documents* (not inside *Program Files*, and preferably not inside a OneDrive/Dropbox folder that syncs while the task runs).

Nothing else needs installing: PsychoPy Standalone includes Python and every package the task uses (including openpyxl for the Excel files).

**Check the installation:** in PsychoPy Coder open `test_design.py` and press Run. The output panel should end with `59/59 checks passed`. (In a terminal with Python: `python3 test_design.py` on macOS, `py test_design.py` on Windows.)

**Windows notes:** keep `data/all_sessions.csv` closed in Excel while a session runs (Excel locks open files on Windows; if it is open, the session still finishes and writes its line to `all_sessions_<session>.csv` instead). Use display scaling 100–150 %; the display is drawn in screen-height units, so it looks the same on any screen of 4:3 or wider.

## 2. Run

1. In PsychoPy, open the **Coder** view, then *File → Open* → `study1_vigilance.py`.
2. Press the green **Run** button.
3. A dialog appears:
   - **Katılımcı no**: use `1, 2, 3 …` for real participants. With *Koşul = Otomatik*, odd numbers go to A and even numbers to B (1 = A, 2 = B, 3 = A …), so the groups are always equal within 1. For pilots use e.g. `P01`.
   - **Mod**:
     - *Ana deney*: demographics → instructions → 20-slide practice → 800-slide task without a break → end-of-study questions → end.
     - *Pilot (10 deneme x 2 koşul)*: instructions → 10 slides of condition A → 10 slides of condition B → end-of-study questions. Each block has one target, and the thought probe works. Use it to check the screen, the keys and the data files.

**Keys:** `M` = vertical lines · `SPACE` = a thought came to mind (stops the task and opens the 8 questions) · `ESC` = experimenter stop (asks for confirmation; data collected so far is already saved).

In the questions, participants type and press ENTER (or click *Devam*). For the 1–5 ratings they press 1–5 or click a box. *Boş bırak* skips a question, as allowed in the consent form.

**Check the design:** run `test_design.py` in PsychoPy Coder (or `python3 test_design.py` / `py test_design.py`).

## 3. Data (`data/` folder)

Files are written while the task runs, so a crash loses at most one slide. All are UTF-8 CSV with commas.

**Timing of a SPACE press** (sheet `basislar` / file `_reports.csv`):
- `time_into_trial_s`: seconds from the moment the slide (and its phrase) appeared to the press, 0–1.5.
- `s_since_last_cue_onset`: seconds from the onset of the most recent phrase to the press. `trials_since_last_cue` is the same in slides (0 = the phrase was still on screen).
- `task_time_s`: seconds from the first slide (wall clock, question screens included).

**Timing of an M press** (sheet `m_basislari` / file `_m_presses.csv`, one row per press):
- `trial`, `time_into_trial_s`: on which slide and at which second of it M was pressed; `task_time_s`: at which second of the task.
- `outcome`: `hit` (while the vertical lines were on screen), `late_hit` (on the next slide, within `LATE_HIT_WINDOW_S`), `repeat` (a second press on a target already hit), `false_alarm` (no target).
- `target_number` (1–15), `rt_from_target_onset_s` (how many seconds after the vertical lines appeared), `late_by_s` (for a late hit: how many seconds after the vertical lines had gone; 0 when on time).
- `cue_on_screen_text`, `last_cue_order` / `last_cue_text` (which phrase, 1–270, was the most recent), `target_cue_order` / `target_cue_text` (the phrase on the target slide).

The sheet `hedefler` has one row per target: `outcome` (`on_time`, `late`, `miss`, `not_scorable` = cut short by SPACE before any M press), `rt_s`, `late_by_s`, block, the phrase on the slide and the most recent phrase.

**Two clocks:** `onset_s` / `task_time_s` are wall-clock times from the first slide. `onset_task_s` / `task_time_active_s` are on a *task clock* that stops while the questions (and the 1-s blank after them) are on screen. `s_since_last_cue_onset` and the lag in seconds use the task clock, so the time a participant spends answering one report never inflates the cue-to-report delay of the next.

| File | Content |
|---|---|
| `S1_<id>_<cond>_<date>.xlsx` | **the participant's own Excel file**, written at the end: `ozet` (demographics, condition, targets on time / late / missed, mean RT, number of presses, end-of-study answers, computer), `basislar` (one row per SPACE press), `m_basislari` (one row per M press), `hedefler` (one row per target), `slaytlar` (one row per slide), `son_sorular` (end-of-study questions with answers), `sutun_aciklamalari` (what each column means, in Turkish) |
| `…_m_presses.csv` | one row per M press (see above) |
| `S1_<id>_<cond>_<date>_trials.csv` | one row per slide: trial, C/N, target, cue id/text/valence, `template`, onset, duration, `interrupted_by_report`, `report_id`, M presses, hit/late hit/false alarm |
| `…_reports.csv` | one row per SPACE press, written as soon as its questions are answered: `report_index` (1, 2, 3… per person), trial, `time_into_trial_s`, cue on screen, last cue, `trials_since_last_cue`, `s_since_last_cue_onset`, the 6 previous cues (trial, id, text, valence), the 8 answers (`q1_description` … `q8_specificity`), `n_unanswered`, `probe_duration_s` |
| `…_coding_BLIND.csv` | for the blind coders: random report code, description, perceived trigger, the 6 most recent cues (no condition, no timing). Coders fill `CODER_specific_memory_0_1` and `CODER_matching_cue_1_to_6_or_0_none` |
| `…_session.json` | settings, full cue order, demographics, eligibility, end-of-study answers, PsychoPy version, computer name, screen size, late-frame share, summary |
| `all_sessions.csv` | one line per session (quick overview) |

Pilot sessions are prefixed `PILOT_`.

To merge everyone, run `python3 combine_data.py` (add `--include-pilot` to also include pilots). It writes `data/combined/`:
- `trials_all.csv` and `reports_all.csv`: long format, one row per slide or report, ready for R/jamovi/SPSS mixed models with reports nested in participants.
- `m_presses_all.csv` and `targets_all.csv`: every M press and every target (the target table is rebuilt from the slides, so it also covers sessions from before v2.2).
- `participants.csv`: one row per person, with hit rate, targets on time / late / missed, mean RT, report counts, private reports, end-of-study answers and the computer used.
- `coding_BLIND_all.csv`: all reports shuffled across participants.
- `Study1_data.xlsx`: participants, reports, M presses, targets and trials as Excel sheets, with numbers stored as numbers and ids kept as text. Run `combine_data.py` from PsychoPy to get this file; plain Python 3.14 has no openpyxl.

Make the coding sheet once, after data collection ends; re-running `combine_data.py` with new sessions reshuffles it.

**After coding:** `python3 merge_coding.py FINAL.xlsx [SECOND_CODER.xlsx]` (run from PsychoPy for .xlsx files). It joins the coders' decisions back to the reports and writes `reports_coded.csv`, `participants_coded.csv` and `Study1_coded.xlsx` with these new columns:

| Column | Meaning |
|---|---|
| `matched_cue_id/_text/_valence/_trial` | the cue the coder matched |
| `memory_type` | `immediate` (matched cue was on screen), `subsequent` (an earlier cue), `no_match`, `uncoded` |
| `lag_cues` | cues shown after the matched one (0 = most recent) |
| `lag_slides` | slides between the matched cue and the report |
| `lag_s` | seconds, on the task clock |
| `unintentional` | `q2_intentionality` ≤ 2 |
| `specific` | coder's specificity decision |
| `include_main_analysis` | unintentional, specific and matched to a cue |
| participants: `n_included`, `n_immediate`, `n_subsequent`, `prop_subsequent` | per person, among included memories |

With a second coder's file it also prints percent agreement and Cohen's kappa, and writes `coding_disagreements.csv`. The cut-offs (`INTENTIONALITY_MAX`, `USE_CODER_SPECIFICITY`) are at the top of `merge_coding.py`; fix them with your supervisor before looking at results.

## 4. Settings to confirm (in `config.py`)

- End screen: participants only see a thank-you message. The session summary (targets hit, false alarms, number of reports) is printed in PsychoPy's output panel for the experimenter, and saved in `_session.json` and `all_sessions.csv`.

- `SLIDE_S = 1.5`: the slide duration is not stated in the ethics form or proposal. 1.5 s follows Schlagman & Kvavilashvili (2008) and gives a ~20-minute task.
- `BREAKS_AFTER_TRIALS = []`: no rest break; the 800 slides run without interruption. `[540]` would add one after the last cue of both conditions. The instruction sentence about resting during breaks was removed, so Appendix E of the ethics form should be updated to match.
- Practice: 20 slides in the participant's own rhythm, so they learn the task they will do: group A sees a phrase on every slide (C-C-C, 20 phrases), group B on every other slide (C-N-C-N, the first 10 of the same phrases). Targets on practice slides 6 and 15 and the line patterns are the same in both. The 20 neutral practice phrases (`PRACTICE_PHRASES`) are not in the 270 list.
- `LATE_HIT_WINDOW_S = 1.0`: an M press in the first second after a target slide still counts as a hit. A target cut short by a SPACE report before any M press is left unscored (`target_hit` empty), not counted as a miss.
- Display: line-pattern templates (`N_H_TEMPLATES`, `N_V_TEMPLATES`, `LINES_PER_SLIDE`, `NAVY_PER_SLIDE`, `FIELD_X/Y`, `CUE_ZONE`, `PATTERN_LINE_*`, `MIN_GAP`, `LINE_COLORS_RGB255`). The line counts are our own choice: the draft's values are in its encrypted configuration file, so ask your supervisor for `liczba_linii_min/max` and `liczba_kolorowych_min/max` and copy them into `LINES_PER_SLIDE` and `NAVY_PER_SLIDE`. Layouts come from `TEMPLATE_SEED`, the order from `TEMPLATE_ORDER_SEED`; change them only before data collection. `python3 test_design.py` checks that lines never touch each other or the phrase box. The phrase is in the middle (`CUE_POS`). All text uses PsychoPy's TextBox2 for sharp rendering.
- `CUE_TEXT_HEIGHT = 0.025`, `CUE_COLOR`: phrase size and colour. `CUE_ZONE` was kept from v2.1 so the 8 line layouts are exactly the piloted ones; making it smaller (e.g. `(0.30, 0.05)`) lets lines come closer to the phrase but creates 8 new layouts.
- `BACKUP_DIR`: when set, every session's files and `all_sessions.csv` are copied there at the end (see section 5).
- `MAX_DROPPED_FRAME_SHARE = 0.01`: if more than 1 % of slide frames came late, PsychoPy's output panel warns that the computer is too slow; the share is saved as `dropped_frame_share`.
- On-screen texts contain no semicolons (checked by `test_design.py`).
- Earlier versions are kept in `_backup_v1.1.0/` (single jittering line, permuted-block assignment), `_backup_v2.0.0/` (grid templates, questions after the task) `_backup_v2.1.0/` (phrase in a white box at 0.05, no end-of-study questions) and `_backup_v2.2.0/` (same C-N-C-N practice for both groups).
- `FEEDBACK_PHASES`: "Doğru" / "Dikey çizgi yoktu" / "Dikey çizgiyi kaçırdınız" appears after M presses in the practice and pilot only, never in the main task.


## 5. Running on another computer, and keeping the data safe

**Same software everywhere.** Install the same PsychoPy Standalone version on every computer (section 1; the version, operating system and computer name are saved in every session). Copy the whole `Study1_Experiment` folder (USB stick or cloud), run `test_design.py`, then a *Pilot*. Close other programs during a session; the output panel warns if the computer drew slides late. Participant numbers may contain only letters, digits, `-` and `_`, because they become part of file names on both systems.

**One lab computer for real data** if possible: same screen, keyboard and room for everyone.

**Data:**
1. Everything is written to `data/` inside the folder while the task runs; the participant's Excel file is written at the end.
2. Set `BACKUP_DIR` in `config.py` to a folder that syncs to the university cloud (e.g. Bilkent OneDrive / Google Drive) or to an encrypted USB stick. Every session is then copied there automatically; the output panel prints where.
3. Keep at least two copies (lab computer + backup), and check after each session day that the backup folder has the new files.
4. Data files hold only the participant number, never a name. Keep the list linking names to numbers and the consent forms separately (paper, locked), as the ethics form says.
5. Run `combine_data.py` on the backup copy for analysis; never edit the raw `data/` files by hand.
6. Before real data collection starts, move the test sessions out of `data/` (e.g. into `data/_tests/`), so `combine_data.py` does not mix them with real participants.
