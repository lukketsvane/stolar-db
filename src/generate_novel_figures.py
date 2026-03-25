"""Novel research figurar: ergonomisk ratio, materialradius, affordanse, historiske knutepunkt."""
import csv, math, os
from collections import Counter, defaultdict
import statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

BG='#faf8f5'; GRID='#e0dcd5'; TXT='#2d2a26'
RED='#a04030'; BLUE='#4a6fa5'; GREEN='#5a8a5a'; BROWN='#8b6914'; GREY='#8a8a8a'; GOLD='#c49b2a'
PURPLE='#7a5a8a'; TEAL='#5a8a7a'

plt.rcParams.update({
    'font.family':'serif','font.size':9.5,'axes.titlesize':12,'axes.titleweight':'normal',
    'axes.labelsize':10,'axes.linewidth':0.4,'axes.facecolor':BG,'axes.edgecolor':'#c0bdb5',
    'axes.grid':True,'grid.color':GRID,'grid.linewidth':0.3,'grid.alpha':0.7,
    'figure.facecolor':BG,'figure.dpi':200,'savefig.bbox':'tight','savefig.pad_inches':0.3,
    'savefig.facecolor':BG,'text.color':TXT,'axes.labelcolor':TXT,
})

FIG="../texts/fig"
rows=[]
with open("../stolar_db.csv",encoding="utf-8-sig") as f:
    for r in csv.DictReader(f): rows.append(r)
def sf(v):
    try: x=float(v.replace(",",".")); return x if x>0 else None
    except: return None
def cs(c):
    try: return int(c.split("-")[0])
    except: return 9999
for r in rows:
    r["_c"]=r.get("Hundreår","").strip(); r["_h"]=sf(r.get("Høgde (cm)",""))
    r["_w"]=sf(r.get("Breidde (cm)","")); r["_sh"]=sf(r.get("Setehøgde (cm)",""))
    r["_mats"]=[m.strip() for m in r.get("Materialar","").split(",") if m.strip()]
    try: r["_y"]=int(r.get("Frå år","").strip()); r["_y"]=r["_y"] if r["_y"]>100 else None
    except: r["_y"]=None

main_c=sorted([c for c in set(r["_c"] for r in rows if r["_c"])
               if c not in ("1200-talet","1300-talet","1400-talet")],key=cs)

# FIG 23: Ergonomisk ratio SH/H
print("Fig 23: Ergonomisk ratio...")
cent_ratio=defaultdict(list)
for r in rows:
    if r["_c"] in main_c and r["_h"] and r["_sh"] and r["_h"]>30:
        cent_ratio[r["_c"]].append(r["_sh"]/r["_h"])

pc=[c for c in main_c if len(cent_ratio[c])>=5]
means=[100*statistics.mean(cent_ratio[c]) for c in pc]
meds=[100*statistics.median(cent_ratio[c]) for c in pc]

fig,ax=plt.subplots(figsize=(8,4.5))
ax.fill_between(range(len(pc)),means,alpha=0.15,color=PURPLE)
ax.plot(range(len(pc)),means,'o-',color=PURPLE,lw=2.5,ms=7,label='Gj.snitt SH/H (%)')
ax.plot(range(len(pc)),meds,'s--',color=TEAL,lw=1.5,ms=5,label='Median')
ax.axhline(50,color=GREY,ls=':',lw=0.6,alpha=0.5)
ax.axhline(100,color=RED,ls=':',lw=0.6,alpha=0.3)
for i,(c,m) in enumerate(zip(pc,means)):
    ax.annotate(f'{m:.0f}%',(i,m),textcoords='offset points',xytext=(0,10),
                ha='center',fontsize=8.5,color=PURPLE,fontweight='bold')
ax.set_xticks(range(len(pc))); ax.set_xticklabels(pc,rotation=45,ha='right')
ax.set_ylabel('Setehogde / Totalhogde (%)')
ax.set_title('Stolen mistar ryggen: ergonomisk ratio over tid')
ax.legend(fontsize=8); ax.set_ylim(35,110)
ax.text(len(pc)-1.5,40,'100% = krakk\n(ingen rygg)',fontsize=8,color=RED,style='italic',ha='center')
fig.savefig(f"{FIG}/fig23_ergonomisk_ratio.png",dpi=200); plt.close()

# FIG 24: Materialradius over tid
print("Fig 24: Materialradius...")
radius={"Bjørk":0,"Furu":0,"Eik":0,"Ask":0,"Or":0,"Alm":0,"Gran":0,"Bøk":0,"Osp":0,"Lind":0,"Lønn":0,
        "Nøttetre":1,"Buksbom":1,"Messing":1,"Bronse":1,"Jern":1,"Lin":1,"Ull":1,"Bomull":1,
        "Hestetagl":1,"Lær":1,"Skinn":1,"Sølv":1,
        "Mahogni":2,"Ibenholt":2,"Palisander":2,"Rotting":2,"Teak":2,"Bambus":2,"Silke":2,"Palme":2,
        "Stål":3,"Aluminium":3,"Plast":3,"Glasfiber":3,"Kryssfiner":3,"Polypropylen":3,
        "Polyuretan":3,"Skumplast":3,"Gummi":3,"Polykarbonat":3}

period_rad=defaultdict(list)
for r in rows:
    if r["_y"] and r["_mats"]:
        p=(r["_y"]//50)*50
        rads=[radius.get(m,1) for m in r["_mats"]]
        period_rad[p].append(max(rads) if rads else 0)

ps=sorted(p for p in period_rad if p>=1500 and len(period_rad[p])>=5)
mr=[statistics.mean(period_rad[p]) for p in ps]

fig,ax=plt.subplots(figsize=(9,4.5))
colors_r=[GREEN if m<1 else BROWN if m<2 else RED if m<2.5 else BLUE for m in mr]
ax.bar(range(len(ps)),mr,color=colors_r,edgecolor='white',width=0.7,alpha=0.7)
ax.plot(range(len(ps)),mr,'o-',color=TXT,lw=1.5,ms=4)
for i,(p,m) in enumerate(zip(ps,mr)):
    ax.text(i,m+0.08,f'{m:.2f}',ha='center',fontsize=7,color=TXT)
ax.set_xticks(range(len(ps)))
ax.set_xticklabels([str(p) for p in ps],rotation=55,ha='right',fontsize=7.5)
ax.set_ylabel('Gj.snittleg maks materialradius')
ax.set_title('Materialradiusen veks: fraa dalfoere til verdsmarknad')
ax.set_ylim(0,3.2)
# Label the radius levels
for lvl,label,col in [(0.5,'Lokalt',GREEN),(1.5,'Europeisk',BROWN),(2.5,'Kolonialt',RED)]:
    ax.axhline(lvl,color=col,ls=':',lw=0.5,alpha=0.3)
    ax.text(len(ps)-0.5,lvl+0.05,label,fontsize=7,color=col,ha='right',style='italic')
fig.savefig(f"{FIG}/fig24_materialradius.png",dpi=200); plt.close()

# FIG 25: Historiske knutepunkt + entropi
print("Fig 25: Historiske knutepunkt...")
def entropy_bits(mats):
    c=Counter(mats);t=sum(c.values())
    if t==0: return 0
    return -sum((n/t)*math.log2(n/t) for n in c.values() if n>0)

events=[(1700,"Queen Anne"),(1750,"Sjuaarskrigen"),(1800,"Napoleon"),
        (1850,"Great Exhibition"),(1900,"Jugend"),(1925,"Bauhaus"),
        (1950,"Scandinavian Design"),(1970,"Postmodernisme")]
years_e=[e[0] for e in events]
labels_e=[e[1] for e in events]
hs_e=[]
ns_e=[]
for yr,_ in events:
    window=[m for r in rows if r["_y"] and abs(r["_y"]-yr)<=10 for m in r["_mats"]]
    n=len([r for r in rows if r["_y"] and abs(r["_y"]-yr)<=10])
    hs_e.append(entropy_bits(window) if window else 0)
    ns_e.append(n)

fig,ax=plt.subplots(figsize=(9,5))
ax.bar(range(len(events)),hs_e,color=[BROWN if y<1850 else BLUE for y,_ in events],
       edgecolor='white',width=0.6,alpha=0.7)
for i,(yr,label) in enumerate(events):
    ax.text(i,hs_e[i]+0.08,f"$H'$={hs_e[i]:.2f}\nn={ns_e[i]}",ha='center',fontsize=7.5,color=TXT)
ax.set_xticks(range(len(events)))
ax.set_xticklabels([f'{yr}\n{label}' for yr,label in events],fontsize=8)
ax.set_ylabel("Shannon-entropi $H'$ (bits)")
ax.set_title('Historiske knutepunkt og materialentropi')
ax.set_ylim(0,5.5)

# Annotate mahogni dominance at 1750
ax.annotate('Mahogni\ndominerer',xy=(1,hs_e[1]),xytext=(1,2.5),
            fontsize=8,color=RED,ha='center',fontweight='bold',
            arrowprops=dict(arrowstyle='->',color=RED))
fig.savefig(f"{FIG}/fig25_historiske_knutepunkt.png",dpi=200); plt.close()

# FIG 26: Materiell demokratisering tidslinje
print("Fig 26: Materiell demokratisering...")
track_mats={"Mahogni":RED,"Stål":BLUE,"Kryssfiner":BROWN,"Plast":PURPLE,"Bjørk":GREEN}
fig,ax=plt.subplots(figsize=(10,4.5))
for mat,col in track_mats.items():
    decades=defaultdict(int)
    for r in rows:
        if mat in r["_mats"] and r["_y"]:
            decades[(r["_y"]//10)*10]+=1
    if decades:
        ds=sorted(decades.keys())
        vs=[decades[d] for d in ds]
        ax.fill_between(ds,vs,alpha=0.15,color=col)
        ax.plot(ds,vs,'-',color=col,lw=2,label=mat)
        # Mark peak
        peak_d=max(decades,key=decades.get)
        ax.plot(peak_d,decades[peak_d],'o',color=col,ms=8)
        ax.text(peak_d,decades[peak_d]+2,f'{peak_d}',fontsize=7,color=col,ha='center')

ax.set_xlabel('Tiaar'); ax.set_ylabel('Antal stolar')
ax.set_title('Materiell demokratisering: kvar dominerer sitt hundreaar')
ax.legend(fontsize=8,loc='upper left'); ax.set_xlim(1550,2030); ax.set_ylim(0,75)
fig.savefig(f"{FIG}/fig26_demokratisering.png",dpi=200); plt.close()

print("Ferdige novel figurar:")
for f in sorted(os.listdir(FIG)):
    if f.startswith("fig2") and f.endswith(".png"):
        print(f"  {f}")
