# STOLAR - Kvantitativ formhistorie for europeiske stolar

Ein forskingsdatabase med **2 300 stolar** (1280-2024) frå [Nasjonalmuseet](https://www.nasjonalmuseet.no/) og [Victoria and Albert Museum](https://www.vam.ac.uk/), med AI-genererte 3D-modellar, dimensjonar, stilklassifisering og rik metadata.

Utvikla som del av masterforsking ved [AHO](https://aho.no). Prosjektet testar FORMLÆRE-rammeverket: ein formell traktat med 10 proposisjonar om korleis form oppstår.

## Datalagring

All strukturert data er tilgjengeleg som JSON-API:

```
https://raw.githubusercontent.com/lukketsvane/stolar-db/main/STOLAR/api.json
```

### Feltdekning (2 300 postar)

| Felt | Dekning | Skildring |
|---|---|---|
| `id` | 100% | Objekt-ID (t.d. `OK-02274`, `NMK.2006.0076`) |
| `name` | 100% | Namn |
| `type` | 100% | Nemning: Stol, Armstol, Krakk, Barnestol, osb. |
| `materials` | 100% | Materialar |
| `height_cm` | 100% | Hogde i cm |
| `width_cm` | 99% | Breidde i cm |
| `depth_cm` | 98% | Djupn i cm |
| `year_from` | 100% | Tidlegaste datering |
| `year_to` | 96% | Seinaste datering |
| `style` | 99% | Stilperiode (38 kategoriar, sjå under) |
| `designer` | 69% | Designar/produsent |
| `origin` | 95% | Produksjonsstad |
| `nationality` | 70% | Nasjonalitet |
| `weight_kg` | 69% | Estimert vekt i kg |
| `museum_url` | 100% | Lenkje til museumsside |
| `glb_url` | 99% | 3D-modell (GLB) |
| `bguw_url` | 99% | Bakgrunnsfjerna bilete |
| `source_image_url` | 99% | Original museumsfoto |

### Stilperiodar (topp 15)

| Stil | Antal | Periode |
|---|---|---|
| Nyklassisisme | 301 | ~1750-1800 |
| Barokk | 264 | ~1600-1700 |
| Rokokko | 222 | ~1700-1750 |
| Postmodernisme | 212 | ~1970-2000 |
| Historisme | 207 | ~1830-1900 |
| Modernisme / Midtjahrhundre | 150 | ~1945-1970 |
| Empire | 147 | ~1800-1830 |
| Viktorianisme | 107 | ~1860-1900 |
| Art Deco / Tidleg modernisme | 106 | ~1920-1945 |
| Samtidsdesign | 79 | 2000+ |
| Jugend/Art Nouveau | 79 | ~1900-1920 |
| Renessanse | 63 | Før 1600 |
| Funksjonalisme | 47 | ~1920-1940 |
| Skandinavisk modernisme | 14 | ~1930-1970 |
| Bauhaus | 20 | ~1919-1933 |

### Nemningar (stoltypar)

| Type | Antal |
|---|---|
| Stol | 1 680 |
| Armstol | 463 |
| Krakk | 86 |
| Barnestol | 21 |
| Spisestol | 19 |
| Benkestol | 9 |
| Klappstol | 7 |
| Loungestol | 6 |
| Gyngestol | 6 |

## Repostruktur

```
stolar-db/
  STOLAR/                  # Database med 2300 stolar
    glb/                   #   3D-modellar (GLB), ~2288 filer
    bguw/                  #   Bakgrunnsfjerna bilete (PNG)
    images/                #   Originale museumsfoto (JPG)
    pages/                 #   Notion-eksport (Markdown)
    api.json               #   Fullstendig JSON-API
    STOLAR.csv             #   CSV-eksport

  texts/                   # Akademiske artiklar (ClaudePrism-kompatible)
    I-Materialar/          #   Artikkel I: Materialar som geopolitisk historie
    II-Geografi/           #   Artikkel II: Produksjonsgeografi
    III-Form-og-tid/       #   Artikkel III: Form og tid, Random Forest
    IV-Form-follows-fitness/ # Artikkel IV: Fitnesslandskap-teori
    V-Modulor/             #   Artikkel V: Le Corbusier-proporsjonar
    VI-Seleksjonstrykk/    #   Artikkel VI: Seleksjonstrykk og gradient
    VII-Fitnesslandskap/   #   Artikkel VII: Empirisk fitnesslandskap
    VIII-Vegar-og-grenser/ #   Artikkel VIII: Vegar og grenser
    Avhandling/            #   Monografi (kappa)
    Formlaere-traktat/     #   FORMLARE traktat (10 proposisjonar)

  src/                     # Analysskript (Python)
    artikkel_*_analyse.py  #   Per-artikkel statistisk analyse
    formlaere_*.py         #   FORMLARE empirisk testing
    enrich_database.py     #   Stil- og typeklassifisering
    entropy_materials_v2.py #  Shannon-entropi materialar

  figurar/                 # Publiseringsfigurar (PNG)
  teikningar/              # Konseptuelle illustrasjonar

  build_api.py             # Bygg api.json frå CSV/Notion
  sync_stolar.py           # Synkroniser Notion <-> GitHub
  generate_and_upload.py   # 3D-generering (Hunyuan3D-2)
  generate_bguw.py         # Bakgrunnsfjerning (Gemini Vision)
  gen_pbr_glb.py           # PBR-teksturering
  push_enrichment.py       # Push beriking til Notion

  claude-prism/            # ClaudePrism (nynorsk fork, lokal LaTeX-arbeidsplass)
  arkiv/                   # Arkiverte eingongsskript
```

## Synkronisering

```
Notion (STOLAR) <-> sync_stolar.py <-> GitHub <-> build_api.py -> api.json
```

GitHub Actions synkroniserer kvar 6. time.

## Datakjelder

- **Nasjonalmuseet** - Nasjonalmuseet for kunst, arkitektur og design (NMK, OK)
- **V&A** - Victoria and Albert Museum, London

## Lisens

3D-modellane er AI-genererte forskingsresultat. Originalfoto og metadata kjem frå opne museum-API-ar. Sjå kvart museum sine vilkar for gjenbruk.
