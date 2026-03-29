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

Rotstrukturen har metadata (`generated`, `total`, `with_3d`, `with_bguw`, `base_url`) og ein `chairs`-liste med 2 300 objekt.

### Felt (2 300 postar)

| Felt | Dekning | Skildring |
|---|---|---|
| `id` | 100 % | Objekt-ID (t.d. `OK-02274`, `NMK.2006.0076`) |
| `name` | 100 % | Namn |
| `type` | 100 % | Nemning: Stol, Armstol, Krakk, osb. |
| `materials` | 100 % | Materialar |
| `materials_desc` | 100 % | Materialkommentar |
| `dating` | 99 % | Dateringsstreng (t.d. "1750-1780") |
| `year_from` | 99 % | Tidlegaste datering (tal) |
| `year_to` | 64 % | Seinaste datering (tal) |
| `century` | 99 % | Hundreår (t.d. "1700-talet") |
| `style` | 99 % | Stilperiode (38 kategoriar) |
| `designer` | 69 % | Designar/produsent |
| `origin` | 95 % | Produksjonsstad |
| `nationality` | 70 % | Nasjonalitet |
| `height_cm` | 89 % | Hogde i cm |
| `width_cm` | 87 % | Breidde i cm |
| `depth_cm` | 84 % | Djupn i cm |
| `seat_height_cm` | 21 % | Setehogde i cm |
| `weight_kg` | 7 % | Estimert vekt i kg |
| `technique` | 44 % | Teknikk |
| `keywords` | 29 % | Emneord |
| `acquisition` | 29 % | Ervervingshistorikk |
| `museum_url` | 100 % | Lenkje til museumsside |
| `source_image_url` | 99 % | Original museumsfoto |
| `glb_url` | 99 % | 3D-modell (GLB) |
| `bguw_url` | 99 % | Bakgrunnsfjerna bilete |

### Stilperiodar (topp 15)

| Stil | Antal |
|---|---|
| Nyklassisisme | 301 |
| Barokk | 264 |
| Rokokko | 222 |
| Postmodernisme | 212 |
| Historisme | 207 |
| Modernisme / Midtjahrhundre | 150 |
| Empire | 147 |
| Viktorianisme | 107 |
| Art Deco / Tidleg modernisme | 106 |
| Samtidsdesign | 79 |
| Jugend / Art Nouveau | 79 |
| Renessanse | 63 |
| Funksjonalisme | 47 |
| Hepplewhite | 28 |
| Regence | 27 |

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
