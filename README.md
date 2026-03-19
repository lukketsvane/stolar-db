# STOLAR — 3D Chair Database

A research database of **2,048 chairs** from the [Nasjonalmuseet](https://www.nasjonalmuseet.no/) (Norway) and the [Victoria and Albert Museum](https://www.vam.ac.uk/) (UK), with AI-generated 3D models, background-removed images, and rich metadata.

Built as part of PhD research at [AHO – Oslo School of Architecture and Design](https://aho.no).

## Data

All structured data is available as a single JSON file:

```
https://raw.githubusercontent.com/lukketsvane/stolar-db/main/STOLAR/api.json
```

### Schema

Each entry in `api.json` contains:

| Field | Type | Description |
|---|---|---|
| `id` | string | Object ID (e.g., `OK-02274`, `NMK.2006.0076`, `O80363`) |
| `name` | string | Chair name/title |
| `type` | string | Object type (Stol, Lenestol, Krakk, etc.) |
| `dating` | string | Date or period description |
| `year_from` | number | Earliest year |
| `year_to` | number | Latest year |
| `century` | string | Century (e.g., `1800-talet`) |
| `style` | string | Style period (Barokk, Rokoko, Nyklassisisme, Etterkrigsmodernisme, etc.) |
| `designer` | string | Designer/producer name |
| `origin` | string | Place of production |
| `nationality` | string | Country of origin |
| `materials` | string | Materials list |
| `materials_desc` | string | Detailed material description |
| `technique` | string | Construction and decoration techniques |
| `keywords` | string | Subject keywords |
| `height_cm` | number | Height in cm |
| `width_cm` | number | Width in cm |
| `depth_cm` | number | Depth in cm |
| `seat_height_cm` | number | Seat height in cm |
| `weight_kg` | number | Estimated weight in kg |
| `acquisition` | string | Acquisition history |
| `museum_url` | string | Link to museum collection page |
| `source_image_url` | string | Original high-resolution photo URL |
| `glb_url` | string | 3D model (GLB) direct download URL |
| `bguw_url` | string | Background-removed preview image URL |

All textual metadata is in **Nynorsk** (Norwegian).

### Style Periods

| Nynorsk | English | Period |
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

## Repository Structure

```
STOLAR/
├── glb/          # 3D models (GLB format), flat directory
├── bguw/         # Background-removed preview images (PNG)
├── images/       # Original source photographs (JPG)
├── pages/        # Notion page exports (Markdown)
├── api.json      # Full JSON API with all metadata
├── STOLAR.csv    # Database CSV export
└── STOLAR_all.csv
```

## Pipeline Scripts

| Script | Purpose |
|---|---|
| `generate_and_upload.py` | Generate 3D meshes from bguw images (Hunyuan3D-2 GPU) |
| `gen_pbr_glb.py` | Generate PBR-textured 3D models (GPU) |
| `generate_bguw.py` | Generate background-removed images (Gemini Vision AI) |
| `sync_stolar.py` | Sync Notion database with GitHub repo |
| `build_api.py` | Build `STOLAR/api.json` from Notion or CSV |
| `push_enrichment.py` | Push enrichment data to Notion with Nynorsk translation |

## Sync Architecture

```
Notion (STOLAR database)
    ↕  sync_stolar.py
GitHub (this repo)
    ↕  build_api.py
STOLAR/api.json → Website / Research tools
```

GitHub Actions runs every 6 hours to keep everything in sync.

## Data Sources

- **Nasjonalmuseet** — Norwegian National Museum of Art, Architecture and Design
- **V&A** — Victoria and Albert Museum, London

## License

The 3D models are AI-generated research outputs. Original photographs and metadata are sourced from museum open-access APIs. See individual museum terms for image reuse.
