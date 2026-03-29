# STOLAR - Open database for europeiske stolar

Ein open forskingsdatabase med **2 300 stolar** (1280-2024) frå [Nasjonalmuseet](https://www.nasjonalmuseet.no/) og [Victoria and Albert Museum](https://www.vam.ac.uk/), med AI-genererte 3D-modellar, dimensjonar, stilklassifisering og metadata.

## Innhald

```
STOLAR/
  api.json          # Fullstendig JSON-API (alle felt)
  STOLAR.csv        # CSV-eksport
  STOLAR_all.csv    # Utvida CSV med alle felt
  glb/              # 3D-modellar (GLB), ~2 200 filer
  bguw/             # Bakgrunnsfjerna bilete (PNG)
  images/           # Originale museumsfoto (JPG)
  pages/            # Strukturerte Markdown-sider per stol
```

## JSON-API

All strukturert data er tilgjengeleg som ein enkel JSON-fil:

```
https://raw.githubusercontent.com/lukketsvane/stolar-db/main/STOLAR/api.json
```

### Felt (2 300 postar)

| Felt | Dekning | Skildring |
|---|---|---|
| `id` | 100 % | Objekt-ID (t.d. `OK-02274`, `NMK.2006.0076`) |
| `name` | 100 % | Namn |
| `type` | 100 % | Nemning: Stol, Armstol, Krakk, Barnestol, osb. |
| `materials` | 100 % | Materialar |
| `height_cm` | 100 % | Hogde i cm |
| `width_cm` | 99 % | Breidde i cm |
| `depth_cm` | 98 % | Djupn i cm |
| `year_from` | 100 % | Tidlegaste datering |
| `year_to` | 96 % | Seinaste datering |
| `style` | 99 % | Stilperiode (38 kategoriar) |
| `designer` | 69 % | Designar/produsent |
| `origin` | 95 % | Produksjonsstad |
| `nationality` | 70 % | Nasjonalitet |
| `weight_kg` | 69 % | Estimert vekt i kg |
| `museum_url` | 100 % | Lenkje til museumsside |
| `glb_url` | 99 % | 3D-modell (GLB) |
| `bguw_url` | 99 % | Bakgrunnsfjerna bilete |
| `source_image_url` | 99 % | Original museumsfoto |

### Stilperiodar

| Stil | Antal | Periode |
|---|---|---|
| Nyklassisisme | 301 | ~1750-1800 |
| Barokk | 264 | ~1600-1700 |
| Rokokko | 222 | ~1700-1750 |
| Postmodernisme | 212 | ~1970-2000 |
| Historisme | 207 | ~1830-1900 |
| Modernisme | 150 | ~1945-1970 |
| Empire | 147 | ~1800-1830 |
| Viktorianisme | 107 | ~1860-1900 |
| Art Deco | 106 | ~1920-1945 |
| Samtidsdesign | 79 | 2000+ |
| Jugend / Art Nouveau | 79 | ~1900-1920 |
| Renessanse | 63 | Før 1600 |
| Funksjonalisme | 47 | ~1920-1940 |
| Bauhaus | 20 | ~1919-1933 |
| Skandinavisk modernisme | 14 | ~1930-1970 |

### Stoltypar

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

## Datakjelder

- **Nasjonalmuseet** - Nasjonalmuseet for kunst, arkitektur og design, Oslo
- **V&A** - Victoria and Albert Museum, London

3D-modellane er AI-genererte med [Hunyuan3D-2](https://github.com/Tencent/Hunyuan3D-2) frå museumsfoto. Bakgrunnsfjerna bilete er produserte med Gemini Vision. Originalfoto og metadata kjem frå opne museum-API-ar.

## Lisens

[MIT](LICENSE)

Originalfoto og metadata er henta frå opne museum-API-ar. Sjå kvart museum sine vilkar for gjenbruk av deira materiale.
