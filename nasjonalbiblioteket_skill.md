# Nasjonalmuseet DiMu API

Auto description: Systeminstruksjon for å hente strukturert metadata frå Nasjonalmuseet si samling via DigitaltMuseum (DiMu) API. Inkluderer søk, objekthenting, IIIF-bilete, klassifikasjonskoder og Python-script. Demo API-nøkkel: demo. Eigarkode: NMK* (NMK-D=Design). Relevante klassifikasjonar: 352.6 (Stativer/opphengsanordningar), 352.1 (Veggheng), 322.48 (Møbeldesign). Metadata er CC0, bilete CC-BY.
Created Date: March 8, 2026
Description: Systeminstruksjon for å hente strukturert metadata frå Nasjonalmuseet si samling via DigitaltMuseum (DiMu) API. Inkluderer søk, objekthenting, IIIF-bilete, klassifikasjonskoder og Python-script. Demo API-nøkkel: demo. Eigarkode: NMK* (NMK-D=Design). Relevante klassifikasjonar: 352.6 (Stativer/opphengsanordningar), 352.1 (Veggheng), 322.48 (Møbeldesign). Metadata er CC0, bilete CC-BY.
Select: claude

## Nasjonalmuseet via DigitaltMuseum API

### Tilgang

- Base-URL: `https://api.dimu.org/api/solr/select`
- Demo-nøkkel: `demo` (maks 10 rader). Full nøkkel: søk hjå KulturIT ([https://kulturit.org/](https://kulturit.org/))
- Eigarkode: `NMK*` (NMK-D = Design, NMK-B = Biletkunst, NMK-A = Arkitektur)

### Søk

```
curl "https://api.dimu.org/api/solr/select?q=SOEKEORD&fq=identifier.owner:NMK*&wt=json&api.key=demo&rows=50"
```

Kombiner med OR/AND: `q=knagg+OR+stumtjener`

Filtrer på felt: `fq=artifact.ingress.names:"Knagg"`

### Hente fullt objekt

```
curl "https://api.dimu.org/artifact/uuid/UUID_HER?api.key=demo"
```

Returnerer fullstendig JSON:

- `names` → Objektnamn
- `eventWrap.events` → Produksjon (designar, produsent, stad, år)
- `material.materials` → Materialar + `material.comment`
- `measureDescription` → Mål
- `media.pictures[0].sourceUrl` → IIIF bilete-URL
- `eventWrap.acquisition` → Ervervsmetode
- `eventWrap.descriptiveDating` → Datering

### IIIF bilete

```
https://ms01.nasjonalmuseet.no/iiif/tif/FILNAMN.tif/full/WIDTH,/0/default.jpg
```

Juster WIDTH (800 for liten, 4000 for full).

### Objektlenke

```
https://www.nasjonalmuseet.no/en/collection/object/INVENTARNUMMER/
```

### Klassifikasjonskoder

- `352.6` = Stativer og opphengsanordningar (knaggar, stumtjenarar)
- `352.1` = Veggheng (OBS: inneheld også stolar)
- `322.48` = Møbeldesign
- `353` = Frakkestativ (OBS: breitt, inneheld også tekstilar)

### Søkjeord for knaggar/oppheng

Norsk: knagg, stumtjener, kleshenger, knaggebrett, frakkestativ, entrévegg, entremøbel, veggfeste, hatteknag

Engelsk: coat hook, coat stand, coat hanger, coat rack, wall hook, hat rack

Namnsøk: `fq=artifact.ingress.names:"Knagg"`

### Python-script

```python
import json, urllib.request

def search_nmk(query, rows=50):
    url = f'https://api.dimu.org/api/solr/select?q={query}&fq=identifier.owner:NMK*&wt=json&api.key=demo&rows={rows}'
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read())['response']['docs']

def get_object(uuid):
    url = f'https://api.dimu.org/artifact/uuid/{uuid}?api.key=demo'
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read())

def extract(data):
    names = [n['name'] for n in data.get('names', [])]
    events = data.get('eventWrap', {}).get('events', [])
    designers, producers, places, years = [], [], [], []
    for ev in events:
        for p in ev.get('relatedPersons', []):
            role = p.get('role', {}).get('name', '')
            status = str(p.get('role', {}).get('status', ''))
            if 'feilaktig' in status: continue
            if role in ['Kunstner','Formgiver','Designer']: designers.append(p['name'])
            elif role == 'Produsent': producers.append(p['name'])
        for pl in ev.get('relatedPlaces', []):
            for f in pl.get('fields', []):
                if f['placeType'] == 'country': places.append(f['value'])
        ts = ev.get('timespan', {})
        if ts and ts.get('fromYear'): years.append(ts['fromYear'])
    mat = data.get('material', {})
    materials = [m['material'] for m in mat.get('materials',[])] if mat else []
    pics = data.get('media',{}).get('pictures',[])
    return {
        'names': names, 'designers': designers, 'producers': producers,
        'places': list(set(places)), 'year': min(years) if years else None,
        'materials': materials, 'dims': data.get('measureDescription',''),
        'image': pics[0].get('sourceUrl','') if pics else '',
        'id': data.get('identifier',{}).get('id','')
    }
```

### Dokumentasjon

- GitHub: [https://github.com/nasjonalmuseet/DiMu-API-documentation](https://github.com/nasjonalmuseet/DiMu-API-documentation)
- API-dok: [https://api.dimu.org/doc/public_api.html](https://api.dimu.org/doc/public_api.html)
- KulturIT: [https://dok.digitaltmuseum.org/api](https://dok.digitaltmuseum.org/api)