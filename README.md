# STOLAR - Open database for europeiske stolar

Ein open forskingsdatabase med **2 048 stolar** (1280-2024) frå [Nasjonalmuseet](https://www.nasjonalmuseet.no/) og [Victoria and Albert Museum](https://www.vam.ac.uk/), med AI-genererte 3D-modellar, dimensjonar, stilklassifisering og metadata.

## Innhald

```
STOLAR/
  api.json          # Fullstendig JSON-API (alle felt)
  STOLAR.csv        # CSV-eksport
  STOLAR_all.csv    # Utvida CSV med alle felt
  glb/              # 3D-modellar (GLB), ~2 041 filer
  bguw/             # Bakgrunnsfjerna bilete (PNG)
  images/           # Originale museumsfoto (JPG)
  pages/            # Strukturerte Markdown-sider per stol
```

## JSON-API

All strukturert data er tilgjengeleg som ein enkel JSON-fil:

```
https://raw.githubusercontent.com/lukketsvane/stolar-db/main/STOLAR/api.json
```

Rotstrukturen har metadata (`generated`, `total`, `with_3d`, `with_bguw`, `base_url`) og ein `chairs`-liste med 2 048 objekt.

### Felt

| Felt | Dekning | Skildring |
|---|---|---|
| `id` | 100 % | Objekt-ID (t.d. `OK-02274`, `NMK.2006.0076`) |
| `name` | 100 % | Namn |
| `type` | 100 % | Nemning: Stol, Armstol, Krakk, osb. |
| `materials` | 100 % | Materialar |
| `materials_desc` | 100 % | Materialkommentar |
| `dating` | 99 % | Dateringsstreng (t.d. "1750-1780") |
| `year_from` | 99 % | Tidlegaste datering (tal) |
| `year_to` | 59 % | Seinaste datering (tal) |
| `century` | 99 % | Hundreår (t.d. "1700-talet") |
| `style` | 99 % | Stilperiode |
| `designer` | 77 % | Designar/produsent |
| `origin` | 96 % | Produksjonsstad |
| `nationality` | 77 % | Nasjonalitet |
| `height_cm` | 88 % | Hogde i cm |
| `width_cm` | 86 % | Breidde i cm |
| `depth_cm` | 82 % | Djupn i cm |
| `seat_height_cm` | 15 % | Setehogde i cm |
| `weight_kg` | 7 % | Estimert vekt i kg |
| `technique` | 38 % | Teknikk |
| `keywords` | 21 % | Emneord |
| `acquisition` | 21 % | Ervervingshistorikk |
| `museum_url` | 100 % | Lenkje til museumsside |
| `source_image_url` | 99 % | Original museumsfoto |
| `glb_url` | 100 % | 3D-modell (GLB) |
| `bguw_url` | 100 % | Bakgrunnsfjerna bilete |

### Stilperiodar

| Stil | Antal |
|---|---|
| Nyklassisisme | 291 |
| Barokk | 229 |
| Rokokko | 206 |
| Postmodernisme | 180 |
| Historisme | 180 |
| Modernisme / Midtjahrhundre | 147 |
| Empire | 130 |
| Viktorianisme | 107 |
| Art Deco / Tidleg modernisme | 103 |
| Jugend / Art Nouveau | 79 |
| Samtidsdesign | 66 |
| Renessanse | 55 |
| Funksjonalisme | 33 |
| Midtjahrhundre modernisme | 21 |
| Bauhaus | 20 |

### Stoltypar

| Type | Antal |
|---|---|
| Stol | 1 444 |
| Armstol | 449 |
| Krakk | 86 |
| Barnestol | 21 |
| Spisestol | 18 |
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
