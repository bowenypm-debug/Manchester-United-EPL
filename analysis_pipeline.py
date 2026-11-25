# %% [md]
# # Manchester United: Ten Games of Signal and Noise
# **AMA2233 Data Analytics and Visualization · course project**
#
# This notebook rebuilds every figure and number in the report from raw match CSVs.
# Run all cells from the project root. Requirements: Python 3.10+, pandas, numpy, matplotlib.
#
# Modules: M1 same-window comparison · M2 expected points (xPts) · M3 rank twist ·
# M4 match-by-match · M5 historical benchmark · M6 cumulative residual. All figures go to `figures/`.

# %%
import json, math, os, tempfile
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
os.environ.setdefault("MPLCONFIGDIR", tempfile.mkdtemp(prefix="mpl_"))
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path.cwd()
# run from the project root; if launched from notebooks/ (e.g. via nbconvert), step up one level
if not (ROOT / "data").exists() and (ROOT.parent / "data").exists():
    ROOT = ROOT.parent
RAW  = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
FIG  = ROOT / "figures"
PROC.mkdir(exist_ok=True); FIG.mkdir(exist_ok=True)

# ---- unified design system -------------------------------------------------
MU   = "#C8102E"   # Manchester United red
INK  = "#1F2937"   # near-black ink
GRAY = "#7A8694"   # neutral gray
LGRAY= "#B7C0CA"
BLUE = "#2563EB"   # expected / process
GREEN= "#2E7D4F"
AMBER= "#B45309"
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 11.5, "axes.titleweight": "bold", "axes.titlecolor": INK,
    "axes.labelcolor": INK, "text.color": INK, "axes.edgecolor": "#D1D5DB",
    "axes.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": "#E5E7EB", "grid.linewidth": 0.7,
    "axes.axisbelow": True, "xtick.color": INK, "ytick.color": INK,
    "figure.facecolor": "white", "savefig.facecolor": "white",
    "figure.dpi": 110, "savefig.dpi": 220,
    "legend.frameon": False,
})

SEASONS = [("2122","2021/22"), ("2223","2022/23"), ("2324","2023/24"),
           ("2425","2024/25"), ("2526","2025/26"), ("2627","2026/27")]
CURRENT   = "2026/27"
COMPLETED = [s for _, s in SEASONS if s != CURRENT]
MUTEAM    = "Man United"

# %% [md]
# ## Load and reshape
# Six seasons from Football-Data.co.uk (raw CSVs in `data/raw/`). Each match is expanded
# into home and away team rows; points are 3/1/0 from the final score.

# %%
def load(path, season):
    d = pd.read_csv(path, encoding="latin1")
    d = d.dropna(subset=["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG"]).copy()
    d["Date"] = pd.to_datetime(d.Date, dayfirst=True)
    d["Season"] = season
    d["HomePoints"]  = np.select([d.FTHG > d.FTAG,  d.FTHG == d.FTAG], [3, 1], 0)
    d["AwayPoints"]  = np.select([d.FTAG > d.FTHG,  d.FTAG == d.FTHG], [3, 1], 0)
    return d

def expand(d):
    rows = []
    for _, r in d.iterrows():
        for side in ("H", "A"):
            oth = "A" if side == "H" else "H"
            t_col = "HomeTeam" if side == "H" else "AwayTeam"
            o_col = "AwayTeam" if side == "H" else "HomeTeam"
            rows.append({
                "Date": r.Date.date().isoformat(),
                "Season": r.Season,
                "Team": r[t_col], "Opponent": r[o_col],
                "Venue": "Home" if side == "H" else "Away",
                "GF": r[f"FT{side}G"], "GA": r[f"FT{oth}G"],
                "Points": r[f"{side}omePoints"] if side == "H" else r[f"{side}wayPoints"],
                "Shots": r.get(f"{side}S"), "SOT": r.get(f"{side}ST"),
                "xG": r.get(f"{side}xG"), "xGA": r.get(f"{oth}xG"),
            })
    df = pd.DataFrame(rows)
    for c in ["GF", "GA", "Points", "Shots", "SOT", "xG", "xGA"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

match = pd.concat([expand(load(RAW / f"football_data_{k}_E0.csv", s)) for k, s in SEASONS],
                  ignore_index=True).sort_values(["Season", "Date", "Team"])
for c in ["GF", "GA", "Points", "Shots", "SOT", "xG", "xGA"]:
    match[c] = pd.to_numeric(match[c], errors="coerce")
match.to_csv(PROC / "team_match.csv", index=False)

team = match.groupby(["Season", "Team"]).agg(
    MP=("Points", "size"), Pts=("Points", "sum"),
    W=("Points", lambda s: int((s == 3).sum())),
    D=("Points", lambda s: int((s == 1).sum())),
    GF=("GF", "sum"), GA=("GA", "sum"), Shots=("Shots", "sum"), SOT=("SOT", "sum"),
    CleanSheets=("GA", lambda s: int((s == 0).sum())),
    xG=("xG", "sum"), xGA=("xGA", "sum")).reset_index()
for c in ["Pts", "GF", "GA", "Shots", "SOT", "xG", "xGA"]:
    team[c + "pg"] = team[c] / team.MP
team["L"]  = team.MP - team.W - team.D
team["GD"] = team.GF - team.GA
team["Position"] = team.groupby("Season").Pts.rank(ascending=False, method="min")
team["Conversion"] = team.GF / team.Shots
team["Accuracy"]   = team.SOT / team.Shots
team["Finishing"]  = team.GF - team.xG
team["DefDev"]     = team.GA - team.xGA
team.loc[team.Season != CURRENT, ["xG", "xGA", "xGpg", "xGApg", "Finishing", "DefDev"]] = np.nan
team.to_csv(PROC / "team_season.csv", index=False)

# first-ten aggregate per team-season (same-window comparisons)
def first10(m):
    rows = []
    for (s, t), g in m.groupby(["Season", "Team"]):
        h = g.sort_values("Date").head(10)
        rows.append({"Season": s, "Team": t,
                     "Pts10": h.Points.sum(), "GF10": h.GF.sum(), "GA10": h.GA.sum(),
                     "Shots10": h.Shots.sum(), "SOT10": h.SOT.sum()})
    f = pd.DataFrame(rows)
    f["rank10"] = f.groupby("Season").Pts10.rank(ascending=False, method="min")
    return f

first = first10(match)
team = team.merge(first, on=["Season", "Team"], how="left")
print("seasons/matches:", match.groupby("Season").size().to_dict())

# %% [md]
# ## M1 · Same-window comparison
# Compare Manchester United's first ten matches in 2025/26 against the first ten in
# 2026/27 — identical windows, so the comparison is not distorted by season length.

# %%
mu10 = match[(match.Team == MUTEAM)].copy()
mu10["round"] = mu10.groupby("Season").cumcount() + 1
mu10 = mu10[mu10["round"] <= 10].sort_values(["Season", "round"])

m1 = {}
for s in ["2025/26", "2026/27"]:
    g = mu10[mu10.Season == s]
    m1[s] = {
        "pts": int(g.Points.sum()), "gf": int(g.GF.sum()), "ga": int(g.GA.sum()),
        "shots": int(g.Shots.sum()), "sot": int(g.SOT.sum()),
        "conv": float(g.GF.sum() / g.Shots.sum()),
    }
# league median pace, 2026/27 (reference line)
cur = match[match.Season == CURRENT].copy()
cur["round"] = cur.groupby("Team").cumcount() + 1
sub = cur[cur["round"] <= 10].sort_values(["Team", "round"]).copy()
sub["cump"] = sub.groupby("Team").Points.cumsum()
pace = sub.groupby("round").cump.median()

fig, ax = plt.subplots(figsize=(7.0, 4.2))
ax.plot(pace.index, pace.values, ls="--", color=LGRAY, lw=1.6,
        label="league median pace, 2026/27")
d25 = mu10[mu10.Season == "2025/26"].sort_values("round")
d26 = mu10[mu10.Season == "2026/27"].sort_values("round")
ax.plot(d25["round"], d25.Points.cumsum(),
        "o-", color=GRAY, lw=2.4, ms=5.5, label="2025/26 · first ten: 17 pts, 6th")
ax.plot(d26["round"], d26.Points.cumsum(),
        "o-", color=MU, lw=2.8, ms=6, label="2026/27 · first ten: 8 pts, 18th")
ax.annotate("17", (10.15, 17), color=GRAY, fontweight="bold", va="center")
ax.annotate("8",  (10.15,  8), color=MU,   fontweight="bold", va="center")
ax.set(xlabel="Match round", ylabel="Cumulative points",
       title="The same ten matches, one year apart", ylim=(0, 21), xlim=(0.8, 10.6))
ax.legend(loc="upper left")
fig.tight_layout(); fig.savefig(FIG / "01_same_window.png"); plt.close(fig)

# %% [md]
# ## M2 · Expected points from chances
# For every 2026/27 match with xG, model goals as independent Poisson draws with
# λ = xG (home) and xGA (away): P(win) = Σ_{i>j} Pois(i; λ_h)·Pois(j; λ_a).
# Expected points xPts = 3·P(win) + P(draw). League position is never used as a predictor.

# %%
def pois(k, lam):
    return math.exp(-lam) * lam ** k / math.factorial(k)

def match_xpts(lh, la, K=12):
    pw = pd_ = 0.0
    for i in range(K):
        for j in range(K):
            p = pois(i, lh) * pois(j, la)
            if i > j:   pw  += p
            elif i == j: pd_ += p
    return 3 * pw + pd_

curm = cur.dropna(subset=["xG", "xGA"]).copy()
curm["xPts"] = [match_xpts(r.xG, r.xGA) for r in curm.itertuples()]
xrow = curm.groupby("Team").agg(Pts=("Points", "sum"), xPts=("xPts", "sum"),
                                xG=("xG", "sum"), xGA=("xGA", "sum")).reset_index()
xrow["resid"]  = xrow.Pts - xrow.xPts   # actual − xPts: residual vs the xG/Poisson model, not necessarily luck
xrow["rank_actual"] = xrow.Pts.rank(ascending=False, method="min")
xrow["rank_xPts"]   = xrow.xPts.rank(ascending=False, method="min")
xrow["twist"]  = xrow.rank_actual - xrow.rank_xPts     # positive = worse than chance-based rank
xrow["Ptspg"]  = xrow.Pts / 10
xrow["xPtspg"] = xrow.xPts / 10

mu_x = xrow[xrow.Team == MUTEAM].iloc[0]
resid_rank = (xrow.resid <= mu_x.resid).sum()          # teams with residual ≤ MU's (incl. MU)
m2 = {
    "actual": float(mu_x.Pts), "xpts": float(round(mu_x.xPts, 1)),
    "resid": float(round(mu_x.resid, 1)),
    "rank_actual": int(mu_x.rank_actual), "rank_xpts": int(mu_x.rank_xPts),
    "twist": int(mu_x.twist),
    "xgpg": float(round(mu_x.xG / 10, 2)), "xgApg": float(round(mu_x.xGA / 10, 2)),
    "xg_rank": int(xrow.xG.rank(ascending=False)[xrow.Team == MUTEAM].iloc[0]),
    "xgA_rank": int(xrow.xGA.rank(ascending=False)[xrow.Team == MUTEAM].iloc[0]),
    "resid_percentile": float(round(resid_rank / len(xrow), 2)),
    "league_mean_xpts": float(round(xrow.xPts.mean(), 1)),
    "league_mean_actual": float(round(xrow.Pts.mean(), 1)),
}
mu_fin = curm[curm.Team == MUTEAM]
m2["finishing"] = float(round((mu_fin.GF - mu_fin.xG).sum(), 2))
m2["defdev"]    = float(round((mu_fin.GA - mu_fin.xGA).sum(), 2))

fig, ax = plt.subplots(figsize=(7.2, 4.8))
ax.scatter(xrow.xPtspg, xrow.Ptspg, s=42, color=LGRAY, zorder=2,
           label="other clubs")
ax.scatter(mu_x.xPtspg, mu_x.Ptspg, s=110, color=MU, zorder=3, label="Man United")
lo = min(xrow.xPtspg.min(), xrow.Ptspg.min()) - 0.18
hi = max(xrow.xPtspg.max(), xrow.Ptspg.max()) + 0.18
ax.plot([lo, hi], [lo, hi], "--", color=GRAY, lw=1.3, zorder=1,
        label="parity (points = chances)")
# team labels placed at verified non-colliding positions
for t, x, y in [("Arsenal", 1.72, 2.78), ("Brighton", 1.75, 2.32), ("Man City", 1.92, 1.92),
                ("Nott'm Forest", 1.75, 0.80), ("Crystal Palace", 1.05, 0.62)]:
    ax.annotate(t, (x, y), fontsize=8.5, color=INK, ha="left", va="center")
ax.annotate("Man United", (0.98, 0.55), color=MU, fontweight="bold",
            fontsize=8.5, ha="left", va="center")
ax.set(xlabel="Expected points per match (xPts from xG)",
       ylabel="Actual points per match",
       title="Actual vs expected points per match, 2026/27",
       xlim=(lo, hi), ylim=(lo, hi))
ax.legend(loc="lower right", fontsize=8.5)
fig.tight_layout(); fig.savefig(FIG / "02_actual_vs_expected.png"); plt.close(fig)

# %% [md]
# ## M3 · Rank twist
# How many places does the residual (actual − xPts) move each club relative to its chance-based
# rank? Sorted so the largest negative residuals sit on top.

# %%
SHORT = {"Arsenal": "Arsenal", "Aston Villa": "A. Villa", "Bournemouth": "Bournemouth",
         "Brentford": "Brentford", "Brighton": "Brighton", "Burnley": "Burnley",
         "Chelsea": "Chelsea", "Crystal Palace": "C. Palace", "Coventry": "Coventry",
         "Everton": "Everton", "Fulham": "Fulham", "Hull": "Hull", "Ipswich": "Ipswich",
         "Leeds": "Leeds", "Liverpool": "Liverpool", "Man City": "Man City",
         "Man United": "Man United", "Newcastle": "Newcastle", "Nott'm Forest": "N. Forest",
         "Sunderland": "Sunderland", "Tottenham": "Tottenham", "West Ham": "West Ham",
         "Wolves": "Wolves"}
x3 = xrow.sort_values("twist", ascending=False)
fig, ax = plt.subplots(figsize=(7.0, 5.2))
y = np.arange(len(x3))
for yi, r in enumerate(x3.itertuples()):
    color = MU if r.Team == MUTEAM else (BLUE if r.twist > 0 else LGRAY)
    ax.plot([r.rank_xPts, r.rank_actual], [yi, yi], "-", color=color, lw=2.4,
            solid_capstyle="round", alpha=0.9)
    ax.plot(r.rank_xPts, yi, "o", ms=6, color=BLUE, alpha=0.9)
    ax.plot(r.rank_actual, yi, "o", ms=6, color=color, alpha=0.9)
    ax.text(21.0, yi, SHORT.get(r.Team, r.Team), fontsize=8.6, va="center",
            fontweight="bold" if r.Team == MUTEAM else "normal",
            color=MU if r.Team == MUTEAM else INK)
ax.axvline(1, color=GRAY, lw=0.6, alpha=0.4)
ax.annotate("six places apart", xy=(15, y[x3.Team == MUTEAM][0]), xytext=(10.2, y[x3.Team == MUTEAM][0] + 1.6),
            color=MU, fontweight="bold", fontsize=9,
            arrowprops=dict(arrowstyle="->", color=MU, lw=1.1))
ax.invert_yaxis(); ax.invert_xaxis()
ax.set(xlabel="League position  (1 = top)", ylabel="",
       title="Actual vs expected rank — where the residual moved the table",
       xlim=(23.8, 0.5))
ax.set_yticks([])
fig.tight_layout(); fig.savefig(FIG / "03_rank_twist.png"); plt.close(fig)

# %% [md]
# ## M4 · Match by match
# United's ten matches: result, chance balance (xG / xGA) and points expected vs earned.
# Tile background is tinted by the actual result.

# %%
CODES = {"Arsenal": "ARS", "Aston Villa": "AVL", "Bournemouth": "BOU", "Brentford": "BRE",
         "Brighton": "BHA", "Burnley": "BUR", "Chelsea": "CHE", "Crystal Palace": "CRY",
         "Coventry": "COV", "Everton": "EVE", "Fulham": "FUL", "Hull": "HUL",
         "Ipswich": "IPS", "Leeds": "LEE", "Liverpool": "LIV", "Man City": "MCI",
         "Man United": "MUN", "Newcastle": "NEW", "Nott'm Forest": "NFO",
         "Sunderland": "SUN", "Tottenham": "TOT", "West Ham": "WHU", "Wolves": "WOL"}
def code(t): return CODES.get(t, t[:3].upper())

games = mu_fin.sort_values("Date")
TINTS = {"W": "#EDF6EE", "D": "#F6F3E8", "L": "#FAEDED"}
fig, axes = plt.subplots(2, 5, figsize=(7.6, 4.6))
for ax, g in zip(axes.flat, games.itertuples()):
    res = "W" if g.GF > g.GA else ("D" if g.GF == g.GA else "L")
    ax.set_facecolor(TINTS[res])
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values(): sp.set_color("#D8DDE3")
    ax.set_title(f"R{g.round:.0f} · {code(g.Opponent)} ({'H' if g.Venue == 'Home' else 'A'})",
                 fontsize=8.2, color=INK, pad=3)
    ax.text(0.08, 0.56, f"{int(g.GF)}–{int(g.GA)}", fontsize=13, fontweight="bold",
            color=INK, va="center", transform=ax.transAxes)
    ax.text(0.96, 0.56, f"{int(g.Points)} pts", fontsize=9.5, fontweight="bold", ha="right",
            va="center", transform=ax.transAxes, color=GREEN if res == "W" else (AMBER if res == "D" else MU))
    ax.text(0.08, 0.14, f"xG {g.xG:.1f} · xGA {g.xGA:.1f} · xPts {g.xPts:.1f}",
            fontsize=7.8, color=GRAY, transform=ax.transAxes)
fig.suptitle("Ten matches: results vs chances · Man United, 2026/27", fontsize=11.5,
             fontweight="bold", color=INK)
fig.tight_layout(rect=[0, 0, 1, 0.94])
fig.savefig(FIG / "04_match_by_match.png"); plt.close(fig)

# %% [md]
# ## M5 · Historical benchmark
# Across five completed seasons (100 team-seasons): how much does a ten-match table tell
# us about the final one? Where does an eight-point start usually end up?

# %%
bench = team[team.Season.isin(COMPLETED)][["Season", "Team", "Pts10", "Pts", "rank10", "Position"]].dropna(subset=["Pts10"])
bench = bench.rename(columns={"Pts": "Pts38", "Position": "rank38"})
bench["move"] = bench.rank10 - bench.rank38

def spearman(a, b): return pd.Series(a).rank().corr(pd.Series(b).rank())
rho = spearman(bench.Pts10, bench.Pts38)
rho_rank = spearman(bench.rank10, bench.rank38)
r   = bench.Pts10.corr(bench.Pts38)
slope, intercept = np.polyfit(bench.Pts10, bench.Pts38, 1)

# permutation test with add-one correction: p = (count + 1) / (n_perm + 1)
N_PERM = 9999
rng = np.random.default_rng(7)
perm = np.array([spearman(rng.permutation(bench.Pts10.values), bench.Pts38) for _ in range(N_PERM)])
p_perm = (int((np.abs(perm) >= abs(rho)).sum()) + 1) / (N_PERM + 1)

slice6_10 = bench[(bench.Pts10 >= 6) & (bench.Pts10 <= 10)]
at8 = bench[bench.Pts10 == 8]
m5 = {
    "n": int(len(bench)), "rho": float(round(rho, 3)), "rho_rank": float(round(rho_rank, 3)),
    "r": float(round(r, 3)), "r2": float(round(r ** 2, 3)),
    "p_perm": p_perm,
    "mean_abs_move": float(round(bench.move.abs().mean(), 1)),
    "pct_move_ge6": float(round((bench.move.abs() >= 6).mean() * 100)),
    "max_move": int(bench.move.abs().max()),
    "slice_n": int(len(slice6_10)),
    "slice_median": float(slice6_10.Pts38.median()),
    "slice_q1": float(slice6_10.Pts38.quantile(0.25)),
    "slice_q3": float(slice6_10.Pts38.quantile(0.75)),
    "slice_min": int(slice6_10.Pts38.min()), "slice_max": int(slice6_10.Pts38.max()),
    "at8_finals": sorted(at8.Pts38.astype(int).tolist()),
}
trio = bench[(bench.Season == "2025/26") & (bench.Pts10 == 17)]

fig, ax = plt.subplots(figsize=(7.0, 4.5))
ax.scatter(bench.Pts10, bench.Pts38, s=26, color=LGRAY, alpha=0.65, zorder=2)
xs = np.linspace(bench.Pts10.min(), bench.Pts10.max(), 50)
ax.plot(xs, slope * xs + intercept, color=GRAY, lw=1.4, zorder=3)
ax.text(0.03, 0.93, f"ρ (points) = {rho:.2f} · ρ (rank) = {rho_rank:.2f} · R² = {r**2:.2f} "
        f"(n = {len(bench)} team-seasons)",
        transform=ax.transAxes, fontsize=7.6, va="top", color=INK)
ax.axvspan(7.4, 8.6, color=MU, alpha=0.07, zorder=1)
ax.axvline(8, color=MU, lw=1.2, alpha=0.7)
ax.text(8.1, 66, "Man United 2026/27:\n8 points", color=MU, fontsize=8,
        fontweight="bold", ha="left", va="center")
for r_ in trio.itertuples():
    ax.annotate(r_.Team, (r_.Pts10 + 0.18, r_.Pts38), fontsize=8, color=INK,
                ha="left", va="center")
ax.annotate("same 17-point start, 2025/26:\nChelsea 52 · Man United 71 · Tottenham 41",
            (17, 41), xytext=(9.2, 30.5), fontsize=8.4, color=AMBER,
            arrowprops=dict(arrowstyle="->", color=AMBER, lw=0.9))
# bracket for the 6–10 point slice
bx = 27.2
ax.plot([bx, bx], [m5["slice_min"], m5["slice_max"]], color=GRAY, lw=1.1)
for v in [m5["slice_min"], m5["slice_median"], m5["slice_max"]]:
    ax.plot([bx - 0.35, bx], [v, v], color=GRAY, lw=0.9)
    ax.text(bx - 0.55, v, f"{v:.0f}", fontsize=8, color=GRAY, va="center", ha="right")
ax.text(bx + 0.25, (m5["slice_min"] + m5["slice_max"]) / 2,
        f"final points,\nteams with 6–10\nafter ten (n = {m5['slice_n']})",
        fontsize=7.6, color=GRAY, va="center")
ax.set(xlabel="Points after ten matches", ylabel="Final points (38 matches)",
       title="What an eight-point start has meant — 2021/22 to 2025/26",
       xlim=(0, 29.5), ylim=(15, 100))
fig.tight_layout(); fig.savefig(FIG / "05_historical_benchmark.png"); plt.close(fig)

# %% [md]
# ## M6 · Cumulative residual
# United's actual points against the points their chances deserved, accumulated match by
# match. The shaded gap is the shortfall against the chance model — not a direct measure of luck.

# %%
gseq = games.sort_values("Date").reset_index(drop=True)
fig, ax = plt.subplots(figsize=(7.0, 4.2))
x = np.arange(1, len(gseq) + 1)
ax.plot(x, gseq.xPts.cumsum(), "-", color=BLUE, lw=2.2, label="expected points (xPts)")
ax.plot(x, gseq.Points.cumsum(), "-", color=MU, lw=2.8, label="actual points")
ax.fill_between(x, gseq.Points.cumsum(), gseq.xPts.cumsum(), color=MU, alpha=0.10)
ax.annotate("13.0", (10.2, gseq.xPts.sum()), color=BLUE, fontweight="bold", va="center")
ax.annotate("8", (10.2, gseq.Points.sum()), color=MU, fontweight="bold", va="center")
gap_y = gseq.xPts.cumsum().iloc[5] - 0.6
ax.annotate("≈ five points below expectation", (6.3, gap_y), xytext=(1.1, 4.4),
            color=MU, fontsize=8.8, fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=MU, lw=1.0))
ax.text(0.55, 0.04, "goal-level channels (separate units):\nfinishing −3.4 · defensive +1.2 goals",
        transform=ax.transAxes, fontsize=7.6, color=GRAY, va="bottom", ha="left")
ax.set(xlabel="Match round (2026/27)", ylabel="Cumulative points",
       title="Cumulative actual vs expected points · Man United, 2026/27",
       xlim=(0.8, 10.6), ylim=(0, 15.5))
ax.legend(loc="upper left")
fig.tight_layout(); fig.savefig(FIG / "06_cumulative_luck.png"); plt.close(fig)

# %% [md]
# ## Robustness
# Simple schedule-strength proxy: average points per match of each club's opponents
# (including games against United). A permutation test guards the benchmark correlation.

# %%
opp_pp = team[team.Season == CURRENT].set_index("Team").Ptspg
curm2 = curm.copy()
sos = curm2.groupby("Team")["Opponent"].apply(lambda s: s.map(opp_pp).mean()).sort_values(ascending=False)
m_rob = {"mu_sos": float(round(sos[MUTEAM], 2)), "league_sos": float(round(sos.mean(), 2)),
         "mu_sos_rank": int(sos.rank(ascending=False)[MUTEAM]),
         "spearman_perm_p": p_perm}

print("M1", json.dumps(m1, indent=1))
print("M2", json.dumps(m2, indent=1))
print("M5", json.dumps(m5, indent=1))
print("ROB", json.dumps(m_rob, indent=1))

# %% [md]
# ## Summary export
# One JSON with every number used in the report and slides, so the two stay in sync.

# %%
summary = {"m1_same_window": m1, "m2_expected_points": m2, "m5_benchmark": m5,
           "robustness": m_rob, "trio_17pts": {
               "teams": [(r.Team, int(r.Pts38)) for r in trio.itertuples()]}}
with open(PROC / "analysis_summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print("figures:", sorted(p.name for p in FIG.glob("*.png")))
