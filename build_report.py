"""Builds report/Academic_Report.docx from analysis_summary.json + figures.

Run with a Python that has python-docx (the bundled office runtime)."""
import json
from pathlib import Path
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

ROOT = Path.cwd()
FIG = ROOT / "figures"
S = json.load(open(ROOT / "data" / "processed" / "analysis_summary.json"))
m1, m2, m5, rob = S["m1_same_window"], S["m2_expected_points"], S["m5_benchmark"], S["robustness"]
trio = S["trio_17pts"]["teams"]  # [(team, final_pts), ...]

INK = RGBColor(0x1F, 0x29, 0x37)
MU  = RGBColor(0xC8, 0x10, 0x2E)
GRAY= RGBColor(0x5A, 0x64, 0x72)

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21.59), Cm(27.94)
for a in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
    setattr(sec, a, Cm(1.9))

st = doc.styles["Normal"]
st.font.name = "Calibri"; st.font.size = Pt(10.5); st.font.color.rgb = INK
st.paragraph_format.line_spacing = 1.12
st.paragraph_format.space_after = Pt(5)
st.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

def style_heading(name, size, color=INK, space_before=10, space_after=4):
    s = doc.styles[name]
    s.font.name = "Calibri"; s.font.size = Pt(size); s.font.bold = True
    s.font.color.rgb = color
    s.paragraph_format.space_before = Pt(space_before)
    s.paragraph_format.space_after = Pt(space_after)
style_heading("Heading 1", 13.5)
style_heading("Heading 2", 11.5)

def para(text, bold=False, italic=False, align=None, size=None, color=None, space_after=None):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = bold; r.italic = italic
    if size: r.font.size = Pt(size)
    if color: r.font.color.rgb = color
    if align is not None: p.alignment = align
    if space_after is not None: p.paragraph_format.space_after = Pt(space_after)
    return p

def caption(text):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.italic = True; r.font.size = Pt(9); r.font.color.rgb = GRAY
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(10)
    p.paragraph_format.space_before = Pt(3)

def figure(path, cap):
    doc.add_picture(str(path), width=Cm(16.0))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption(cap)

# footer page number
p = sec.footer.paragraphs[0]
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run()
f1 = OxmlElement("w:fldChar"); f1.set(qn("w:fldCharType"), "begin")
it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = "PAGE"
f2 = OxmlElement("w:fldChar"); f2.set(qn("w:fldCharType"), "end")
run._r.append(f1); run._r.append(it); run._r.append(f2)
run.font.size = Pt(9); run.font.color.rgb = GRAY

# ---------------- title block ----------------
para("Ten Games of Signal and Noise: What Manchester United's 18th Place Really Means",
     bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, size=16, space_after=2)
para("Comparative analysis of 2025/26 and the first ten 2026/27 Premier League matches",
     italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, size=10.5, color=GRAY, space_after=2)
para("AMA2233 Data Analytics and Visualization · Course project · Data extracted 18 November 2026",
     align=WD_ALIGN_PARAGRAPH.CENTER, size=9, color=GRAY, space_after=10)

# ---------------- abstract ----------------
p = doc.add_paragraph()
r = p.add_run("Abstract. ")
r.bold = True
p.add_run(
    f"After ten matches of 2026/27, Manchester United sit 18th with {int(m2['actual'])} points — "
    f"fewer than half the {int(m1['2025/26']['pts'])} points they had at the same stage of 2025/26. "
    "This paper decomposes that decline into process and noise. (i) The decline is real on a "
    "like-for-like basis: over the first ten rounds, goals scored fell from "
    f"{m1['2025/26']['gf']} to {m1['2026/27']['gf']}, goals conceded rose from "
    f"{m1['2025/26']['ga']} to {m1['2026/27']['ga']}, and shot conversion halved. "
    f"(ii) The league table overstates the decline: from United's chance quality ({m2['xgpg']} xG per match, "
    f"the league's {m2['xg_rank']}th-best attack, against {m2['xgApg']} xGA, the {m2['xgA_rank']}th-worst "
    f"defence), an independent-Poisson expected-points model puts United on {m2['xpts']} points — the "
    f"{m2['rank_xpts']}th-best side of this ten-match window, not the {m2['rank_actual']}th — with a shortfall of "
    f"{m2['resid']} points against chance expectation, the third-largest negative residual in the division. "
    f"(iii) Ten-match tables are informative but imprecise: across {m5['n']} team-seasons (2021/22–2025/26), "
    f"points after ten rounds correlate {m5['rho']} (Spearman) with final points — yet three clubs with "
    "identical 17-point starts finished 3rd, 10th "
    "and 17th. The five-point gap between actual and expected points sits alongside goal-level residuals of "
    f"{m2['finishing']} goals (finishing) and +{m2['defdev']} (defensive outcomes). The findings argue "
    "against panic decisions based on a ten-match table, while showing that United's underlying level — "
    "roughly 12th over these ten matches — is itself a real decline that deserves a response."
)
p.paragraph_format.space_after = Pt(8)

# ---------------- 1 Introduction ----------------
doc.add_heading("1. Introduction", level=1)
para(
    "A league table is a point estimate built from a noisy sample. After ten rounds of 2026/27, "
    "Manchester United's estimate is alarming: 18th place, eight points, three from safety. The natural "
    "question — what explains the collapse from last season's 71 points and third place — is, in its full "
    "form, unanswerable with team-level data alone: it would require counterfactuals about squads, "
    "injuries and tactics that match files do not contain. This paper asks instead the questions that "
    "can be answered, and that decision-makers actually need: (i) is the decline real once the comparison "
    "is made fairly; (ii) is 18th a fair description of the underlying level of play; and (iii) how much "
    "evidence is a ten-match table in the first place?"
)
para(
    "Three hypotheses are tested. H1: United's like-for-like results declined relative to the same window "
    "of the previous season. H2: the ranking understates United's chance-based level, i.e. their expected "
    f"rank differs from their actual rank. H3: ten-match results are informative but imprecise predictors "
    "of final standing. All three are supported below, and together they replace the alarmist reading of "
    "the table with a calibrated one: a real, moderate decline, amplified by one of the division's three "
    "largest negative residuals — plausibly luck, plausibly skill."
)

# ---------------- 2 Data and methods ----------------
doc.add_heading("2. Data and methods", level=1)
doc.add_heading("2.1 Related work", level=2)
para(
    "Expected-goals models estimate shot-level scoring probabilities and aggregate them into a measure of "
    "chance quality; their outputs are provider-dependent, because the inputs and definitions built into "
    "the model differ across providers (Anzer & Bauer, 2021; Bandara et al., 2024). Holzmeister and "
    "Johannesson (2025) decompose deviations between actual and expected performance in European football "
    "into persistent skill differences and match-level variation, showing that such residuals cannot "
    "simply be equated with luck. Both points structure the present analysis: xG is treated as one "
    "provider's estimate and is used within a single season, and the gap between actual and expected "
    "points is reported as a residual whose interpretation is discussed rather than assumed."
)
doc.add_heading("2.2 Data", level=2)
para(
    "Match-level CSVs for six Premier League seasons (2021/22–2026/27) were downloaded from "
    "Football-Data.co.uk; the five completed seasons contain 380 matches each and the current season 100 "
    "(21 August to 8 November 2026). Each match was expanded into home and away team rows, with points "
    "assigned 3/1/0 from the final score. Shot totals, shots on target and — for the current season only — "
    "expected goals (xG, provider estimates) are retained. The same-window design compares each club's "
    "first ten rounds within a season, so no comparison mixes a ten-match window with a 38-match one. "
    "Raw files, a reproducible notebook, and a source register accompany this report."
)
doc.add_heading("2.3 Expected points", level=2)
para(
    "For every current-season match, goals are modelled as independent Poisson draws with rates equal to "
    "each team's xG. The win and draw probabilities follow from the full score matrix, and expected points "
    "are xPts = 3·P(win) + P(draw). League position is never used as a predictor. Across the division the "
    f"aggregated totals match closely: mean xPts is {m2['league_mean_xpts']} against "
    f"{m2['league_mean_actual']} actual points — a sanity check on the league-wide mean, not a full "
    "calibration test. The model assumes independence of the two scorelines, a limitation discussed in "
    "Section 5. xG exists only in the current-season file, so the decomposition is within-season."
)
doc.add_heading("2.4 Historical benchmark and inference", level=2)
para(
    f"The five completed seasons supply {m5['n']} team-seasons. Each club's points after ten rounds are "
    "compared with its final points and rank. Association is summarised by Pearson and Spearman "
    "correlations; a 9,999-iteration permutation test guards the Spearman coefficient against chance. "
    "A schedule-strength proxy — the average points per match of each club's opponents — is computed for "
    "the current season."
)

# ---------------- 3 Results ----------------
doc.add_heading("3. Results", level=1)

doc.add_heading("3.1 A real decline, on a like-for-like basis (H1 supported)", level=2)
para(
    f"United took {int(m1['2025/26']['pts'])} points from their first ten matches in 2025/26 (6th place) "
    f"and {int(m1['2026/27']['pts'])} from the same ten rounds in 2026/27 (18th) — a 53% drop in points "
    "rate over identical windows. The decline spans both directions of play: goals scored fell from "
    f"{m1['2025/26']['gf']} to {m1['2026/27']['gf']} and goals conceded rose from "
    f"{m1['2025/26']['ga']} to {m1['2026/27']['ga']}. Shot volume actually rose "
    f"({m1['2025/26']['shots']} to {m1['2026/27']['shots']} in total) while shots on target were identical "
    f"({m1['2025/26']['sot']}), so the collapse is in conversion: {m1['2025/26']['conv']*100:.1f}% of shots "
    f"became goals last season against {m1['2026/27']['conv']*100:.1f}% now. The decline is real; H1 holds."
)
figure(FIG / "01_same_window.png",
       "Figure 1. Cumulative points over United's first ten matches in 2025/26 and 2026/27, with the "
       "2026/27 league-median pace for reference. Identical windows; a 17-to-8 point drop.")

doc.add_heading("3.2 The table overstates the decline (H2 supported)", level=2)
para(
    f"United's chances have been worth more than their points. With {m2['xgpg']} xG created per match — "
    f"the league's {m2['xg_rank']}th-best attack — against {m2['xgApg']} xGA conceded — the "
    f"{m2['xgA_rank']}th-worst defence — the Poisson model expects {m2['xpts']} points from the ten games, "
    f"not {int(m2['actual'])}. At 1.30 expected points per match, United's ten-match chance-based rank is "
    f"{m2['rank_xpts']}th, not {m2['rank_actual']}th. The shortfall of {m2['resid']} points against chance "
    f"expectation is the third-largest in the division (bottom {m2['resid_percentile']*100:.0f}%). The "
    "profile is coherent: "
    "the attack creates enough, the defence concedes too much, and on top of both, results have lagged "
    "the chances. H2 holds."
)
figure(FIG / "02_actual_vs_expected.png",
       "Figure 2. Actual versus expected points per match, 2026/27 (n = 20). United sit well below the "
       "diagonal: 0.80 actual against 1.30 expected points per match.")

doc.add_heading("3.3 Six places of residual", level=2)
para(
    f"Ranking clubs by the gap between their actual and expected positions, United's twist is "
    f"+{int(m2['twist'])} places — the {int(m2['resid'])}-point shortfall against their chances is worth "
    "six table positions. Only two clubs have larger negative residuals. The point of the figure is "
    "not that United are good; it is that the table, read naively, misprices them by a third of the league."
)
figure(FIG / "03_rank_twist.png",
       "Figure 3. Expected rank (blue) versus actual rank (red) for every club, sorted by residual "
       "(actual minus expected points). United's ten-match chance-based position is six places better than the "
       "table suggests.")

doc.add_heading("3.4 A ten-match table is informative but imprecise (H3 supported)", level=2)
para(
    f"Across {m5['n']} completed team-seasons, points after ten rounds correlate {m5['rho']} (Spearman; "
    f"rank-based {m5['rho_rank']}) with final points — clearly non-chance (p = {m5['p_perm']}, add-one "
    f"corrected over 9,999 permutations) — and R² = {m5['r2']}. The association is strong as football "
    f"associations go, yet far from deterministic: "
    f"the average club moves {m5['mean_abs_move']} places between round ten and round 38, "
    f"{m5['pct_move_ge6']:.0f}% move at least six, and one club moved {m5['max_move']}. The most instructive "
    "comparison is United's own start: in 2025/26, three clubs — Chelsea, Manchester United and Tottenham "
    "— each had 17 points after ten rounds; they finished "
    f"{', '.join(f'{t} {p}' for t, p in trio)} points respectively — 10th, 3rd and 17th. "
    f"An eight-point start is rare and its history is bimodal: among teams starting on 6–10 points "
    f"(n = {m5['slice_n']}), final tallies ranged from {m5['slice_min']} to {m5['slice_max']} points "
    f"(median {m5['slice_median']:.0f}, IQR {m5['slice_q1']:.0f}–{m5['slice_q3']:.0f}) — usually lower "
    "mid-table; but the single club in five seasons to start on exactly eight points finished on 25. "
    "The reasonable reading: relegation is not the statistical favourite, but the uncertainty is real. "
    "H3 holds."
)
figure(FIG / "05_historical_benchmark.png",
       "Figure 4. Points after ten rounds versus final points, 100 team-seasons (2021/22–2025/26). "
       "United's current eight points sit in the shaded band; the bracket shows the final tallies of "
       "teams starting on 6–10 points.")

doc.add_heading("3.5 Where the shortfall accumulated", level=2)
para(
    f"Behind the five-point gap sit two goal-level residuals: United scored {m2['finishing']} goals fewer "
    f"than their chances warrant (finishing) and conceded {m2['defdev']} more than expected (defensive "
    "outcomes). Goals and points are different units — these channels indicate where the gap accumulated; "
    "they do not sum to it. Whether the gap reflects luck, finishing or goalkeeping skill, or model error "
    "cannot be separated here (cf. Holzmeister & Johannesson, 2025). Figure 5 shows the shortfall match "
    "by match: "
    "the worst results concentrated in games where chances exceeded outcomes. Figure 6 accumulates both "
    "series: actual points track expected points for stretches, then diverge permanently after rounds "
    "six to eight, when the finishing and defensive shortfalls compounded. Schedule strength does not "
    f"explain the start: United's opponents average {rob['mu_sos']} points per match against a league "
    f"average of {rob['league_sos']} ({rob['mu_sos_rank']}th-hardest), only marginally above average."
)
figure(FIG / "04_match_by_match.png",
       "Figure 5. United's ten matches: result, chance balance (xG / xGA) and points earned versus "
       "expected. Tiles tinted by result.")
figure(FIG / "06_cumulative_luck.png",
       "Figure 6. Cumulative actual versus expected points. The shaded gap — roughly five points — is "
       "United's shortfall against chance expectation.")

# ---------------- 4 Discussion ----------------
doc.add_heading("4. Discussion", level=1)
para(
    "Three implications follow, of the kind a board or a fanbase faces in a bad run. First, do not manage "
    "on the headline number: an 18th-place reading of a ten-round table overweights noise, and the same "
    "table one year ago would have implied a title race for a club that finished 17th (Tottenham) and a "
    "collapse for one that finished third (United). Second, do not dismiss the run either: a 1.30 "
    "expected-points-per-match pace over these ten games is mid-table, and mid-table is itself a severe "
    "decline from last season's "
    "71-point, third-place campaign. Third, treat the aggregates as hypotheses about where to look rather "
    "than verdicts on personnel. The attack creates the league's fourth-best chances; the problems are "
    "concentrated where chances are conceded (fourth-worst xGA) and converted (conversion halved "
    "year-on-year). These patterns are consistent with defensive-structure and finishing problems — "
    "targets for further scrutiny, not grounds for a rebuild on their own."
)

# ---------------- 5 Limitations ----------------
doc.add_heading("5. Limitations", level=1)
para(
    "The expected-points model assumes independent Poisson scorelines and a fixed K = 12 goal cap; "
    "real scorelines are correlated, so point probabilities are approximate. xG values come from one "
    "provider and are model-dependent; they exist only for the current season, preventing a cross-season "
    "comparison of chance quality. The residual of actual against expected points can reflect luck, "
    "systematic finishing or goalkeeping skill, or provider-model error; it is reported and interpreted "
    "here, never attributed causally. The benchmark uses five completed seasons and treats each "
    "team-season "
    "as one observation, ignoring within-club dependence and era drift, and position ranks share ties. "
    "The schedule-strength proxy is coarse. No player-level, injury, or tactical data are used, so the "
    "mechanisms proposed in the Discussion are hypotheses consistent with the aggregates, not proven "
    "causes. These caveats bound the claim: this paper establishes what ten matches can and cannot say, "
    "not what United will finish."
)

# ---------------- 6 Conclusion ----------------
doc.add_heading("6. Conclusion", level=1)
para(
    f"United's start is worse than last season's — 17 points became eight over identical windows — but "
    f"the league table exaggerates how much worse: the chances were worth {m2['xpts']} points, roughly "
    f"12th over these ten matches, and the missing five points are the third-largest negative residual in "
    "the division. Ten-round "
    "tables are informative but imprecise instruments, and history says an eight-point start ends anywhere "
    "from the low twenties to sixty. The disciplined conclusion: investigate the defence and the "
    "finishing, and refuse to read the table as prophecy."
)

# ---------------- References ----------------
doc.add_heading("References", level=1)
refs = [
    "Football-Data.co.uk. (2026). English Premier League match data, 2021/22–2026/27 [Data sets]. "
    "https://www.football-data.co.uk/england.php",
    "Premier League. (2026). Premier League table 2026/27. "
    "https://www.premierleague.com/en/tables/premier-league/2026-27",
    "Anzer, G., & Bauer, P. (2021). A goal scoring probability model for shots based on synchronized "
    "positional and event data in football (soccer). Frontiers in Sports and Active Living, 3, 624475. "
    "https://doi.org/10.3389/fspor.2021.624475",
    "Bandara, I., Shelyag, S., Rajasegarar, S., Dwyer, D., Kim, E., & Angelova, M. (2024). Predicting goal "
    "probabilities with improved xG models using event sequences in association football. PLOS ONE, "
    "19(10), e0312278. "
    "https://doi.org/10.1371/journal.pone.0312278",
    "Holzmeister, F., & Johannesson, M. (2025). Skills vs. luck: Decomposing deviations from expected "
    "performance in European football leagues. Journal of Sports Economics, 26(8). "
    "https://doi.org/10.1177/15270025251374620",
]
for ref in refs:
    p = doc.add_paragraph(ref)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.left_indent = Cm(0.75)
    p.paragraph_format.first_line_indent = Cm(-0.75)

doc.save(ROOT / "report" / "Academic_Report.docx")
print("saved report; paragraphs:", len(doc.paragraphs), "images:", len(doc.inline_shapes))
