# FORMLÆRE

## prosjekt

ei traktatform om korleis form oppstår, modellert på Wittgensteins *Tractatus*. nynorsk. proposisjonar 1-7, formell appendiks, empiriske testar, føreord og etterord.

## status

- traktaten har føreord, ordliste, proposisjonar 1-7, appendiks (A.1, A.3, A.6), etterord og referansar
- ein claude-agent arbeider med printlayout og formatering av docx
- A.6.1 til A.6.7 er gjennomførte empiriske testar
- mesh_features.csv i analysis/ har resultat frå mesh-geometri-analysar

## hovudoppgåve

systematisk etterprøving av *kvar einaste testbare proposisjon*. me har gjort A.6.1-A.6.7. no skal resten gjerast: avlei hypotesar frå proposisjonane, test dei mot data, og lag gode visualiseringar.

### 1. identifiser alle testbare proposisjonar

gå gjennom 1.1 til 7.8. for kvar proposisjon merka ^a^, ^o^ eller ^t^ som gjer ein empirisk prediksjon: formuler ein testbar hypotese. skriv `analysis/hypotheses.md`.
### 2. test mot data
- `STOLAR.csv` / `STOLAR_all.csv`: katalogdata (~2300 stolar)
- `STOLAR/glb/`: ~2000 GLB mesh-filer. dette er faktisk geometri, ikkje berre mål
GLB-parsing: `trimesh.load(path, force='scene')`, batch 60-80, `gc.collect()` etter kvar batch. hent frå `https://media.githubusercontent.com/media/lukketsvane/stolar-db/main/STOLAR/glb/{Objekt-ID}.glb`


lag veldig gode, lesbare visualiseringar. radar, scatter, density. aldri stolpediagram. kvit bakgrunn, skarpe geometriske former, ingen avrunda hjørne. kvar figur skal kunne stå åleine og fortelje ei historie.
prøv aktivt å felle proposisjonane. ein proposisjon som overlever forsøk på falsifisering er sterkare enn ein som berre er "stadfesta". sjå etter:
- kantverdiar som bryt mønsteret
- stilar eller periodar der prediksjonen ikkje held
- alternative forklaringar som er enklare
### 5. oppdater appendiks
nye testar vert lagt til A.6 etter same mønster som A.6.1-A.6.7. kvar test refererer tilbake til proposisjonsnummeret.
lag ei ny docs fil som inneheld kunn desse empiri appendicx, samt dei førre
```
FORMLÆRE.docx         # hovudfil (claude-agent held på layout)
STOLAR.csv            # katalogdata
STOLAR/glb/           # mesh-geometri
analysis/             # testar og visualiseringar
  mesh_features.csv   # utrekna mesh-trekk
temp/referansar/           # alle kjelder som PDF
temp/stilar/
  traktat.md          # skrivestil for proposisjonar
  prosa.md            # skrivestil for artiklar
```
## skrivestilar
les `temp/stilar/traktat.md` og `temp/stilar/prosa.md`
## forbod
- aldri em-dash
- aldri stolpediagram
- aldri «emergent»
- aldri avrunda hjørne i figurar
- hald unna build_latex og FORMLÆRE.docx og FORMLÆRE.text etc