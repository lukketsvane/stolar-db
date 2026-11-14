"""43_figurar_studie.py - figurane til Studie A og Studie B2.

  python analyse/43_figurar_studie.py   -> analyse/figurar/png/studie_b2_setet_staar.png, studie_a_typen_forklarer.png
"""
import importlib.util, json, os, sys
import numpy as np

HER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HER, "parallell"))
import felles_p as fp

sys.stdout.reconfigure(encoding="utf-8")
S = fp.figurstil()
plt, FG, DIM, SERIF, MONO = S["plt"], S["FG"], S["DIM"], S["SERIF"], S["MONO"]
UT = os.path.join(HER, "figurar", "png")
os.makedirs(UT, exist_ok=True)
spec = importlib.util.spec_from_file_location("b2", os.path.join(HER, "studie_b2", "prove.py"))
b2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b2)
D = b2.D
RB = json.load(open(os.path.join(HER, "studie_b2", "RESULTAT.json"), encoding="utf-8"))
RA = json.load(open(os.path.join(HER, "studie_a", "RESULTAT.json"), encoding="utf-8"))
pr = lambda v, d=1: ("%.*f" % (d, v)).replace(".", ",")

# ------------------------------------------------------------------ B2: bolkmiddel per akse og museum
AKS = [("logH", "Totalhøgd"), ("logB", "Breidd"), ("logD", "Djupn"), ("logSH_kat", "Setehøgd")]
fig, axs = plt.subplots(4, 2, figsize=(7.4, 8.6), sharex=True, sharey=True)
fig.subplots_adjust(left=0.17, right=0.97, top=0.82, bottom=0.12, hspace=0.12, wspace=0.08)
for c, (mus, mnamn) in enumerate((("VA", "V&A"), ("NM", "Nasjonalmuseet"))):
    idx = np.where(D["museum"] == mus)[0]
    for r, (a, anamn) in enumerate(AKS):
        ax = axs[r, c]
        y = b2.juster_type(b2.AKSAR[a], idx)
        ok = idx[np.isfinite(y[idx])]
        b = np.clip(D["aar"][ok], 1550, 1999) // 50
        gm = y[ok].mean()
        xs, ms, es = [], [], []
        for k in np.unique(b):
            j = ok[b == k]
            if len(j) >= 8:
                xs.append(D["aar"][j].mean())
                ms.append(100 * (np.exp(y[j].mean() - gm) - 1))
                es.append(100 * 1.96 * y[j].std(ddof=1) / np.sqrt(len(j)))
        xs, ms, es = map(np.array, (xs, ms, es))
        ax.axhline(0, color=DIM, lw=0.5, dashes=(3, 3))
        ax.errorbar(xs, ms, yerr=es, color=FG, lw=0.9, marker="o", ms=3.4, capsize=0, elinewidth=0.6, zorder=3)
        ax.set_ylim(-26, 26)
        ax.set_xlim(1540, 2010)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        ax.tick_params(length=2, labelsize=6.5, colors=DIM)
        for lab in ax.get_xticklabels() + ax.get_yticklabels():
            lab.set_family(MONO)
        v = RB["per_museum"][mus][a]
        ax.text(0.98, 0.9, "SD mellom bolkar %s %%" % pr(100 * v["sd_mellom"]), transform=ax.transAxes, ha="right", va="top", family=MONO, fontsize=6.4, color=FG if mus == "VA" else DIM)
        if c == 0:
            ax.set_ylabel(anamn, fontsize=11, rotation=0, ha="right", va="center", labelpad=8)
        if r == 0:
            ax.set_title(mnamn, fontsize=11, loc="left", pad=4)
fig.text(0.04, 0.965, "Setet står stille. Høgda går.", fontsize=23, va="top")
fig.text(0.04, 0.912, "Nivået til kvar formakse i 50-årsbolkar, justert for stoltype, i prosent frå eige snitt.", fontsize=10.4, va="top")
fig.text(0.04, 0.888, "Same skala i alle ruter. Setehøgda flyttar seg minst, totalhøgda mest.", fontsize=10.4, va="top")
d = RB["per_museum"]["VA"]
fig.text(0.04, 0.062, "katalogmål · punkt: bolkmiddel med 95 %% intervall (minst 8 stolar per bolk) · V&A: skilnaden i variansdel mellom bolkar (totalhøgd minus setehøgd) er %s, 95 %% frå %s til %s" % (
    pr(1000 * d["diff_omega_H_minus_sete"], 1) + "e-3", pr(1000 * d["diff_omega_H_minus_sete_ki95"][0], 1) + "e-3", pr(1000 * d["diff_omega_H_minus_sete_ki95"][1], 1) + "e-3"),
    family=MONO, fontsize=5.9, color=DIM)
fig.text(0.04, 0.045, "Nasjonalmuseet: same retning, men kontrollen fann ikkje ein planta effekt av denne storleiken der, så museet står utan dom · forsegla studie B2", family=MONO, fontsize=5.9, color=DIM)
fig.text(0.04, 0.028, "1 377 stolar (V&A 1 009, Nasjonalmuseet 368) · år trekt jamt i dateringsintervallet, suitar trekte på nytt, 1 000 repetisjonar", family=MONO, fontsize=5.9, color=DIM)
fig.savefig(os.path.join(UT, "studie_b2_setet_staar.png"), dpi=230, bbox_inches="tight", pad_inches=0.22)
plt.close(fig)

# ------------------------------------------------------------------ A: unikt bidrag per faktor
ORD = [("type", "Stoltype"), ("stil", "Stil (kuratorstil)"), ("pseudostil", "Pseudostil (stilen året gjev)"), ("tid", "Tid (spline)"),
       ("materiale", "Materiale"), ("teknikk", "Teknikk"), ("region", "Region"), ("museum", "Museum")]
fig, ax = plt.subplots(figsize=(7.4, 5.9))
fig.subplots_adjust(left=0.33, right=0.96, top=0.77, bottom=0.2)
for i, (k, namn) in enumerate(ORD):
    y = len(ORD) - 1 - i
    s = RA["dekomponering"]["samla"]
    if k in s["unik"]:
        lo, hi = s["ki95"][k]
        ax.plot([100 * lo, 100 * hi], [y, y], color=FG, lw=1.0, zorder=2)
        ax.plot(100 * s["unik"][k], y, "o", color=FG, ms=6, zorder=3)
    for mus, mk, kl in (("VA", "o", "white"), ("NM", "s", "white")):
        v = RA["dekomponering"][mus]
        if k in v["unik"]:
            ax.plot(100 * v["unik"][k], y + (0.22 if mus == "VA" else -0.22), mk, mfc=kl, mec=DIM, ms=3.6, mew=0.8, zorder=3)
    ax.axhline(y - 0.5, color="#ededed", lw=0.5)
ax.set_yticks(range(len(ORD)))
ax.set_yticklabels([n for _, n in ORD][::-1], fontsize=10.5)
ax.set_xlim(-0.8, 10.2)
ax.set_ylim(-0.6, len(ORD) - 0.4)
ax.set_xlabel("unikt bidrag til forma, prosentpoeng justert R2", family=MONO, fontsize=6.8, color=DIM)
ax.tick_params(length=2, labelsize=6.8, colors=DIM)
for lab in ax.get_xticklabels():
    lab.set_family(MONO)
for sp in ("top", "right"):
    ax.spines[sp].set_visible(False)
fig.text(0.04, 0.965, "Typen forklarer mest.", fontsize=23, va="top")
fig.text(0.04, 0.905, "Stilen tilfører ikkje meir enn året gjev. Kva forklarer storleiken på stolen (høgd, breidd, djupn)", fontsize=10.4, va="top")
fig.text(0.04, 0.875, "når alle andre faktorar er med? Fylt prikk: alle stolane med 95 % intervall. Ope: V&A (rund) og Nasjonalmuseet (firkant).", fontsize=10.4, va="top")
fig.text(0.04, 0.08, "1 377 stolar · katalogmål: log H, log B, log D · unikt bidrag = auke i justert R2 når faktoren kjem med sist, med alle andre inne", family=MONO, fontsize=5.9, color=DIM)
fig.text(0.04, 0.062, "pseudostil = stilen året åleine gjev (modus blant dei fem næraste stolane i år) · 95 % bootstrap over suitar, 300 trekk · forsegla studie A", family=MONO, fontsize=5.9, color=DIM)
rv = RA["revival"]
fig.text(0.04, 0.044, "nyrokokko (12 stolar) ligg ikkje nærare rokokkoen enn dei samtidige: median avstand %s mot %s, permutasjonsp %s" % (pr(rv["median_avstand_revival"], 2), pr(rv["median_avstand_samtidige"], 2), pr(rv["p_naerare_forbildet"], 2)),
         family=MONO, fontsize=5.9, color=DIM)
fig.savefig(os.path.join(UT, "studie_a_typen_forklarer.png"), dpi=230, bbox_inches="tight", pad_inches=0.22)
print("ferdig")
