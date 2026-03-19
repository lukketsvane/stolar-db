# STOLAR — 3D-database for stolar

Ein forskingsdatabase med **2 048 stolar** frå [Nasjonalmuseet](https://www.nasjonalmuseet.no/) (Noreg) og [Victoria and Albert Museum](https://www.vam.ac.uk/) (Storbritannia), med AI-genererte 3D-modellar, bakgrunnsfjerna bilete og rik metadata.

Utvikla som del av PhD-forsking ved [AHO – Arkitektur- og designhøgskolen i Oslo](https://aho.no).

## Data

All strukturert data er tilgjengeleg som ei einskild JSON-fil:

```
https://raw.githubusercontent.com/lukketsvane/stolar-db/main/STOLAR/api.json
```

### Skjema

Kvar oppføring i `api.json` inneheld:

| Felt | Type | Skildring |
|---|---|---|
| `id` | tekst | Objekt-ID (t.d. `OK-02274`, `NMK.2006.0076`, `O80363`) |
| `name` | tekst | Namn på stolen |
| `type` | tekst | Objekttype (Stol, Lenestol, Krakk, osb.) |
| `dating` | tekst | Datering eller periodeskildring |
| `year_from` | tal | Tidlegaste år |
| `year_to` | tal | Seinaste år |
| `century` | tekst | Hundreår (t.d. `1800-talet`) |
| `style` | tekst | Stilperiode (sjå tabell under) |
| `designer` | tekst | Designar/produsent |
| `origin` | tekst | Produksjonsstad |
| `nationality` | tekst | Nasjonalitet |
| `materials` | tekst | Materialar |
| `materials_desc` | tekst | Detaljert materialskildring |
| `technique` | tekst | Konstruksjons- og dekorasjonsteknikkar |
| `keywords` | tekst | Emneord |
| `height_cm` | tal | Høgde i cm |
| `width_cm` | tal | Breidde i cm |
| `depth_cm` | tal | Djupn i cm |
| `seat_height_cm` | tal | Setehøgde i cm |
| `weight_kg` | tal | Estimert vekt i kg |
| `acquisition` | tekst | Ervervingshistorikk |
| `museum_url` | tekst | Lenkje til museumsside |
| `source_image_url` | tekst | Original høgoppløyseleg foto-URL |
| `glb_url` | tekst | 3D-modell (GLB) direkte nedlastings-URL |
| `bguw_url` | tekst | Bakgrunnsfjerna førehandsvisingsbilete-URL |

### Stilperiodar

| Stilperiode | Engelsk | Periode |
|---|---|---|
| Renessanse | Renaissance | ~1400–1600 |
| Barokk | Baroque | ~1600–1720 |
| Rokoko | Rococo | ~1720–1770 |
| Nyklassisisme | Neoclassicism | ~1770–1830 |
| Empire | Empire | ~1800–1830 |
| Biedermeier | Biedermeier | ~1815–1848 |
| Historisme | Historicism | ~1840–1900 |
| Jugend | Art Nouveau | ~1890–1910 |
| Arts and Crafts | Arts and Crafts | ~1880–1920 |
| Art Deco | Art Deco | ~1920–1940 |
| Funksjonalisme | Functionalism | ~1920–1940 |
| Skandinavisk modernisme | Scandinavian Modernism | ~1930–1970 |
| Etterkrigsmodernisme | Post-war Modernism | ~1945–1970 |
| Postmodernisme | Postmodernism | ~1975–2000 |
| Samtidsdesign | Contemporary Design | 2000+ |

## Mappestruktur

```
STOLAR/
├── glb/          # 3D-modellar (GLB-format), flat mappe
├── bguw/         # Bakgrunnsfjerna førehandsvisingsbilete (PNG)
├── images/       # Originale kjeldefotografi (JPG)
├── pages/        # Notion-sideeksportar (Markdown)
├── api.json      # Fullstendig JSON-API med all metadata
├── STOLAR.csv    # Database CSV-eksport
└── STOLAR_all.csv
```

## Pipeline-skript

| Skript | Formål |
|---|---|
| `generate_and_upload.py` | Generer 3D-mesh frå bguw-bilete (Hunyuan3D-2 GPU) |
| `gen_pbr_glb.py` | Generer PBR-teksturerte 3D-modellar (GPU) |
| `generate_bguw.py` | Generer bakgrunnsfjerna bilete (Gemini Vision AI) |
| `sync_stolar.py` | Synkroniser Notion-database med GitHub-repo |
| `build_api.py` | Bygg `STOLAR/api.json` frå Notion eller CSV |
| `push_enrichment.py` | Push berikingsdata til Notion med nynorsk-omsetjing |

## Synkroniseringsarkitektur

```
Notion (STOLAR-database)
    ↕  sync_stolar.py
GitHub (dette repoet)
    ↕  build_api.py
STOLAR/api.json → Nettstad / Forskingsverktøy
```

GitHub Actions køyrer kvar 6. time for å halde alt synkronisert.

## Datakjelder

- **Nasjonalmuseet** — Nasjonalmuseet for kunst, arkitektur og design
- **V&A** — Victoria and Albert Museum, London

## Lisens

3D-modellane er AI-genererte forskingsresultat. Originale fotografi og metadata kjem frå opne museum-API-ar. Sjå vilkåra til kvart museum for gjenbruk av bilete.
