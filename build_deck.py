"""Builds presentation/Presentation.pptx and Presentation_Script.docx from figures + summary."""
import json
from pathlib import Path
from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

ROOT = Path.cwd()
FIG = ROOT / "figures"
S = json.load(open(ROOT / "data" / "processed" / "analysis_summary.json"))
m1, m2, m5, rob = S["m1_same_window"], S["m2_expected_points"], S["m5_benchmark"], S["robustness"]

INK  = RGBColor(0x1F, 0x29, 0x37)
MU   = RGBColor(0xC8, 0x10, 0x2E)
GRAY = RGBColor(0x6B, 0x74, 0x80)
LGRAY= RGBColor(0xD8, 0xDD, 0xE3)

prs = Presentation()
prs.slide_width  = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]

def add_box(slide, l, t, w, h):
    box = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    box.text_frame.word_wrap = True
    return box

def style_run(r, size, color=INK, bold=False, italic=False):
    r.font.size = Pt(size); r.font.color.rgb = color
    r.font.bold = bold; r.font.italic = italic
    r.font.name = "Calibri"

def title_slide(tag="AMA2233 · Data Analytics and Visualization"):
    s = prs.slides.add_slide(BLANK)
    bar = s.shapes.add_shape(1, Inches(0), Inches(0), Inches(13.333), Inches(0.16))
    bar.fill.solid(); bar.fill.fore_color.rgb = MU; bar.line.fill.background()
    tb = add_box(s, 0.9, 2.15, 11.5, 0.5)
    style_run(tb.text_frame.paragraphs[0].add_run(), 13, GRAY)
    tb.text_frame.paragraphs[0].runs[0].text = tag
    tb = add_box(s, 0.9, 2.6, 11.5, 1.9)
    style_run(tb.text_frame.paragraphs[0].add_run(), 40, INK, bold=True)
    tb.text_frame.paragraphs[0].runs[0].text = "Ten games of signal and noise"
    p2 = tb.text_frame.add_paragraph()
    style_run(p2.add_run(), 40, MU, bold=True)
    p2.runs[0].text = "What Manchester United's 18th place really means"
    tb = add_box(s, 0.9, 5.3, 11.5, 0.5)
    style_run(tb.text_frame.paragraphs[0].add_run(), 15, GRAY)
    tb.text_frame.paragraphs[0].runs[0].text = (
        "AMA2233 course project · Premier League 2021/22–2026/27 · data extracted 18 November 2026")
    return s

def content_slide(title, fig=None, takeaway=None, tag="AMA2233"):
    s = prs.slides.add_slide(BLANK)
    bar = s.shapes.add_shape(1, Inches(0), Inches(0), Inches(13.333), Inches(0.1))
    bar.fill.solid(); bar.fill.fore_color.rgb = MU; bar.line.fill.background()
    tb = add_box(s, 0.55, 0.28, 12.2, 0.6)
    style_run(tb.text_frame.paragraphs[0].add_run(), 23, INK, bold=True)
    tb.text_frame.paragraphs[0].runs[0].text = title
    if fig is not None:
        im = Image.open(fig); wpx, hpx = im.size
        max_w, max_h = 10.6, 5.35
        w = min(max_w, max_h * wpx / hpx)
        h = w * hpx / wpx
        left = (13.333 - w) / 2
        s.shapes.add_picture(str(fig), Inches(left), Inches(0.95), width=Inches(w))
    if takeaway:
        tb = add_box(s, 0.8, 6.55, 11.7, 0.65)
        style_run(tb.text_frame.paragraphs[0].add_run(), 14, MU, bold=True, italic=True)
        tb.text_frame.paragraphs[0].runs[0].text = takeaway
    tb = add_box(s, 12.35, 7.05, 0.8, 0.35)
    style_run(tb.text_frame.paragraphs[0].add_run(), 9, GRAY)
    tb.text_frame.paragraphs[0].runs[0].text = f"{len(prs.slides.__iter__.__self__._sldIdLst)}"
    return s

def bullets_slide(title, bullets, takeaway=None):
    s = prs.slides.add_slide(BLANK)
    bar = s.shapes.add_shape(1, Inches(0), Inches(0), Inches(13.333), Inches(0.1))
    bar.fill.solid(); bar.fill.fore_color.rgb = MU; bar.line.fill.background()
    tb = add_box(s, 0.55, 0.35, 12.2, 0.7)
    style_run(tb.text_frame.paragraphs[0].add_run(), 26, INK, bold=True)
    tb.text_frame.paragraphs[0].runs[0].text = title
    tb = add_box(s, 0.9, 1.45, 11.6, 4.9)
    first = True
    for lead, body in bullets:
        p = tb.text_frame.paragraphs[0] if first else tb.text_frame.add_paragraph()
        first = False
        style_run(p.add_run(), 17, MU, bold=True)
        p.runs[0].text = "▪ "
        style_run(p.add_run(), 17, INK, bold=True)
        p.runs[1].text = lead + "  "
        style_run(p.add_run(), 16, INK)
        p.runs[2].text = body
        p.space_after = Pt(14)
    if takeaway:
        tb = add_box(s, 0.8, 6.6, 11.7, 0.6)
        style_run(tb.text_frame.paragraphs[0].add_run(), 14, MU, bold=True, italic=True)
        tb.text_frame.paragraphs[0].runs[0].text = takeaway
    tb = add_box(s, 12.35, 7.05, 0.8, 0.35)
    style_run(tb.text_frame.paragraphs[0].add_run(), 9, GRAY)
    tb.text_frame.paragraphs[0].runs[0].text = str(len(prs.slides._sldIdLst))
    return s

def note(slide, text):
    slide.notes_slide.notes_text_frame.text = text

# ---------- slides ----------
s = title_slide()
note(s, "After ten matches of this season, Manchester United sit 18th with eight points. Three from safety. "
        "The natural reaction is panic: sell the squad, sack the manager. Our project asks a quieter question: "
        "how much of this table position is signal, and how much is noise? Over the next ten minutes we answer "
        "it with six seasons of match data, a chance model, and the best judge available: history.")

s = bullets_slide("The question", [
    ("Is the decline real?", "compare identical windows — first ten rounds of 2025/26 against first ten of 2026/27."),
    ("Is 18th a fair price?", "compare actual points with the points United's chances deserved (expected points from xG)."),
    ("How much is a ten-game table worth?", "benchmark against 100 completed team-seasons, 2021/22 to 2025/26."),
], takeaway="Same window · same metric · history as the judge")
note(s, "Three sub-questions replace the unanswerable one — what explains the collapse — which would need "
        "counterfactuals about squads and tactics. Question one: is the decline real, once the comparison is "
        "fair? Question two: is 18th a fair description of the underlying play? Question three: how much "
        "evidence is a ten-match table in the first place?")

s = content_slide("The decline is real", FIG / "01_same_window.png",
    takeaway=f"Same ten games: {int(m1['2025/26']['pts'])} points → {int(m1['2026/27']['pts'])}. "
             f"Goals {m1['2025/26']['gf']}→{m1['2026/27']['gf']}, conceded {m1['2025/26']['ga']}→{m1['2026/27']['ga']}.")
note(s, f"First: the decline is real. Last season United took {int(m1['2025/26']['pts'])} points from the first "
        f"ten rounds and sat sixth. This season, over the identical window, {int(m1['2026/27']['pts'])} points "
        f"and eighteenth. That is a fifty-three percent drop, and it shows on both sides of the ball: goals "
        f"scored fell from {m1['2025/26']['gf']} to {m1['2026/27']['gf']}, goals conceded rose from "
        f"{m1['2025/26']['ga']} to {m1['2026/27']['ga']}. The grey dashed line is the league median pace — "
        "United are tracking well below it. So far, so worrying.")

s = content_slide("But the table overstates it", FIG / "02_actual_vs_expected.png",
    takeaway=f"Expected {m2['xpts']} points, actual {int(m2['actual'])}. "
             f"4th-best attack by xG ({m2['xgpg']}), 4th-worst defence ({m2['xgApg']}).")
note(s, f"Now the second question. For every match we model goals as independent Poisson draws at each team's "
        f"xG and compute expected points — the points the chances were worth. Across the league the model is "
        f"the aggregated totals match: mean expected {m2['league_mean_xpts']} against {m2['league_mean_actual']} "
         "actual — a sanity check on the league-wide mean, not a full calibration test. "
        f"United's ten games were worth {m2['xpts']} points, not {int(m2['actual'])}. One point three per match "
        f"is a mid-table pace over these ten games. Look at the profile: United create {m2['xgpg']} xG per match, the league's "
        f"{m2['xg_rank']}th-best attack — and concede {m2['xgApg']}, the {m2['xgA_rank']}th-worst defence. "
        "The attack is not the problem. The team above the line gets more points than its chances; United "
        "are far below it.")

s = content_slide("Six places apart", FIG / "03_rank_twist.png",
    takeaway="Ten-match chance-based rank 12th vs actual 18th — third-largest negative residual (−5.0 vs expectation).")
note(s, f"Rank every club by the gap between actual and chance-based position. United's twist is plus six "
        f"places: the five-point shortfall against the chance model is worth six table positions, and only "
        f"two clubs have larger negative residuals. Whether that residual is luck, finishing skill or model "
        "error, the data cannot separate — but we are not saying United are good. We are saying the table, "
        "read naively, misprices them by a third of the league — and naive readings drive real decisions.")

s = content_slide("What history says about ten-game tables", FIG / "05_historical_benchmark.png",
    takeaway=f"ρ = {m5['rho']} (points, n = {m5['n']}) · the same 17-point start finished 3rd, 10th and 17th.")
note(s, f"Third question: how much should anyone trust a ten-round table? We compared every club's points "
        f"after ten rounds with its final points across {m5['n']} completed team-seasons. The Spearman "
        f"correlation is {m5['rho']} — strong, clearly non-chance, yet far from prophecy: two-thirds of the "
        f"variance is explained and the average club still moves "
        f"{m5['mean_abs_move']} places between round ten and round thirty-eight. And here is the warning for "
        "United themselves: in twenty-twenty-five/twenty-six, Chelsea, Manchester United and Tottenham all "
        "had seventeen points after ten rounds. They finished tenth, third and seventeenth. Same start, "
        "fourteen places apart. The red band is United's current eight points: teams starting on six to ten "
        f"points finished anywhere from {m5['slice_min']} to {m5['slice_max']}, median {m5['slice_median']:.0f}. "
        "Relegation is not the favourite — but the honest reading is uncertainty, in both directions.")

s = content_slide("Where the gap opened", FIG / "06_cumulative_luck.png",
    takeaway=f"Finishing −{abs(m2['finishing'])} goals vs xG, defence +{m2['defdev']} vs xGA — five points below expectation.")
note(s, f"The gap between the blue expected line and the red actual line is roughly five points. Two goal-level "
        f"channels sit behind it: finishing — United scored {m2['finishing']} goals fewer than their chances "
        f"warranted — and defensive outcomes, {m2['defdev']} goals more than expected. Goals and points are "
        "different units: these channels show where the gap accumulated, they do not sum to it. Match by "
        "match, the damage concentrates "
        "in a handful of games where chances were there and points were not. And it is not the schedule: "
        f"United's opponents average {rob['mu_sos']} points per match against a league average of "
        f"{rob['league_sos']}. What causes the five points — luck, skill or model error — is exactly what the "
        "data cannot separate, and exactly what should be treated cautiously before any personnel decision.")

s = bullets_slide("So what should be done?", [
    ("Don't manage on the headline number.", "18th overweights noise; the same table one year ago implied a title race for a club that finished 17th."),
    ("Don't dismiss the run either.", "1.30 expected points per match over ten games is a mid-table pace — itself a real fall from 71 points and 3rd."),
    ("Where the evidence points: defence and finishing — hypotheses, not verdicts.", "Defence concedes the 4th-worst chances; conversion halved from 11.1% to 7.3%. Investigate there first."),
], takeaway="Investigate the defence and the finishing — not the table.")
note(s, "So what does this mean for decisions? First, do not manage on the headline number: an eighteen-place "
        "reading of a ten-round table overweights noise. Second, do not dismiss the run either: one point "
        "three expected per match is mid-table, and mid-table is itself a severe decline from last season's "
        "seventy-one points and third place. Third, treat the aggregates as hypotheses to investigate: chance "
        "creation is fine; chance prevention and finishing look broken. Those are places to look, not "
        "verdicts on individuals.")

s = bullets_slide("Limits of the evidence", [
    ("One provider's xG, one season.", "xG exists only for 2026/27, so no cross-season chance comparison."),
    ("A simple chance model.", "Independent Poisson scorelines; real goals are correlated."),
    ("Team-level aggregates only.", "No players, injuries or tactics — mechanisms are hypotheses, not proven causes."),
    ("Five seasons of history.", "A hundred team-seasons is enough to bound the question, not to settle it."),
], takeaway="This paper establishes what ten matches can and cannot say.")
note(s, "To be clear about the boundary. The xG comes from one provider and only for the current season. The "
        "Poisson model assumes independent scorelines. Everything is team-level; no player, injury or tactical "
        "data, so the mechanisms we propose are hypotheses, not proven causes. And the historical benchmark "
        "rests on five seasons — enough to bound the question, not to settle it.")

s = bullets_slide("Three sentences", [
    ("The decline is real.", "17 points became 8 over identical windows."),
    ("The table exaggerates it.", "the chances were worth 13 points — roughly 12th over these ten games, not 18th."),
    ("History says stay calm and be precise.", "respond to the defence and the finishing; refuse to read the table as prophecy."),
], takeaway="Thank you.")
note(s, "Three sentences to take away. The decline is real: seventeen points became eight over identical "
        "windows. The table exaggerates it: the chances were worth thirteen points, roughly twelfth, not "
        "eighteenth. And history says stay calm and be precise: respond to the defence and the finishing, "
        "and refuse to read the table as prophecy. Thank you.")

prs.save(ROOT / "presentation" / "Presentation.pptx")
print("slides:", len(prs.slides._sldIdLst))
