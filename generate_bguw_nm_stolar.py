#!/usr/bin/env python3
"""
generate_bguw_nm_stolar.py — Generate white-background images for all chair
images in NM_stolar/ subdirectories using Gemini 3.1 Flash.

Output: bilete/images_bguw_NM_stolar/{stem}_bguw.png
Resumable: skips existing outputs.
"""

import os
import glob
import concurrent.futures
from pathlib import Path
from PIL import Image
from google import genai
from google.genai import types
from colorama import init, Fore, Style

init(autoreset=True)

API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyDwoj-cEfQiZn-bHQ1rEcwUvHTgMvV4g_8b")
OUT_DIR = Path("bilete/images_bguw_NM_stolar")
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
            image_config=types.ImageConfig(
                aspect_ratio="1:1",
                image_size="1K",
            ),
            response_modalities=["IMAGE", "TEXT"],
        )

        print(f"{Fore.YELLOW}Generating: {img_path.name}...{Style.RESET_ALL}")

        saved = False
        for chunk in client.models.generate_content_stream(
            model=MODEL,
            contents=[PROMPT, img],
            config=config,
        ):
            if chunk.parts is None:
                continue
            for part in chunk.parts:
                if part.inline_data and part.inline_data.data:
                    save_binary_file(str(out_path), part.inline_data.data)
                    saved = True
                elif part.text:
                    print(f"{Fore.MAGENTA}Text: {part.text}{Style.RESET_ALL}")

        if not saved:
            print(f"{Fore.RED}No image generated for {img_path.name}{Style.RESET_ALL}")

    except Exception as e:
        print(f"{Fore.RED}Error {img_path.name}: {e}{Style.RESET_ALL}")


def main():
    if not API_KEY:
        print(f"{Fore.RED}GEMINI_API_KEY not set.{Style.RESET_ALL}")
        return

    client = genai.Client(api_key=API_KEY)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Collect all images from NM_stolar subdirectories
    image_paths = sorted(
        Path(p) for pattern in ("NM_stolar/*/*.png", "NM_stolar/*/*.jpg")
        for p in glob.glob(pattern)
    )

    print(f"\n{Fore.CYAN}{Style.BRIGHT}==========================================")
    print(f" BGUW Generation — NM_stolar")
    print(f" Source images: {len(image_paths)}")
    print(f" Output: {OUT_DIR}")
    print(f" Workers: 10")
    print(f"=========================================={Style.RESET_ALL}\n")

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for img_path in image_paths:
            stem = img_path.stem
            out_path = OUT_DIR / f"{stem}_bguw.png"
            futures.append(executor.submit(generate_bguw, client, img_path, out_path))

        concurrent.futures.wait(futures)

    done = len(list(OUT_DIR.glob("*_bguw.png")))
    print(f"\n{Fore.GREEN}{Style.BRIGHT}Done! {done}/{len(image_paths)} bguw images in {OUT_DIR}{Style.RESET_ALL}")


if __name__ == "__main__":
    main()
