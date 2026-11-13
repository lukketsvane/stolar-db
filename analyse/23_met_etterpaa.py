"""23_met_etterpaa.py - utforsking ETTER at den tredje prøva er opna. Endrar ingen dom.

Spørsmål: (1) Kvifor fekk ingen armstol både sete- og armhøgd? Er det katalogen eller tolkinga?
(2) Kva krakkar gjev den store spreiinga i M1, og kva for slag krakkar er dei?

  python analyse/23_met_etterpaa.py      Ut: analyse/forsegla3/ETTERPAA.json
"""
import collections, csv, importlib.util, json, os, re, sys
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
HER = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("p3", os.path.join(HER, "22_met_prove.py"))
p3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(p3)
csv.field_size_limit(10 ** 8)
F = p3.F
AVD = set(F["M1_krakk"]["utval"]["avdelingar_primaer"])
rx_arm = re.compile(F["M2_armlene"]["utval"]["objektnamn"], re.I)
rx_krakk = re.compile(F["M1_krakk"]["utval"]["objektnamn"], re.I)

arm_merke = collections.Counter(); arm_har = collections.Counter(); arm_dome = []
krakk = []
with open(p3.P_CSV, encoding="utf-8-sig", newline="") as f:
    for rad in csv.DictReader(f):
        on = (rad.get("Object Name") or "").strip()
        d = rad.get("Dimensions") or ""
        if rx_arm.search(on) and rad.get("Department") in AVD:
            H, sete, arm = p3.maal(d)
            arm_har[("H" if H else "-") + ("S" if sete else "-") + ("A" if arm else "-")] += 1
            for l, v in p3.segment(d):
                arm_merke[l[:30]] += 1
            if re.search(r"\barms?\b", d, re.I) and len(arm_dome) < 12:
                arm_dome.append(d[:220])
        if rx_krakk.search(on) and rad.get("Department") in AVD:
            H, sete, _ = p3.maal(d)
            h = H if H is not None else sete
            if h is not None:
                krakk.append({"avd": rad["Department"], "namn": on, "tittel": (rad.get("Title") or "")[:60],
                              "aar": rad.get("Object Begin Date"), "h": h, "dims": d[:160]})

hs = np.array([k["h"] for k in krakk])
med = np.median(hs)
ut = {"armstolar_maal_HSA": arm_har.most_common(), "armstolar_merkelappar_topp30": arm_merke.most_common(30),
      "armstolar_med_arm_i_teksten_dome": arm_dome,
      "krakk_n": len(krakk), "krakk_median": round(float(med), 1),
      "krakk_objektnamn": collections.Counter(k["namn"] for k in krakk).most_common(20),
      "krakk_lengst_fraa_medianen": sorted(krakk, key=lambda k: -abs(k["h"] - med))[:16]}
json.dump(ut, open(os.path.join(HER, "forsegla3", "ETTERPAA.json"), "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
print("armstolar H/S/A:", ut["armstolar_maal_HSA"])
print("merkelappar:", ut["armstolar_merkelappar_topp30"][:20])
print("døme med arm:", *ut["armstolar_med_arm_i_teksten_dome"][:6], sep="\n  ")
print("krakk namn:", ut["krakk_objektnamn"][:12])
for k in ut["krakk_lengst_fraa_medianen"]:
    print("  %5.1f %-28s %-40s %s | %s" % (k["h"], k["avd"][:28], (k["namn"] + " / " + k["tittel"])[:40], k["aar"], k["dims"][:90]))
