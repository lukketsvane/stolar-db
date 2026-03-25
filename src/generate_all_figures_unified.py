"""
STOLAR: Unified figure generation.
All figures in consistent visual style matching the existing figurar/ aesthetic.
Style: warm earth tones, off-white bg, subtle grid, scatter+median, nynorsk.
"""
import csv, math, os
from collections import Counter, defaultdict
import statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

# ================================================================
# GLOBAL STYLE - matches figurar/ aesthetic
# ================================================================
BG = '#faf8f5'
GRID_COL = '#e0dcd5'
TEXT_COL = '#2d2a26'
ACCENT_RED = '#a04030'       # mahogni / highlight
ACCENT_GOLD = '#c49b2a'      # gullsnitt
ACCENT_BLUE = '#4a6fa5'      # dimensjonar / kald
ACCENT_GREEN = '#5a8a5a'     # lokalt tre
ACCENT_BROWN = '#8b6914'     # koloniale tre
ACCENT_GREY = '#8a8a8a'      # metall / nøytral
ACCENT_PINK = '#d4837a'      # industrielt / plast

# Material palette (matching material_river)
MAT_COLORS = {
    'Bøk': '#8B7355', 'Mahogni': '#8B2500', 'Eik': '#DAA520',
    'Nøttetre': '#5C4033', 'Furu': '#C4A882', 'Bjørk': '#E8D5A3',
    'Stål': '#9FB6CD', 'Plast': '#E8A0A0', 'Kryssfiner': '#D2B48C',
    'Aluminium': '#B0C4DE',
}

# Century colors
CENT_COLORS = {
    '1500-talet': '#8B7355', '1600-talet': '#A0522D', '1700-talet': '#CD853F',
    '1800-talet': '#DAA520', '1900-talet': '#9FB6CD', '2000-talet': '#B0C4DE',
}

plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Palatino Linotype', 'Book Antiqua', 'Georgia', 'Times New Roman'],
    'font.size': 9.5,
    'axes.titlesize': 12,
    'axes.titleweight': 'normal',
    'axes.labelsize': 10,
    'axes.linewidth': 0.4,
    'axes.facecolor': BG,
    'axes.edgecolor': '#c0bdb5',
    'axes.grid': True,
    'grid.color': GRID_COL,
    'grid.linewidth': 0.3,
    'grid.alpha': 0.7,
    'figure.facecolor': BG,
    'figure.dpi': 200,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.3,
    'savefig.facecolor': BG,
    'xtick.labelsize': 8.5,
    'ytick.labelsize': 8.5,
    'legend.fontsize': 8,
    'legend.framealpha': 0.9,
    'legend.edgecolor': GRID_COL,
    'lines.linewidth': 1.8,
    'lines.markersize': 4,
    'text.color': TEXT_COL,
    'axes.labelcolor': TEXT_COL,
    'xtick.color': TEXT_COL,
    'ytick.color': TEXT_COL,
})

CSV = "../stolar_db.csv"
FIG = "../texts/fig"
os.makedirs(FIG, exist_ok=True)

rows = []
with open(CSV, encoding="utf-8-sig") as f:
    for r in csv.DictReader(f): rows.append(r)

def sf(v):
    try: x=float(v.replace(",",".")); return x if x>0 else None
    except: return None
def museum(r):
    if "nasjonalmuseet.no" in r.get("Nasjonalmuseet","") or r.get("Objekt-ID","").startswith(("OK-","NMK")):
        return "NMK"
    return "V&A"
def cs(c):
    try: return int(c.split("-")[0])
    except: return 9999

for r in rows:
    r["_m"]=museum(r)
    r["_mats"]=[m.strip() for m in r.get("Materialar","").split(",") if m.strip()]
    r["_c"]=r.get("Hundreår","").strip()
    r["_h"]=sf(r.get("Høgde (cm)",""))
    r["_w"]=sf(r.get("Breidde (cm)",""))
    r["_d"]=sf(r.get("Djupn (cm)",""))
    r["_wt"]=sf(r.get("Estimert vekt (kg)",""))
    r["_style"]=r.get("Stilperiode","").strip()
    r["_nat"]=r.get("Nasjonalitet","").strip()
    try: r["_y"]=int(r.get("Frå år","").strip()); r["_y"]=r["_y"] if r["_y"]>100 else None
    except: r["_y"]=None

main_c = sorted([c for c in set(r["_c"] for r in rows if r["_c"])
                  if c not in ("1200-talet","1300-talet","1400-talet")], key=cs)

# ================================================================
# FIG 1: MAHOGNIENS BOGE (NMK, 25-aars)
# ================================================================
print("Fig 1: Mahogniens boge...")
pd = defaultdict(lambda:{"t":0,"m":0})
for r in rows:
    if r["_m"]!="NMK" or not r["_y"]: continue
    p=(r["_y"]//25)*25; pd[p]["t"]+=1
    if "Mahogni" in r["_mats"]: pd[p]["m"]+=1
ps=sorted(p for p in pd if p>=1600 and pd[p]["t"]>=3)
pcts=[100*pd[p]["m"]/pd[p]["t"] for p in ps]

fig,ax=plt.subplots(figsize=(10,4.5))
ax.fill_between(range(len(ps)), pcts, alpha=0.25, color=ACCENT_RED)
ax.plot(range(len(ps)), pcts, 'o-', color=ACCENT_RED, linewidth=2, markersize=5)
for i,(p,pct) in enumerate(zip(ps,pcts)):
    if pct>=99:
        ax.annotate(f'100 %\n(n={pd[p]["t"]})', (i,pct), textcoords='offset points',
                    xytext=(15,5), fontsize=10, fontweight='bold', color='#5a0000',
                    arrowprops=dict(arrowstyle='->', color='#5a0000', lw=1.5))
    elif pct>40:
        ax.text(i, pct+3, f'{pct:.0f}%', ha='center', fontsize=7.5, color=ACCENT_RED)
ax.set_xticks(range(len(ps)))
ax.set_xticklabels([str(p) for p in ps], rotation=55, ha='right')
ax.set_ylabel('Stolar med mahogni (%)')
ax.set_title('Mahogniens boge: Nasjonalmuseet, 1600-2024 (n=671)')
ax.set_ylim(-3,115)
ax.axhline(50, color=ACCENT_GREY, ls=':', lw=0.5, alpha=0.4)
fig.savefig(f"{FIG}/fig1_mahogni_boge.pdf"); plt.close()

# ================================================================
# FIG 4: JACCARD NMK vs V&A
# ================================================================
print("Fig 4: Jaccard...")
nmk_s,va_s=defaultdict(set),defaultdict(set)
for r in rows:
    if r["_c"] and r["_mats"]:
        (nmk_s if r["_m"]=="NMK" else va_s)[r["_c"]].update(r["_mats"])
jc,jd=[],[]
for c in main_c:
    if nmk_s[c] and va_s[c]:
        inter=nmk_s[c]&va_s[c]; union=nmk_s[c]|va_s[c]
        jc.append(c); jd.append(1-len(inter)/len(union))

fig,ax=plt.subplots(figsize=(7,4))
ax.fill_between(range(len(jc)),jd,alpha=0.15,color=ACCENT_BLUE)
ax.plot(range(len(jc)),jd,'s-',color=ACCENT_BLUE,linewidth=2,markersize=7)
for i,(c,d) in enumerate(zip(jc,jd)):
    ax.text(i, d+0.04, f'{d:.2f}', ha='center', fontsize=8.5, color=ACCENT_BLUE)
ax.set_xticks(range(len(jc))); ax.set_xticklabels(jc, rotation=45, ha='right')
ax.set_ylabel('Jaccard-avstand ($d_J$)')
ax.set_title('Materialkonvergens: NMK vs. V&A')
ax.set_ylim(0,1.05)
ax.text(len(jc)-1.5,0.1,'Konvergens',fontsize=9,color=ACCENT_BLUE,style='italic',ha='center')
fig.savefig(f"{FIG}/fig4_jaccard.pdf"); plt.close()

# ================================================================
# FIG 7: FEATURE IMPORTANCE
# ================================================================
print("Fig 7: Feature importance...")
feats=["Hogde","Breidde","Djupn","Setehogde","Bøk","Buksbom","Mahogni","Silke","Hestetagl","Messing","Eik","Furu"]
imps=[0.197,0.140,0.120,0.110,0.038,0.037,0.036,0.035,0.035,0.023,0.022,0.022]
cols=[ACCENT_BLUE]*4+[ACCENT_BROWN]*8
fig,ax=plt.subplots(figsize=(7,5))
y=np.arange(len(feats)-1,-1,-1)
ax.barh(y,imps,color=cols,edgecolor='white',height=0.6)
for i,(imp,yy) in enumerate(zip(imps,y)):
    ax.text(imp+0.003,yy,f'{imp:.1%}',va='center',fontsize=8.5,color=cols[i])
ax.set_yticks(y); ax.set_yticklabels(feats)
ax.set_xlabel('Feature importance (Random Forest)')
ax.set_title('Kva predikerer stilperiode? (n=469, k=15)')
ax.axhline(7.5, color=GRID_COL, lw=0.8)
ax.text(0.16,10,'DIMENSJONAR',fontsize=9,color=ACCENT_BLUE,fontweight='bold',
        bbox=dict(facecolor=BG,edgecolor=ACCENT_BLUE,boxstyle='round,pad=0.3',alpha=0.9))
ax.text(0.16,4,'MATERIALAR',fontsize=9,color=ACCENT_BROWN,fontweight='bold',
        bbox=dict(facecolor=BG,edgecolor=ACCENT_BROWN,boxstyle='round,pad=0.3',alpha=0.9))
ax.set_xlim(0,0.24)
fig.savefig(f"{FIG}/fig7_feature_importance.pdf"); plt.close()

# ================================================================
# FIG 9: NMK vs V&A HOGDE (dual bars + delta)
# ================================================================
print("Fig 9: NMK vs V&A...")
nmk_h,va_h=defaultdict(list),defaultdict(list)
for r in rows:
    if r["_c"] and r["_h"]:
        (nmk_h if r["_m"]=="NMK" else va_h)[r["_c"]].append(r["_h"])
pc=[c for c in main_c if nmk_h[c] and va_h[c]]
nm=[statistics.mean(nmk_h[c]) for c in pc]
vm=[statistics.mean(va_h[c]) for c in pc]
deltas=[n-v for n,v in zip(nm,vm)]

fig,(ax1,ax2)=plt.subplots(2,1,figsize=(8,6),height_ratios=[3,1.2],sharex=True)
fig.subplots_adjust(hspace=0.05)
x=np.arange(len(pc)); w=0.35
ax1.bar(x-w/2,nm,w,color=ACCENT_BLUE,label='NMK (Noreg)',edgecolor='white')
ax1.bar(x+w/2,vm,w,color=ACCENT_RED,label='V&A (Storbritannia)',edgecolor='white')
for i,(n,v) in enumerate(zip(nm,vm)):
    ax1.text(i-w/2,n+1.5,f'{n:.0f}',ha='center',fontsize=7,color=ACCENT_BLUE)
    ax1.text(i+w/2,v+1.5,f'{v:.0f}',ha='center',fontsize=7,color=ACCENT_RED)
ax1.set_ylabel('Gj.snittleg hogde (cm)')
ax1.set_title('Norske vs. britiske stolar: hogde per hundreaar')
ax1.legend(fontsize=9); ax1.set_ylim(0,130)

dcols=[ACCENT_BLUE if d>0 else ACCENT_RED for d in deltas]
ax2.bar(x,deltas,color=dcols,edgecolor='white',width=0.6)
ax2.axhline(0,color=TEXT_COL,lw=0.6)
for i,d in enumerate(deltas):
    ax2.text(i,d+(2 if d>0 else -3.5),f'{d:+.0f}',ha='center',fontsize=7.5,color=dcols[i],fontweight='bold')
ax2.set_ylabel('$\\Delta$ (cm)'); ax2.set_xticks(x); ax2.set_xticklabels(pc,rotation=45,ha='right')
fig.savefig(f"{FIG}/fig9_nmk_va_hogde.pdf"); plt.close()

# ================================================================
# FIG 10: DOBBELTHEIT
# ================================================================
print("Fig 10: Dobbeltheit...")
local={"Bjørk","Furu","Eik","Ask","Or","Alm","Gran","Bøk","Osp","Lind"}
imp={"Mahogni","Palisander","Ibenholt","Rotting","Teak","Bambus","Silke","Fløyel"}
dc,dp=[],[]
for c in main_c:
    items=[r for r in rows if r["_c"]==c]
    nd=sum(1 for r in items if (set(r["_mats"])&local) and (set(r["_mats"])&imp))
    if items: dc.append(c); dp.append(100*nd/len(items))

fig,ax=plt.subplots(figsize=(7,4))
ax.fill_between(range(len(dc)),dp,alpha=0.2,color=ACCENT_BROWN)
ax.plot(range(len(dc)),dp,'o-',color=ACCENT_BROWN,linewidth=2,markersize=6)
for i,(p,n) in enumerate(zip(dp,dc)):
    if p>1: ax.text(i,p+1,f'{p:.1f}%',ha='center',fontsize=8,color=ACCENT_BROWN)
ax.set_xticks(range(len(dc))); ax.set_xticklabels(dc,rotation=45,ha='right')
ax.set_ylabel('Andel stolar (%)'); ax.set_title('Materiell dobbeltheit: berande lokalt + importert fasade')
ax.set_ylim(0,30)
fig.savefig(f"{FIG}/fig10_dobbeltheit.pdf"); plt.close()

# ================================================================
# FIG 11: H/W PER MATERIALE (boxplot)
# ================================================================
print("Fig 11: H/W per materiale...")
mat_hw=defaultdict(list)
for r in rows:
    if r["_h"] and r["_w"] and r["_w"]>0:
        for m in r["_mats"]: mat_hw[m].append(r["_h"]/r["_w"])
mats_p=["Bjørk","Furu","Eik","Bøk","Mahogni","Kryssfiner","Stål","Plast"]
mdata=[mat_hw[m] for m in mats_p if len(mat_hw[m])>10]
mlabels=[m for m in mats_p if len(mat_hw[m])>10]
mcols=[MAT_COLORS.get(m,ACCENT_GREY) for m in mlabels]

fig,ax=plt.subplots(figsize=(8,4.5))
bp=ax.boxplot(mdata,patch_artist=True,widths=0.55,
              medianprops=dict(color=TEXT_COL,lw=1.5),
              whiskerprops=dict(color=ACCENT_GREY,lw=0.7),
              capprops=dict(color=ACCENT_GREY,lw=0.7),
              flierprops=dict(marker='.',markersize=2,color=ACCENT_GREY,alpha=0.3))
for patch,col in zip(bp['boxes'],mcols):
    patch.set_facecolor(col); patch.set_alpha(0.5); patch.set_edgecolor(col)
phi=(1+math.sqrt(5))/2
ax.axhline(phi,color=ACCENT_GOLD,ls='-.',lw=1.5,label=f'Gullsnitt ($\\varphi$={phi:.2f})')
ax.axhline(1.0,color=ACCENT_GREY,ls=':',lw=0.6,alpha=0.5)
for i,data in enumerate(mdata):
    m=statistics.mean(data)
    ax.text(i+1,0.15,f'{m:.2f}',ha='center',fontsize=7.5,color=mcols[i],fontweight='bold')
ax.set_xticklabels(mlabels,rotation=45,ha='right')
ax.set_ylabel('$H/W$-ratio'); ax.set_title('Kvart materiale dikterer sine proporsjonar')
ax.legend(fontsize=8,loc='upper right'); ax.set_ylim(0,4.5)
fig.savefig(f"{FIG}/fig11_hw_per_material.pdf"); plt.close()

# ================================================================
# FIG 14: DIMENSJONSDRIFT
# ================================================================
print("Fig 14: Dimensjonsdrift...")
ch,cw=defaultdict(list),defaultdict(list)
for r in rows:
    if r["_c"] in main_c:
        if r["_h"]: ch[r["_c"]].append(r["_h"])
        if r["_w"]: cw[r["_c"]].append(r["_w"])
pc14=[c for c in main_c if ch[c]]
hm=[statistics.mean(ch[c]) for c in pc14]
wm=[statistics.mean(cw[c]) for c in pc14]

fig,ax=plt.subplots(figsize=(7,4))
ax.plot(range(len(pc14)),hm,'o-',color=ACCENT_BLUE,lw=2,ms=6,label='Hogde')
ax.plot(range(len(pc14)),wm,'s-',color=ACCENT_RED,lw=2,ms=6,label='Breidde')
for i in range(1,len(hm)):
    dh=hm[i]-hm[i-1]
    if abs(dh)>3:
        ax.annotate(f'{dh:+.0f}',((i+i-1)/2,(hm[i]+hm[i-1])/2),fontsize=7,color=ACCENT_BLUE,ha='center',
                    bbox=dict(facecolor=BG,edgecolor='none',alpha=0.8))
ax.set_xticks(range(len(pc14))); ax.set_xticklabels(pc14,rotation=45,ha='right')
ax.set_ylabel('Centimeter'); ax.set_title('Dimensjonsdrift: hogde fell, breidde oscillerer')
ax.legend(fontsize=9); ax.set_ylim(40,110)
fig.savefig(f"{FIG}/fig14_dimensjonsdrift.pdf"); plt.close()

# ================================================================
# FIG 16: BEVISKJEDE (4-panel)
# ================================================================
print("Fig 16: Beviskjede...")
fig,axes=plt.subplots(2,2,figsize=(10,7.5))
fig.suptitle('Konvergent bevis: fire pilarar i Form Follows Fitness',fontsize=13)

# (a) Entropy
ax=axes[0,0]
cen=['1200','1300','1400','1500','1600','1700','1800','1900','2000']
hv=[1.0,1.0,1.9,1.49,3.85,4.24,4.67,5.07,4.66]
ax.fill_between(range(len(cen)),hv,alpha=0.15,color=ACCENT_BLUE)
ax.plot(range(len(cen)),hv,'o-',color=ACCENT_BLUE,lw=2,ms=5)
ax.set_xticks(range(len(cen))); ax.set_xticklabels(cen,fontsize=7,rotation=45)
ax.set_ylabel("$H'$ (bits)"); ax.set_title('(a) Materialentropi stig',fontsize=10)
ax.set_ylim(0,6)

# (b) Modulor
ax=axes[0,1]
cm=['1500','1600','1700','1800','1900','2000']
av=[-19.7,-20.9,-25.3,-24.8,-34.9,-39.9]
ax.bar(range(len(cm)),av,color=ACCENT_RED,edgecolor='white',width=0.55)
ax.axhline(0,color=TEXT_COL,lw=0.6)
for i,v in enumerate(av): ax.text(i,v-2,f'{v:.0f}',ha='center',fontsize=7,color='white',fontweight='bold')
ax.set_xticks(range(len(cm))); ax.set_xticklabels(cm,fontsize=7,rotation=45)
ax.set_ylabel('Avvik (cm)'); ax.set_title('(b) Modulor-avvik: negativt',fontsize=10)

# (c) Jaccard
ax=axes[1,0]
ax.fill_between(range(len(jc)),jd,alpha=0.15,color=ACCENT_BLUE)
ax.plot(range(len(jc)),jd,'s-',color=ACCENT_BLUE,lw=2,ms=6)
ax.set_xticks(range(len(jc))); ax.set_xticklabels(jc,fontsize=7,rotation=45)
ax.set_ylabel('$d_J$'); ax.set_title('(c) NMK/V&A konvergerer',fontsize=10)
ax.set_ylim(0,1)

# (d) MI
ax=axes[1,1]
mil=['Prop.','Tid','Mat.','Geo.','Funk.']
miv=[2.072,1.546,1.456,0.797,0.0]
mic=[ACCENT_BLUE,ACCENT_BROWN,ACCENT_BROWN,ACCENT_GREEN,ACCENT_RED]
ax.barh(range(len(mil)-1,-1,-1),miv,color=mic,height=0.45)
ax.set_yticks(range(len(mil)-1,-1,-1)); ax.set_yticklabels(mil,fontsize=8)
ax.set_xlabel('MI (bits)'); ax.set_title('(d) Funksjon = null',fontsize=10)
ax.text(0.05,0,'0.000',fontsize=9,color=ACCENT_RED,fontweight='bold')

fig.tight_layout()
fig.savefig(f"{FIG}/fig16_beviskjede.pdf"); plt.close()

print(f"\nAlle figurar regenererte i unified stil.")
print(f"Figurar i {FIG}/:")
for f in sorted(os.listdir(FIG)):
    if f.endswith('.pdf'):
        sz=os.path.getsize(f"{FIG}/{f}")//1024
        print(f"  {f:45s} {sz:>4d} KB")
