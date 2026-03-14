#!/usr/bin/env python3
"""
generate_bguw_va.py — Generate white-background images for V&A chair images.
Source: bilete/VA/*.jpg
Output: bilete/VA_bguw/{stem}_bguw.png
"""

import os
import re
import concurrent.futures
from pathlib import Path
from PIL import Image
from google import genai
from google.genai import types
from colorama import init, Fore, Style

init(autoreset=True)

API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyDwoj-cEfQiZn-bHQ1rEcwUvHTgMvV4g_8")
SRC_DIR = Path("VA")
OUT_DIR = Path("VA_bguw")
MODEL = "gemini-3.1-flash-image-preview"
PROMPT = "place it sharp against solid white background, have the subject cut sharply, and background be #fff 100% white."


def save_binary_file(file_name, data):
    with open(file_name, "wb") as f:
        f.write(data)
    print(f"{Fore.GREEN}Saved: {file_name}{Style.RESET_ALL}")


def generate_bguw(client, img_path, out_path):
    if out_path.exists():
        print(f"{Fore.CYAN}{Style.DIM}Skip: {out_path.name} (exists){Style.RESET_ALL}")
        return

    try:
        img = Image.open(img_path)
        config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_level="MINIMAL"),
            image_config=types.ImageConfig(aspect_ratio="1:1", image_size="1K"),
            response_modalities=["IMAGE", "TEXT"],
        )

        print(f"{Fore.YELLOW}Generating: {img_path.name}...{Style.RESET_ALL}")

        saved = False
        for chunk in client.models.generate_content_stream(
            model=MODEL, contents=[PROMPT, img], config=config,
        ):
            if chunk.parts is None:
                continue
            for part in chunk.parts:
                if part.inline_data and part.inline_data.data:
                    save_binary_file(str(out_path), part.inline_data.data)
                    saved = True

        if not saved:
            print(f"{Fore.RED}No image generated for {img_path.name}{Style.RESET_ALL}")

    except Exception as e:
        print(f"{Fore.RED}Error {img_path.name}: {e}{Style.RESET_ALL}")


def main():
    if not API_KEY:
        print(f"{Fore.RED}Set GEMINI_API_KEY env var.{Style.RESET_ALL}")
        return

    client = genai.Client(api_key=API_KEY)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    all_images = sorted(list(SRC_DIR.glob("*.jpg")) + list(SRC_DIR.glob("*.png")))

    # Deduplicate: keep only the first image per unique object.
    # e.g. OK-17303_1.jpg, OK-17303_2.jpg → only process OK-17303_1.jpg
    seen = {}
    for img_path in all_images:
        base_id = re.sub(r'_\d+$', '', img_path.stem)
        if base_id not in seen:
            seen[base_id] = img_path

    images = list(seen.values())

    print(f"\n{Fore.CYAN}{Style.BRIGHT}==========================================")
    print(f" BGUW Generation - V&A chairs")
    print(f" Source: {SRC_DIR} ({len(all_images)} files, {len(images)} unique objects)")
    print(f" Output: {OUT_DIR}")
    print(f" Workers: 10")
    print(f"=========================================={Style.RESET_ALL}\n")

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for img_path in images:
            base_id = re.sub(r'_\d+$', '', img_path.stem)
            out_path = OUT_DIR / f"{base_id}_bguw.png"
            futures.append(executor.submit(generate_bguw, client, img_path, out_path))
        concurrent.futures.wait(futures)

    done = len(list(OUT_DIR.glob("*_bguw.png")))
    print(f"\n{Fore.GREEN}{Style.BRIGHT}Done! {done}/{len(images)} bguw images{Style.RESET_ALL}")


if __name__ == "__main__":
    main()
