"""Den forsegla prøva: P1-P4 på Rijksmuseum-stolane, med tersklar frå FORESEIINGAR.json.

Skriptet er skrive og committa FØR dataa er henta. Det skal ikkje endrast etterpå;
avvik blir førte i RESULTAT.json under "avvik".

Køyr:  python analyse/09_forsegla_prove.py
Inn:   analyse/forsegla/rijks_raa.jsonl   Ut: analyse/forsegla/RESULTAT.json
"""
import collections, json, math, os, re, sys
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
ROT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPPE = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROT, "analyse", "forsegla")  # argument berre for sjølvtest
F = json.load(open(os.path.join(MAPPE, "FORESEIINGAR.json"), encoding="utf-8"))
if not F.get("godkjend"):
    sys.exit("Stoppa: føreseiingane er ikkje godkjende.")
P, POP = F["foreseiingar"], F["populasjon"]
rng = np.random.default_rng(20261112)
CM = "300379098"  # Getty AAT: centimeter. Andre einingar blir talde og utelatne.


def maal(rec):
    """(H, B, D, sete) i cm. Del utan namn eller «geheel» = heile stolen; «zitting» = setet."""
    ut = {"height": None, "width": None, "depth": None}; sete = None; ukjend = 0
    for x in rec.get("dimension") or []:
        typ = next((n["@value"] for c in x.get("classified_as", []) for n in c.get("notation", []) if n.get("@language") == "en"), None)
        if typ not in ut:
            continue
        if (x.get("unit") or {}).get("id", "").rsplit("/", 1)[-1] != CM:
            ukjend += 1; continue
        try:
            v = float(str(x.get("value")).replace(",", "."))
        except ValueError:
            continue
        if v <= 0:
            continue
        del_ = " ".join((n.get("content") or "").lower() for n in x.get("identified_by", []))
        if "zitting" in del_:
            if typ == "height" and sete is None:
                sete = v
        elif del_ in ("", "geheel") and ut[typ] is None:
            ut[typ] = v
    return ut["height"], ut["width"], ut["depth"], sete, ukjend


def tittel(rec):
    return " ".join((n.get("content") or "") for n in rec.get("identified_by", []) if n.get("type") == "Name")


def aar(rec):
    t = ((rec.get("produced_by") or {}).get("timespan") or {}).get("begin_of_the_begin") or ""
    m = re.match(r"-?\d{4}", t)
    return int(m.group(0)) if m else None


rcv = lambda x: float(1.4826 * np.median(np.abs(x - np.median(x))) / np.median(x))


def eps2(v, g, minn=10):
    d = collections.defaultdict(list)
    for a, k in zip(v, g):
        if k is not None:
            d[k].append(math.log(a))
    d = {k: x for k, x in d.items() if len(x) >= minn}
    if len(d) < 2:
        return None
    al = np.concatenate([np.array(x) for x in d.values()]); N, k = len(al), len(d)
    ssb = sum(len(x) * (np.mean(x) - al.mean()) ** 2 for x in d.values()); sst = ((al - al.mean()) ** 2).sum()
    return float((ssb - (k - 1) * (sst - ssb) / (N - k)) / sst)


def theil_sen(x, y):
    i, j = np.triu_indices(len(x), 1); dx = x[j] - x[i]; ok = dx != 0
    return float(np.median((y[j] - y[i])[ok] / dx[ok]))


rader, tel = [], collections.Counter()
ute = re.compile(POP["utelukk_tittel_regex"], re.I)
for linje in open(os.path.join(MAPPE, "rijks_raa.jsonl"), encoding="utf-8"):
    rec = json.loads(linje).get("record")
    tel["postar"] += 1
    if not rec:
        tel["tom post"] += 1; continue
    if ute.search(tittel(rec)):
        tel["utelukka på tittel"] += 1; continue
    H, B, D, S, ukjend = maal(rec)
    tel["mål i anna eining"] += ukjend
    g = POP["maal_cm"]
    if not (H and B and D and g["H"][0] <= H <= g["H"][1] and g["B"][0] <= B <= g["B"][1] and g["D"][0] <= D <= g["D"][1]):
        tel["utan gyldige mål"] += 1; continue
    tel["gyldige mål"] += 1
    if not (S and POP["sete_cm"][0] <= S <= POP["sete_cm"][1] and S < H):
        tel["utan truverdig setehøgd"] += 1; continue
    rader.append((H, B, D, S, aar(rec)))

n = len(rader)
print("flyt:", dict(tel), "| til prøving:", n)
res = {"flyt": dict(tel), "n": n, "avvik": []}
if n < POP["minste_n"]:
    res["dom"] = "ikkje avgjerande: for få stolar"
else:
    H, B, D, S = (np.array([r[i] for r in rader], float) for i in range(4))
    R = H - S
    bolk = [None if r[4] is None else r[4] // 50 * 50 for r in rader]
    sp = {k: rcv(v) for k, v in (("sete", S), ("breidd", B), ("djupn", D), ("rygg", R), ("totalhøgd", H))}
    tb = {"sete": eps2(S, bolk), "rygg": eps2(R, bolk)}
    x, y = np.log(H), np.log(S)
    b = theil_sen(x, y)
    bs = [theil_sen(x[k], y[k]) for k in (rng.integers(0, n, n) for _ in range(1000))]
    lo, hi = float(np.quantile(bs, 0.025)), float(np.quantile(bs, 0.975))
    idx = rng.permutation(n); feil = {"fast verdi": [], "fast del av H": [], "potenslov": []}
    for f in np.array_split(idx, 5):
        tr = np.setdiff1d(idx, f)
        feil["fast verdi"] += list(np.abs(S[f] - np.median(S[tr])))
        feil["fast del av H"] += list(np.abs(S[f] - np.median(S[tr] / H[tr]) * H[f]))
        a = np.polyfit(np.log(H[tr]), np.log(S[tr]), 1)
        feil["potenslov"] += list(np.abs(S[f] - np.exp(a[1] + a[0] * np.log(H[f]))))
    mae = {k: float(np.mean(v)) for k, v in feil.items()}
    dom = {
        "P1a": sp["sete"] < min(sp["breidd"], sp["djupn"], sp["rygg"]),
        "P1b": sp["sete"] < P["P1b"]["robust_spreiing_sete_under"],
        "P1c": sp["rygg"] > P["P1c"]["robust_spreiing_rygg_over"],
        "P2a": tb["sete"] is not None and tb["sete"] < P["P2a"]["tidsbolk_del_sete_under"],
        "P2b": tb["rygg"] is not None and tb["rygg"] > P["P2b"]["tidsbolk_del_rygg_over"],
        "P3": b < P["P3"]["stiging_sete_mot_H_under"] and hi < P["P3"]["ovre_grense_under"],
        "P4a": mae["fast verdi"] < mae["fast del av H"],
        "P4b": mae["fast verdi"] - mae["potenslov"] <= P["P4b"]["potenslov_slaar_fast_verdi_med_hogst_cm"],
    }
    res.update(median_sete=float(np.median(S)), spreiing=sp, tidsbolk_del=tb, stiging=[b, lo, hi], snittfeil_cm=mae,
               dom={k: bool(v) for k, v in dom.items()},
               grunnmodell_vinn=bool(lo <= 1 <= hi or mae["fast del av H"] <= mae["fast verdi"]))
    for k, v in res.items():
        if k not in ("flyt", "avvik"):
            print(f"{k}: {v}")
json.dump(res, open(os.path.join(MAPPE, "RESULTAT.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
