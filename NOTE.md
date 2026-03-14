# TRELLIS.2 batch pipeline — 400+ chair images → GLB meshes

## System
- Windows 11 Pro, WSL2 Ubuntu
- AMD EPYC 7543P 32-Core, 28 GB RAM
- NVIDIA RTX A4500 (20 GB VRAM)
- Max resolution: 512³ (16 GB VRAM usage, 4 GB headroom)

## Goal
Batch-convert every image in the dataset to a textured 3D mesh (GLB with PBR materials) at the highest quality the GPU allows. Each image = one chair = one .glb output file. Must be fully automated, resumable, and log successes/failures.

## Setup

```bash
# In WSL2 Ubuntu:
git clone --recurse-submodules https://github.com/microsoft/TRELLIS.2.git
cd TRELLIS.2
source setup.sh --new-env   # creates conda env 'trellis2', pytorch 2.6.0 + CUDA 12.4

# If flash-attn fails on A4500, fall back:
export ATTN_BACKEND=xformers
pip install xformers

# Background removal preprocessor:
pip install rembg[gpu] onnxruntime-gpu
```

## Pipeline script requirements

Write a Python script `batch_chairs.py` that:

1. Takes `--input_dir` (folder of chair images, recursive) and `--output_dir`
2. Loads `Trellis2ImageTo3DPipeline.from_pretrained("microsoft/TRELLIS.2-4B")` ONCE
3. Loops all .png/.jpg/.jpeg/.webp images
4. Per image:
   - Load with PIL, resize to 1024×1024 square (pad, don't crop)
   - `pipeline.run(image)` → mesh
   - `o_voxel.postprocess.to_glb(mesh, simplify=500000, texture_size=2048, fill_holes=True)`
   - Save as `{stem}.glb` in output_dir
   - `torch.cuda.empty_cache()` + `gc.collect()` after each to prevent VRAM creep
5. Writes `batch_log.jsonl` — one JSON line per image: source path, output path, status (ok/error), elapsed seconds
6. `--resume` flag: reads batch_log.jsonl, skips images already marked "ok"
7. Catches exceptions per-image (don't crash the whole batch on one failure)

### Max quality settings for pipeline.run():

```python
# Set these env vars before importing torch:
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"

# The TRELLIS.2 API — check the actual pipeline.run() signature in the repo.
# Likely accepts kwargs or dict params. Target these values:
#   ss_guidance_strength: 8.5
#   ss_sampling_steps: 30
#   shape_slat_guidance_strength: 5.0
#   shape_slat_sampling_steps: 30
#   tex_slat_guidance_strength: 3.0
#   tex_slat_sampling_steps: 30
#   resolution: 512
```

### Background removal preprocessing (optional separate script):

```bash
rembg p ./raw_chairs ./clean_chairs
```

Or integrate inline: `from rembg import remove; image = remove(image)` before passing to pipeline.

## Run

```bash
conda activate trellis2

# Test one image first:
python batch_chairs.py -i ./chairs -o ./test_output --limit 1

# Full batch:
python batch_chairs.py -i ./chairs -o ./chair_meshes

# Resume after crash:
python batch_chairs.py -i ./chairs -o ./chair_meshes --resume
```

## Expected output

```
chair_meshes/
├── empire_stol_01.glb
├── thonet_14.glb
├── ...  (400+ files)
├── batch_log.jsonl
└── batch.log
```

~2 min/chair at max quality → ~13 hours for 400 chairs. Run overnight.

## Important

- Read the actual `pipeline.run()` signature in `trellis2/pipelines/` before coding — the param names may differ from the Gradio app. Check `app.py` in the repo for reference.
- `mesh.simplify(16777216)` before `to_glb()` — nvdiffrast hard limit.
- If VRAM OOM: lower ss_sampling_steps to 20, or texture_size to 1024.
- Monitor with `watch -n1 nvidia-smi` in a second terminal.