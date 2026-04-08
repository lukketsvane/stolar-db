#!/usr/bin/env python3
"""
Write mesh-feature columns back into the STOLAR data sources:
  STOLAR/STOLAR.csv         — append 5 mesh columns
  STOLAR/STOLAR_all.csv     — same
  STOLAR/pages/*.md         — append a mesh-trekk section per page
  STOLAR/api.json           — add a "mesh" subobject to each chair

Matched by Objekt-ID. Chairs without a mesh row are skipped (their new
columns stay empty / subobject stays absent).
"""
from __future__ import annotations
import csv
import json
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
MESH_CSV = ROOT / 'analysis' / 'mesh_features.csv'
STOLAR_DIR = ROOT / 'STOLAR'
CSV_MAIN = STOLAR_DIR / 'STOLAR.csv'
CSV_ALL = STOLAR_DIR / 'STOLAR_all.csv'
API_JSON = STOLAR_DIR / 'api.json'
PAGES_DIR = STOLAR_DIR / 'pages'

# Which mesh columns to write back (subset of the full extraction)
MESH_COLS = [
    ('sphericity',    'Sphericity (mesh)'),
    ('fill_ratio',    'Fill-ratio (mesh)'),
    ('inertia_ratio', 'Inertia-ratio (mesh)'),
    ('complexity',    'Kompleksitet (mesh, log10 v/a)'),
    ('vol_hull',      'Konveks hylster-volum (m³)'),
]


def load_mesh() -> dict[str, dict[str, float]]:
    df = pd.read_csv(MESH_CSV)
    df = df.dropna(subset=[c for c, _ in MESH_COLS])
    out: dict[str, dict[str, float]] = {}
    for _, row in df.iterrows():
        out[str(row['objekt_id'])] = {c: float(row[c]) for c, _ in MESH_COLS}
    return out


def writeback_csv(path: Path, mesh_by_id: dict[str, dict[str, float]]) -> int:
    df = pd.read_csv(path, encoding='utf-8')
    id_col = next((c for c in df.columns if 'Objekt-ID' in c or c == 'Objekt-ID'), None)
    if id_col is None:
        # try header with strict match
        id_col = [c for c in df.columns if c.strip() == 'Objekt-ID']
        id_col = id_col[0] if id_col else None
    if id_col is None:
        print(f'  WARN: no Objekt-ID column in {path.name}', file=sys.stderr)
        return 0
    wrote = 0
    for col, label in MESH_COLS:
        df[label] = df[id_col].map(lambda i: mesh_by_id.get(str(i), {}).get(col))
    wrote = df[[lbl for _, lbl in MESH_COLS]].notna().any(axis=1).sum()
    df.to_csv(path, index=False, encoding='utf-8')
    return int(wrote)


def writeback_api(mesh_by_id: dict[str, dict[str, float]]) -> int:
    with API_JSON.open(encoding='utf-8') as f:
        data = json.load(f)
    wrote = 0
    for chair in data.get('chairs', []):
        cid = chair.get('id')
        if cid and cid in mesh_by_id:
            chair['mesh'] = {k: round(v, 4) for k, v in mesh_by_id[cid].items()}
            wrote += 1
    data['mesh_features_generated'] = pd.Timestamp.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    data['with_mesh'] = wrote
    with API_JSON.open('w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return wrote


def writeback_pages(mesh_by_id: dict[str, dict[str, float]]) -> int:
    wrote = 0
    for page in sorted(PAGES_DIR.glob('*.md')):
        text = page.read_text(encoding='utf-8')
        # Find Objekt-ID line
        oid = None
        for line in text.splitlines():
            if line.startswith('Objekt-ID:'):
                oid = line.split(':', 1)[1].strip()
                break
        if not oid or oid not in mesh_by_id:
            continue
        feats = mesh_by_id[oid]
        # Check if a mesh-trekk section already exists; remove it
        marker = '## 3D-mesh-trekk'
        if marker in text:
            text = text.split(marker)[0].rstrip() + '\n'
        block = ['', marker, '']
        for (col, label) in MESH_COLS:
            block.append(f'{label}: {feats[col]:.4f}')
        block.append('')
        page.write_text(text.rstrip() + '\n' + '\n'.join(block), encoding='utf-8')
        wrote += 1
    return wrote


def main() -> int:
    if not MESH_CSV.exists():
        print(f'ERROR: {MESH_CSV} not found', file=sys.stderr)
        return 1
    mesh_by_id = load_mesh()
    print(f'loaded {len(mesh_by_id)} mesh records')

    n_csv_main = writeback_csv(CSV_MAIN, mesh_by_id)
    print(f'STOLAR.csv      : {n_csv_main} rows got mesh columns')

    n_csv_all = writeback_csv(CSV_ALL, mesh_by_id)
    print(f'STOLAR_all.csv  : {n_csv_all} rows got mesh columns')

    n_api = writeback_api(mesh_by_id)
    print(f'api.json        : {n_api} chairs got mesh subobject')

    n_pages = writeback_pages(mesh_by_id)
    print(f'pages/*.md      : {n_pages} pages updated')
    return 0


if __name__ == '__main__':
    sys.exit(main())
