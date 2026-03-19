#!/usr/bin/env python3
"""gen_pbr_glb.py — PBR 3D chair pipeline. Run 24/7, restart anytime."""

import gc, json, os, re, subprocess, sys, threading, time, traceback, warnings, logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue

warnings.filterwarnings("ignore")
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
logging.disable(logging.WARNING)

import fast_simplification, numpy as np, requests, trimesh
from colorama import Fore, Style, init as colorama_init
from PIL import Image

colorama_init()

os.add_dll_directory(os.path.join(sys.prefix, "Lib", "site-packages", "torch", "lib"))
cb = r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.1\bin"
if os.path.isdir(cb): os.add_dll_directory(cb)

BASE = __import__('pathlib').Path(__file__).parent
SRC, OUT = BASE / "STOLAR" / "bguw", BASE / "STOLAR" / "glb"
LOG = BASE / "gen_pbr_glb.log"
BATCH, MAX_FACES = 10, 100_000
SHAPE_STEPS, GUIDANCE = 50, 5.0  # 50 steps = full quality geometry

NOTION_TOKEN = ""
ef = BASE / ".env"
if ef.exists():
    for line in ef.read_text(encoding="utf-8").splitlines():
        if line.startswith("NOTION_API_KEY="):
            NOTION_TOKEN = line.split("=", 1)[1].strip().strip('"')

DB_ID = "405e0f64-6b77-4aab-88b8-73281e58c4f0"
GH_RAW = "https://raw.githubusercontent.com/lukketsvane/stolar-db/main/STOLAR/glb"
N_HDR = {"Authorization": f"Bearer {NOTION_TOKEN}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"}
G, R, Y, C, D, B, RST = Fore.GREEN, Fore.RED, Fore.YELLOW, Fore.CYAN, Style.DIM, Style.BRIGHT, Style.RESET_ALL


def build_heights():
    h = {}
    for src in ["va_heights.json", "va_heights_partial.json"]:
        p = BASE / src
        if not p.exists(): continue
        for oid, val in json.loads(p.read_text(encoding="utf-8")).items():
            v = val[0] if isinstance(val, list) else val
            try:
                f = float(str(v).replace(",", ".").strip())
                if f > 0: h.setdefault(oid, f)
            except: pass
    for jf in (BASE / "noreg").rglob("*.json") if (BASE / "noreg").exists() else []:
        try:
            jd = json.loads(jf.read_text(encoding="utf-8"))
            m = re.search(r'\bH[^\d]*(\d+[,.]?\d*)', str(jd.get("Mål", "")))
            if m and jd.get("objectId"):
                f = float(m.group(1).replace(",", "."))
                if f > 0: h.setdefault(jd["objectId"], f)
        except: pass
    return h


def decimate(mesh):
    if len(mesh.faces) <= MAX_FACES: return mesh
    v, f = fast_simplification.simplify(mesh.vertices, mesh.faces, target_reduction=1.0 - MAX_FACES / len(mesh.faces))
    return trimesh.Trimesh(vertices=v, faces=f, process=False)


# ── Upload (background) ──
upload_q, upload_lock, ncache, nloaded = Queue(), threading.Lock(), {}, threading.Event()

def load_notion():
    global ncache
    pages, has_more, cur = {}, True, None
    while has_more:
        body = {"page_size": 100}
        if cur: body["start_cursor"] = cur
        r = None
        for a in range(3):
            try:
                r = requests.post(f"https://api.notion.com/v1/databases/{DB_ID}/query", headers=N_HDR, json=body, timeout=30)
                if r.status_code == 200: break
            except: pass
            time.sleep(5*(a+1))
        if not r or r.status_code != 200: break
        d = r.json()
        for p in d["results"]:
            rt = p["properties"].get("Objekt-ID", {}).get("rich_text", [])
            oid = rt[0]["plain_text"] if rt else ""
            if oid: pages[oid] = {"pid": p["id"], "has": len(p["properties"].get("3D-modell", {}).get("files", [])) > 0}
        has_more, cur = d.get("has_more", False), d.get("next_cursor")
    ncache = pages; nloaded.set()

def notion_update(pid, oid):
    url = f"{GH_RAW}/{oid}.glb"
    pl = {"properties": {"3D-modell": {"files": [{"type": "external", "name": f"{oid}.glb", "external": {"url": url}}]}}}
    for a in range(3):
        try:
            r = requests.patch(f"https://api.notion.com/v1/pages/{pid}", headers=N_HDR, json=pl, timeout=30)
            if r.status_code == 429: time.sleep(10*(a+1)); continue
            return r.status_code == 200
        except: time.sleep(3)
    return False

def git_push(oids):
    with upload_lock:
        try:
            lk = BASE / ".git" / "index.lock"
            if lk.exists():
                try: lk.unlink()
                except: pass
            res = subprocess.run(["git", "ls-files", "--others", "--exclude-standard", "STOLAR/"], cwd=str(BASE), capture_output=True, text=True)
            unt = [f for f in res.stdout.strip().split("\n") if f.endswith(".glb") and "_prescale" not in f and f.strip()]
            if not unt: return
            for _ in range(3):
                lk = BASE / ".git" / "index.lock"
                if lk.exists():
                    try: lk.unlink()
                    except: time.sleep(2); continue
                if subprocess.run(["git", "add"] + unt, cwd=str(BASE), capture_output=True).returncode == 0: break
                time.sleep(3)
            subprocess.run(["git", "commit", "-m", f"feat: add {len(unt)} PBR 3D chair models"], cwd=str(BASE), capture_output=True)
            for _ in range(3):
                subprocess.run(["git", "fetch", "origin", "main"], cwd=str(BASE), capture_output=True)
                mg = subprocess.run(["git", "merge", "origin/main", "--no-edit"], cwd=str(BASE), capture_output=True, text=True)
                if mg.returncode != 0 and "untracked working tree files" in (mg.stderr or ""):
                    for ln in mg.stderr.splitlines():
                        ln = ln.strip()
                        if ln.endswith("_bguw.png") and (BASE / ln).exists(): (BASE / ln).unlink()
                    subprocess.run(["git", "merge", "origin/main", "--no-edit"], cwd=str(BASE), capture_output=True)
                if subprocess.run(["git", "push"], cwd=str(BASE), capture_output=True).returncode == 0:
                    print(f"\r  {D}↑ pushed {len(unt)} GLBs{RST}"); break
                time.sleep(5)
            time.sleep(2); nloaded.wait()
            upd = [(oid, ncache[oid]["pid"]) for oid in oids if oid in ncache and not ncache[oid]["has"]]
            if upd:
                ok = 0
                with ThreadPoolExecutor(max_workers=10) as ex:
                    futs = {ex.submit(notion_update, pid, oid): oid for oid, pid in upd}
                    for f in as_completed(futs):
                        try:
                            if f.result(): ok += 1; ncache[futs[f]]["has"] = True
                        except: pass
                if ok: print(f"\r  {D}↑ notion {ok}/{len(upd)}{RST}")
        except Exception as e:
            print(f"  {R}upload err: {e}{RST}")

def uploader():
    pending = []
    while True:
        oid = upload_q.get()
        if oid is None:
            if pending: git_push(pending)
            break
        pending.append(oid)
        if len(pending) >= BATCH: git_push(pending); pending = []


# ── Pre-process next image on CPU while GPU works ──
preprocess_result = {}
preprocess_lock = threading.Lock()

def preprocess_image(oid, img_path, rembg_fn):
    """Run rembg (CPU-heavy) in background thread."""
    try:
        src = Image.open(img_path).convert("RGB")
        rembg_img = rembg_fn(src)
        with preprocess_lock:
            preprocess_result[oid] = (src, rembg_img)
    except Exception as e:
        with preprocess_lock:
            preprocess_result[oid] = e


def main():
    import torch
    from hy3dgen.rembg import BackgroundRemover
    from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline
    from hy3dgen.texgen import Hunyuan3DPaintPipeline

    print(f"\n  {B}{C}PBR Chair Pipeline{RST}  {D}gen_pbr_glb.py{RST}")
    print(f"  {D}steps={SHAPE_STEPS} guidance={GUIDANCE} faces≤{MAX_FACES//1000}K{RST}\n")

    assert torch.cuda.is_available(), "No CUDA!"

    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
    torch.backends.cudnn.benchmark = True
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True
    torch.set_float32_matmul_precision('high')

    heights = build_heights()
    entries, skipped = [], 0
    for p in sorted(SRC.glob("*_bguw.png")):
        oid = p.stem.replace("_bguw", "")
        if (OUT / f"{oid}.glb").exists(): skipped += 1; continue
        entries.append((oid, p))

    total = len(entries)
    print(f"  {G}{total}{RST} to process  {D}{skipped} done{RST}\n")
    if not total: print(f"  {G}All done!{RST}"); return

    OUT.mkdir(parents=True, exist_ok=True)
    threading.Thread(target=load_notion, daemon=True).start()
    ut = threading.Thread(target=uploader, daemon=True); ut.start()

    old_level = logging.root.level; logging.disable(logging.CRITICAL)
    print(f"  {D}loading pipelines...{RST}", end="", flush=True)

    shape = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained("tencent/Hunyuan3D-2", device="cuda")
    shape.to("cuda")
    rembg = BackgroundRemover()
    paint = Hunyuan3DPaintPipeline.from_pretrained("tencent/Hunyuan3D-2")

    vram = torch.cuda.memory_allocated() / 1024**3
    total_vram = torch.cuda.get_device_properties(0).total_mem / 1024**3
    print(f"\r  {G}✓{RST} pipelines loaded  {D}({vram:.1f}/{total_vram:.0f}GB VRAM){RST}\n")
    logging.disable(old_level)

    log = open(LOG, "a", encoding="utf-8")
    log.write(f"\n=== {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")

    done = failed = 0
    t_start = time.time()

    # Pre-process first image while pipelines are ready
    if entries:
        oid0, path0 = entries[0]
        preprocess_image(oid0, path0, rembg)

    for i, (oid, img_path) in enumerate(entries):
        glb = OUT / f"{oid}.glb"
        if glb.exists(): continue

        # Kick off pre-processing of NEXT image in background
        if i + 1 < len(entries):
            next_oid, next_path = entries[i + 1]
            if next_oid not in preprocess_result:
                t = threading.Thread(target=preprocess_image, args=(next_oid, next_path, rembg), daemon=True)
                t.start()

        t0 = time.time()
        try:
            OUT.mkdir(parents=True, exist_ok=True)

            # Get pre-processed image (or process now if not ready)
            with preprocess_lock:
                cached = preprocess_result.pop(oid, None)
            if isinstance(cached, tuple):
                src, rembg_img = cached
            elif isinstance(cached, Exception):
                raise cached
            else:
                src = Image.open(img_path).convert("RGB")
                rembg_img = rembg(src)

            # ── Shape (GPU 100%) ──
            print(f"  {D}[{i+1:03d}/{total}]{RST} {oid} ", end="", flush=True)
            mesh = shape(image=rembg_img, num_inference_steps=SHAPE_STEPS, guidance_scale=GUIDANCE, enable_pbar=False)[0]

            h_cm = heights.get(oid)
            if h_cm:
                ch = float(mesh.bounds[1][1] - mesh.bounds[0][1])
                if ch <= 0: ch = float(mesh.extents.max())
                if ch > 0: mesh.apply_scale((h_cm / 100.0) / ch)
                note = f"{h_cm}cm"
            else:
                note = "—"
            t_shape = time.time() - t0

            # ── Decimate + Texture (GPU 100%) ──
            mesh = decimate(mesh)
            textured = paint(mesh, src)
            textured.export(str(glb))

            elapsed = time.time() - t0
            done += 1
            rate = done / (time.time() - t_start) * 3600
            eta = (total - i - 1) / rate if rate > 0 else 0

            print(f"{G}✓{RST} {D}{t_shape:.0f}s+{elapsed-t_shape:.0f}s={B}{elapsed:.0f}s{RST}  "
                  f"{Y}{note}{RST}  {D}{rate:.0f}/hr ETA {eta:.1f}h{RST}")

            log.write(f"OK [{i+1:03d}] {oid} {note} {elapsed:.0f}s\n"); log.flush()
            upload_q.put(oid)

        except Exception as e:
            elapsed = time.time() - t0
            print(f"{R}✗ {e}{RST} {D}({elapsed:.0f}s){RST}")
            log.write(f"FAIL [{i+1:03d}] {oid} {e}\n"); log.flush()
            failed += 1

        finally:
            torch.cuda.empty_cache(); gc.collect()

    upload_q.put(None); ut.join(timeout=300); log.close()
    h = (time.time() - t_start) / 3600
    print(f"\n  {C}{'═'*50}{RST}")
    print(f"  {G}{done}{RST} done  {D}{skipped} skipped  {R if failed else D}{failed} failed  {D}{h:.1f}h ({done/(h or 1):.0f}/hr){RST}")
    print(f"  {C}{'═'*50}{RST}\n")


if __name__ == "__main__":
    main()
