#!/usr/bin/env python3
"""
Rodin 3D Model Generator - NM_stolar (non-Norway collection)
=============================================================
Genererer 3D GLB-modellar frå bilete via Hyper3D Rodin nettside.
314 bilete frå image_urls_resten.txt.

OPPSETT (Windows):
    pip install playwright pyyaml
    playwright install chromium

BRUK:
    python nm_stolar_automate.py --headed
    python nm_stolar_automate.py --headed --timeout 600
"""

import asyncio
import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("Feil: playwright er ikkje installert.")
    print("Køyr: pip install playwright && playwright install chromium")
    sys.exit(1)

# ─── Konfigurasjon ────────────────────────────────────────────────────────────

SCRIPT_DIR  = Path(__file__).parent.resolve()
BASE_DIR    = SCRIPT_DIR.parent                        # stolar-db/
NM_DIR      = BASE_DIR / "NM_stolar"
IMAGE_URLS_FILE = NM_DIR / "image_urls_resten.txt"
JSON_FILE   = NM_DIR / "NM_stolar.json"
RODIN_URL   = "https://hyper3d.ai/rodin"

# ─── Hjelpefunksjonar ─────────────────────────────────────────────────────────

def load_image_list():
    """Les image_urls_resten.txt og returner liste med (filnamn, url) tuples."""
    images = []
    with open(IMAGE_URLS_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(": ", 1)
            if len(parts) != 2:
                continue
            images.append((parts[0], parts[1]))
    return images


def get_completed():
    """Finn kva bilete som allereie har GLB-filer."""
    done = set()
    for f in NM_DIR.glob("*.glb"):
        done.add(f.stem)
    return done


def get_remaining_images():
    """Returner bilete som manglar GLB-fil."""
    all_images = load_image_list()
    done = get_completed()
    remaining = []
    for filename, url in all_images:
        base = Path(filename).stem
        if base not in done:
            remaining.append((filename, url))
    return remaining


def update_json(updates: dict):
    """Oppdater NM_stolar.json med GLB-referansar."""
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        for obj in data:
            for img in obj.get("images", []) or []:
                fname = img.get("filename", "")
                if fname in updates:
                    img["glb"] = updates[fname]
                    obj["model3d"] = updates[fname]
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"  ⚠ JSON-feil: {e}")


# ─── JavaScript-mallar ───────────────────────────────────────────────────────

UPLOAD_JS = """
(async function() {{
  try {{
    const response = await fetch("{url}");
    if (!response.ok) return 'FETCH_FAILED_' + response.status;
    const blob = await response.blob();
    const file = new File([blob], "{filename}", {{ type: "image/jpeg" }});
    const inputs = document.querySelectorAll('input[type="file"]');
    let target = null;
    for (const input of inputs) {{
      if (input.accept && (input.accept.includes('.jpg') || input.accept.includes('image'))) {{
        target = input; break;
      }}
    }}
    if (!target) {{
      target = document.querySelector('input[type="file"]');
    }}
    if (!target) return 'NO_FILE_INPUT';
    const dt = new DataTransfer();
    dt.items.add(file);
    target.files = dt.files;
    target.dispatchEvent(new Event('change', {{ bubbles: true }}));
    target.dispatchEvent(new Event('input', {{ bubbles: true }}));
    return 'OK';
  }} catch(e) {{
    return 'ERROR_' + e.message;
  }}
}})();
"""

CLICK_CONFIRM_JS = """
() => {
    const allSpans = document.querySelectorAll('span');
    let found = [];
    for (const el of allSpans) {
        if (el.textContent === 'Confirm' && el.children.length === 0) {
            const rect = el.getBoundingClientRect();
            if (rect.width > 0) found.push({el, y: rect.y, w: rect.width});
        }
    }
    if (found.length === 0) return 'NO_CONFIRM';

    found.sort((a, b) => b.y - a.y);
    const span = found[0].el;

    let btn = span;
    for (let i = 0; i < 5; i++) {
        btn = btn.parentElement;
        if (!btn) break;
        const style = window.getComputedStyle(btn);
        if (style.backgroundImage && style.backgroundImage !== 'none') break;
    }
    if (!btn) return 'NO_BTN';

    const rect = btn.getBoundingClientRect();
    const cx = rect.x + rect.width / 2;
    const cy = rect.y + rect.height / 2;

    ['pointerdown','mousedown','pointerup','mouseup','click'].forEach(type => {
        const Cls = type.startsWith('pointer') ? PointerEvent : MouseEvent;
        btn.dispatchEvent(new Cls(type, {
            bubbles: true, cancelable: true, view: window,
            clientX: cx, clientY: cy, button: 0
        }));
    });
    return 'CLICKED_' + Math.round(cy);
}
"""

CONFIGURE_PACK_JS = """
() => {
    let actions = [];

    const allEls = document.querySelectorAll('*');
    for (const el of allEls) {
        if (el.textContent.trim() === '.glb' && el.children.length === 0) {
            const rect = el.getBoundingClientRect();
            if (rect.width > 0) {
                el.click();
                actions.push('clicked_glb');
                break;
            }
        }
    }

    for (const el of allEls) {
        if (el.textContent.trim() === 'Shaded' && el.children.length === 0) {
            const rect = el.getBoundingClientRect();
            if (rect.width > 0) {
                const parentArea = el.closest('div');
                if (parentArea) {
                    const svgs = parentArea.querySelectorAll('svg');
                    if (svgs.length > 0) {
                        parentArea.click();
                        actions.push('unchecked_shaded');
                    }
                }
                break;
            }
        }
    }

    return actions.join(',') || 'no_action';
}
"""

CLICK_DOWNLOAD_JS = """
() => {
    const allSpans = document.querySelectorAll('span');
    for (const el of allSpans) {
        if (el.textContent.trim() === 'Download' && el.children.length === 0) {
            const rect = el.getBoundingClientRect();
            if (rect.width > 0 && rect.y > 400) {
                let btn = el;
                for (let i = 0; i < 5; i++) {
                    btn = btn.parentElement;
                    if (!btn) break;
                    const style = window.getComputedStyle(btn);
                    if (style.cursor === 'pointer' ||
                        style.backgroundImage !== 'none' ||
                        btn.tagName === 'BUTTON' ||
                        btn.role === 'button') break;
                }
                if (btn) {
                    const r = btn.getBoundingClientRect();
                    ['pointerdown','mousedown','pointerup','mouseup','click'].forEach(type => {
                        const Cls = type.startsWith('pointer') ? PointerEvent : MouseEvent;
                        btn.dispatchEvent(new Cls(type, {
                            bubbles: true, cancelable: true, view: window,
                            clientX: r.x + r.width/2, clientY: r.y + r.height/2, button: 0
                        }));
                    });
                    return 'CLICKED';
                }
            }
        }
    }
    return 'NOT_FOUND';
}
"""

CHECK_STATE_JS = """
() => {
    const text = document.body.innerText;
    const url = window.location.href;

    const state = {
        url: url,
        hasModel: url.includes('/rodin/') && url.length > 35,
        hasGeometry: text.includes('Geometry') && !text.includes('PREPARING'),
        hasMaterial: text.includes('Material'),
        isGenerating: text.includes('Generating...'),
        hasRedo: text.includes('Redo'),
        hasConfirm: text.includes('Confirm'),
        hasPack: text.includes('Pack'),
        hasDownload: text.includes('Download'),
        hasGenerate: false,
        progress: '',
    };

    const spans = document.querySelectorAll('span');
    for (const s of spans) {
        if (s.textContent.trim() === 'Generate' && s.getBoundingClientRect().width > 0) {
            state.hasGenerate = true;
        }
    }

    const match = text.match(/(\\d+)%/);
    if (match) state.progress = match[1];

    return state;
}
"""


# ─── Prosessering av eitt bilete ─────────────────────────────────────────────

async def process_image(page, filename, url, timeout_s=600):
    """Full arbeidsflyt for eitt bilete. Returnerer (suksess, glb_path)."""
    base = Path(filename).stem
    glb_name = base + ".glb"
    glb_path = NM_DIR / glb_name
    t0 = time.time()

    def elapsed():
        return time.time() - t0

    def timed_out():
        return elapsed() > timeout_s

    print(f"\n  {'─'*45}")
    print(f"  📷 {filename}")

    try:
        # ── 1. Naviger til Rodin ──────────────────────────────────────────
        await page.goto(RODIN_URL, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)

        # ── 2. Last opp bilete ────────────────────────────────────────────
        js = UPLOAD_JS.format(url=url, filename=filename)
        result = await page.evaluate(js)
        if result != "OK":
            print(f"  ❌ Opplasting feila: {result}")
            return False, None
        print(f"  ✅ Opplasta ({elapsed():.0f}s)")
        await asyncio.sleep(2)

        # ── 3. Klikk GENERATE ─────────────────────────────────────────────
        try:
            gen = page.locator("text=GENERATE").first
            await gen.click(timeout=60000)
            await asyncio.sleep(2)
            try:
                await page.locator("text=GENERATE").first.click(timeout=5000)
            except:
                pass
            print(f"  🔄 GENERATE klikka ({elapsed():.0f}s)")
        except Exception as e:
            print(f"  ❌ GENERATE feila: {e}")
            return False, None

        # ── 4. Vent på modell-URL ─────────────────────────────────────────
        while not timed_out():
            state = await page.evaluate(CHECK_STATE_JS)
            if state["hasModel"]:
                break
            await asyncio.sleep(3)

        if timed_out():
            print(f"  ⏰ Timeout ved modell-URL")
            return False, None

        print(f"  🔗 Modell laga ({elapsed():.0f}s)")

        # ── 5. Vent på geometri + material ────────────────────────────────
        material_generate_clicked = False
        while not timed_out():
            state = await page.evaluate(CHECK_STATE_JS)

            if (state["hasMaterial"] and state["hasGenerate"]
                and not state["isGenerating"] and not material_generate_clicked):
                try:
                    await page.locator("text=Generate").first.click(timeout=5000)
                    material_generate_clicked = True
                    print(f"  🎨 Material generering starta ({elapsed():.0f}s)")
                except:
                    pass

            if state["hasRedo"] and state["hasConfirm"]:
                break

            if state["isGenerating"] and state["progress"]:
                print(f"  ... genererer {state['progress']}%", end="\r")

            await asyncio.sleep(3)

        if timed_out():
            print(f"  ⏰ Timeout ved material")
            return False, None

        print(f"  🎨 Material ferdig ({elapsed():.0f}s)")
        await asyncio.sleep(1)

        # ── 6. Klikk Material Confirm ─────────────────────────────────────
        for attempt in range(5):
            result = await page.evaluate(CLICK_CONFIRM_JS)
            print(f"  🔘 Confirm: {result} ({elapsed():.0f}s)")
            if "CLICKED" in str(result):
                break
            await asyncio.sleep(2)

        await asyncio.sleep(3)

        for _ in range(20):
            state = await page.evaluate(CHECK_STATE_JS)
            if not state["hasRedo"]:
                break
            await page.evaluate(CLICK_CONFIRM_JS)
            await asyncio.sleep(2)

        await asyncio.sleep(2)

        # ── 7. Konfigurer Pack (.glb, ikkje Shaded) ──────────────────────
        result = await page.evaluate(CONFIGURE_PACK_JS)
        print(f"  📦 Pack: {result} ({elapsed():.0f}s)")
        await asyncio.sleep(1)

        # ── 8. Last ned ──────────────────────────────────────────────────
        try:
            async with page.expect_download(timeout=60000) as download_info:
                await page.evaluate(CLICK_DOWNLOAD_JS)
            download = await download_info.value

            await download.save_as(str(glb_path))
            size_mb = glb_path.stat().st_size / (1024 * 1024)

            if size_mb < 0.5:
                print(f"  ❌ For lita fil ({size_mb:.1f}MB)")
                glb_path.unlink()
                return False, None

            print(f"  ✅ FERDIG: {glb_name} ({size_mb:.1f}MB) [{elapsed():.0f}s]")
            return True, glb_path

        except PlaywrightTimeout:
            print(f"  ⚠ Download-event timeout, prøver fallback...")
            await page.evaluate(CLICK_DOWNLOAD_JS)
            await asyncio.sleep(10)

            for check_dir in [BASE_DIR, Path.home() / "Downloads"]:
                candidate = check_dir / "base_basic_pbr.glb"
                if candidate.exists() and candidate.stat().st_size > 500000:
                    shutil.move(str(candidate), str(glb_path))
                    size_mb = glb_path.stat().st_size / (1024 * 1024)
                    print(f"  ✅ FERDIG (fallback): {glb_name} ({size_mb:.1f}MB)")
                    return True, glb_path

            print(f"  ❌ Nedlasting feila")
            return False, None

    except Exception as e:
        print(f"  ❌ Uventa feil: {e}")
        return False, None


# ─── Hovudprogram ────────────────────────────────────────────────────────────

async def main():
    parser = argparse.ArgumentParser(
        description="Automatiser 3D-modellgenerering for NM_stolar-samling"
    )
    parser.add_argument("--timeout", type=int, default=600,
                        help="Timeout per bilete i sekund (standard: 600)")
    parser.add_argument("--headed", action="store_true", default=True,
                        help="Vis nettlesaren (standard: ja)")
    parser.add_argument("--headless", action="store_true",
                        help="Køyr utan synleg nettlesar")
    parser.add_argument("--max-retries", type=int, default=2,
                        help="Maks forsøk per bilete (standard: 2)")
    args = parser.parse_args()

    headless = args.headless and not args.headed

    if not IMAGE_URLS_FILE.exists():
        print(f"Feil: Finn ikkje {IMAGE_URLS_FILE}")
        sys.exit(1)

    remaining = get_remaining_images()
    total = len(load_image_list())
    done_count = total - len(remaining)

    print(f"")
    print(f"  ╔══════════════════════════════════════════╗")
    print(f"  ║  🪑 Rodin 3D NM_stolar-Automatisering   ║")
    print(f"  ║  Totalt: {total:>4} bilete                    ║")
    print(f"  ║  Ferdige: {done_count:>3}  |  Att: {len(remaining):>3}               ║")
    print(f"  ║  Timeout: {args.timeout:>3}s  |  Forsøk: {args.max_retries}            ║")
    print(f"  ╚══════════════════════════════════════════╝")
    print(f"")

    if not remaining:
        print("  ✅ Alle bilete er allereie prosesserte!")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ]
        )
        context = await browser.new_context(
            accept_downloads=True,
            viewport={"width": 1280, "height": 1024},
        )

        # ── Manuell innlogging ────────────────────────────────────────────
        print("  ⚠️  INNLOGGING KREVST")
        print("  1. Ein nettlesar opnar seg no")
        print("  2. Logg inn på hyper3d.ai (Google/Discord/etc)")
        print("  3. Trykk ENTER her i terminalen når du er innlogga")
        print("")

        login_page = await context.new_page()
        await login_page.goto("https://hyper3d.ai/rodin", wait_until="domcontentloaded")

        input("  👉 Trykk ENTER når du er innlogga... ")
        await login_page.close()

        # ── Prosessering ──────────────────────────────────────────────────
        success_count = 0
        fail_count = 0
        failed_images = []

        for i, (filename, url) in enumerate(remaining):
            base = Path(filename).stem
            glb_name = base + ".glb"

            print(f"\n{'='*50}")
            print(f"  [{done_count + i + 1}/{total}] {filename}")
            print(f"{'='*50}")

            success = False
            for attempt in range(args.max_retries):
                if attempt > 0:
                    print(f"\n  🔁 Forsøk {attempt + 1}/{args.max_retries}")

                page = await context.new_page()
                ok, path = await process_image(page, filename, url, args.timeout)

                try:
                    await page.close()
                except:
                    pass

                if ok:
                    success = True
                    update_json({filename: glb_name})
                    success_count += 1
                    break

                await asyncio.sleep(5)

            if not success:
                fail_count += 1
                failed_images.append(filename)
                print(f"  ❌ HOPPA OVER: {filename}")

        # ── Oppsummering ──────────────────────────────────────────────────
        final_done = len(get_completed())
        print(f"\n")
        print(f"  ╔══════════════════════════════════════════╗")
        print(f"  ║  RESULTAT                                ║")
        print(f"  ║  GLB-filer: {final_done:>3}/{total}                     ║")
        print(f"  ║  Nye: {success_count:>3}  |  Feila: {fail_count:>3}              ║")
        print(f"  ╚══════════════════════════════════════════╝")

        if failed_images:
            print(f"\n  Feila bilete:")
            for fn in failed_images:
                print(f"    - {fn}")

        await context.close()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
