# Oppgåvedefinisjon for artikkel 2 (revidert 12.11.2026)

**Arbeidstittel:** Kva stolen held fast, og kva han slepper fri. Katalogførte setehøgder i to museumssamlingar (1280–2024)

Status: utforskande. Alt under er rekna på STOLAR, som er opplæringsdata. Ingenting er forsegla eller registrert.

## 1. Påstanden

Setehøgda er halden fast på tvers av stil, storleik og hundreår. Ryggen er sleppt fri og ber stilen.

Forankring i *formlære*, slik teksten faktisk lyder:

- **6.672:** «Spreiinga langs ein akse minkar med seleksjonsstyrke, prioritering og krumming: Var(x_k) ≈ 1 / (β W_k Λ̂_k″).»
- **6.6721:** «Setehøgda varierer lite, ornamentet mykje. Spreiinga åleine seier ikkje kvifor.»
- **6.6722:** «Er avviket ein avstand til eit målpunkt og grunnfordelinga flat, er Var(x_k) = 2ε_k² / (β W_k)². Korleis spreiinga fell med prioriteringa, skil avviksmåla.»
- **7.151** (føreseiing bunden før måling) og **7.153** (ein enklare grunnmodell må kunne vinne).

Atterhald: i 6.6722 er βW_k ein fri storleik. Ein toleranse henta utanfrå gjev difor ikkje eit absolutt tal for spreiinga. Det som kan føreseiast, er rekkjefølgja mellom aksane, kva spreiinga er bunden til, og korleis målet skalerer.

## 2. Data

STOLAR har 2 048 objekt frå Nasjonalmuseet (426) og Victoria and Albert Museum (1 622). Etter reglane R1–R7 i `04_reinsa_tabell.py`:

| | Nasjonalmuseet | V&A |
|---|---|---|
| Vaksenstolar med gyldig høgd, breidd og djupn | 394 | 1 204 |
| Av desse med truverdig katalogført setehøgd | 225 | 285 |

- V&A-måla er henta på nytt frå museet sitt API, fordi STOLAR.csv hadde 239–330 nullverdiar per mål (einingsfeil: cm, mm, tommar, fot).
- 51 setehøgder i Nasjonalmuseet-radene var kopi av totalhøgda og er fjerna.
- Krakkar, barnestolar, benkestolar og eitt fotografi er flagga ut.
- Musea måler ulikt: V&A ofte «til topp av sarg», Nasjonalmuseet truleg til topp av sete. Nivået kan difor ikkje samanliknast mellom museum.
- Påstanden gjeld det musea har samla, ikkje det som vart laga.

## 3. Funn på opplæringsdataa

| | Nasjonalmuseet | V&A |
|---|---|---|
| Setehøgd: median (cm) | 47,0 | 43,8 |
| Setehøgd: robust spreiing (MAD/median) | 0,047 | 0,078 |
| Rygg: robust spreiing | 0,277 | 0,415 |
| Setehøgd: del forklart av stil | 0,13 | 0,08 |
| Rygg: del forklart av stil | 0,55 | 0,60 |
| Stiging, setehøgd mot totalhøgd | 0,11 [0,05–0,18] | 0,13 [0,08–0,19] |
| Snittfeil fast verdi / fast del av høgda / potenslov (cm) | 3,2 / 6,4 / 3,3 | 3,4 / 7,2 / 3,3 |

## 4. Framlegg til føreseiingar for den forsegla prøva

Tersklane er framlegg med margin til opplæringstala. Dei må fastsetjast av forfattaren før forsegling.

- **P1 Spreiing:** robust spreiing for setehøgd er lågare enn for breidd, djupn og rygg, og under 0,10. For rygg er ho over 0,20.
- **P2 Stil:** stil forklarar under 0,20 av setehøgda og over 0,40 av ryggen.
- **P3 Skalering:** stiginga for setehøgd mot totalhøgd er under 0,3, med øvre intervallgrense under 0,5.
- **P4 Grunnmodellen:** ein fast verdi føreseier setehøgda betre enn ein fast del av totalhøgda, og potenslova slår ikkje den faste verdien med meir enn 0,3 cm.

**Grunnmodell som kan vinne (7.153):** éin felles storleiksfaktor. Han seier stiging 1 i P3 og at fast del av høgda vinn i P4. Held han, tilfører læra ingenting.

## 5. Lagt bort, med grunn

| Føreseiing | Kvifor |
|---|---|
| Setehøgda ligg i 42–46 cm | Slo feil: 34 % (Nasjonalmuseet) og 47 % (V&A) ligg i bandet. |
| Setehøgda følgjer kroppshøgda etter 1850 | Slo feil: ho fell eller står stille i begge museum. |
| Totalhøgda varierer mest | Slo feil i V&A (0,17 mot 0,19 for breidd). Kontrasten er sete mot rygg. |
| Setehøgd målt frå foto | Snittfeil 7,3 cm mot 3,2 cm for fast verdi. 510 katalogmål gjer ho unødvendig. |
| Stil mot materiale (xi), stiavhenge (prop. 4), konvergens (xii) | Som før: sirkulært, for grovt formrom, og dataa kan ikkje prøve det. |

## 6. Ope før forsegling

- Kva museum den forsegla prøva skal hentast frå. Kravet er at museet katalogfører setehøgd. Ikkje undersøkt.
- Innhaustinga må skrivast slik at ingen ser måla før føreseiingane er tidsstempla.
- Antropometriske kjelder er ikkje etterprøvde. ISO 7176 i første utkast er truleg rullestolstandarden.
- Éinfaktormodell med BIC er ikkje køyrd; stiginga i P3 og kryssvalideringa i P4 står i staden.
- Den uavhengige kjelda 6.6721 krev for å seie *kvifor* setehøgda er halden, manglar framleis.

## 7. Køyre på nytt

`python analyse/03_va_dimensjonar.py`, så `04_reinsa_tabell.py`, `05_prove_c.py analyse/data/stolar_reinsa.csv NM` (eller `VA`) og `06_spreiing_per_museum.py`. Utskrift ligg i `*_resultat*.txt`. `02_*` er fotomålinga som ikkje heldt.
