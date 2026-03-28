# Oppsett på ny maskin

```bash
git clone https://github.com/lukketsvane/stolar-db.git
cd stolar-db
git lfs install
git lfs pull
pip install requests pillow trimesh fast_simplification numpy colorama
```

Legg til `.env` med:
```
GEMINI_API_KEY="din-nøkkel"
NOTION_API_KEY="din-nøkkel"
PERSONAL_ACCESS_TOKEN="din-github-pat"
```

For å køyre mesh-pipeline (krev CUDA GPU):
```bash
pip install torch hy3dgen
python generate_and_upload.py
```
