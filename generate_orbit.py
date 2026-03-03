import os
import glob
import concurrent.futures
from pathlib import Path
from PIL import Image
import numpy as np
import cv2
from dotenv import load_dotenv
from google import genai
from google.genai import types
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Load environment and API key
load_dotenv()
API_KEY = os.environ.get("GEMINI_API_KEY")

def save_binary_file(file_name, data):
    with open(file_name, "wb") as f:
        f.write(data)
    print(f"{Fore.GREEN}Frame saved: {file_name}{Style.RESET_ALL}")

def generate_orbit_for_image(client, img_path):
    model = "gemini-3.1-flash-image-preview"
    source_name = Path(img_path).name
    stem_name = Path(img_path).stem
    out_dir = Path("orbit") / stem_name
    out_dir.mkdir(parents=True, exist_ok=True)
    
    black_bg_path = Path("bg-uniform black") / source_name
    
    frames = []
    
    print(f"\n{Fore.CYAN}{Style.BRIGHT}Starting Orbit Generation (Product Turntable Mode) for: {stem_name}")
    print(f"Goal: 8 frames (45° steps), 512x512px, Black BG")
    print(f"----------------------------------------------------------{Style.RESET_ALL}")

    # Persona and Rules
    system_instruction = (
        "You are a product photography turntable.\n\n"
        "RULES:\n"
        "1. Generate EXACTLY 1 image per response. No text, no commentary, no questions.\n"
        "2. Rotate the subject exactly 45° clockwise around its vertical axis from the previous view.\n"
        "3. Sharp subject cutout against solid black background (#000000, 100% black).\n"
        "4. Maintain identical: lighting, scale, vertical position, camera distance, focal length.\n"
        "5. The object must NOT deform, gain, or lose detail between frames.\n"
        "6. Use the provided input image(s) as reference. Rotate 45° clockwise from the designated orientation.\n"
        "7. If multiple images are provided, use the original for detail and the black-background version as the 0° starting point."
    )

    current_input_img = None # Will be set to the previous frame image

    for i in range(1, 9):
        frame_path = out_dir / f"{stem_name}_{i:02d}.png"
        
        if frame_path.exists():
            print(f"{Fore.BLUE}Skipping existing frame {i:02d}{Style.RESET_ALL}")
            current_frame_img = Image.open(frame_path)
            frames.append(current_frame_img)
            current_input_img = current_frame_img
            continue

        print(f"{Fore.YELLOW}Generating frame {i:02d}/08 (Rotating +45°)...{Style.RESET_ALL}")
        
        # Build prompt and contents
        if i == 1:
            # First frame generation: Original + Black BG (0°)
            prompt = (
                f"{system_instruction}\n\n"
                "Attached are the original image and the black-background (0° front) reference. "
                "Generate a new version rotated 45° clockwise from the 0° front orientation."
            )
            contents = [prompt, Image.open(img_path)]
            if black_bg_path.exists():
                contents.append(Image.open(black_bg_path))
        else:
            # Subsequent frames: Just the previous frame
            prompt = (
                f"{system_instruction}\n\n"
                "The provided image is the previous frame in the sequence. "
                "Rotate the subject exactly 45° further clockwise from this orientation."
            )
            contents = [prompt, current_input_img]
            
        generate_content_config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_level="MINIMAL"),
            image_config=types.ImageConfig(
                aspect_ratio="1:1",
                image_size="512",
            ),
            response_modalities=["IMAGE", "TEXT"],
        )

        saved = False
        try:
            for chunk in client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=generate_content_config,
            ):
                if chunk.parts is None:
                    continue
                for part in chunk.parts:
                    if part.inline_data and part.inline_data.data:
                        save_binary_file(str(frame_path), part.inline_data.data)
                        saved = True
                        current_input_img = Image.open(frame_path)
                        frames.append(current_input_img)
                    elif part.text:
                        print(f"{Fore.MAGENTA}Model Text: {part.text}{Style.RESET_ALL}")
            
            if not saved:
                print(f"{Fore.RED}Failed to generate frame {i:02d}{Style.RESET_ALL}")
                break
                
        except Exception as e:
            print(f"{Fore.RED}Error in frame {i:02d}: {e}{Style.RESET_ALL}")
            break

    if len(frames) == 8:
        create_animations(stem_name, frames, out_dir)

def create_animations(name, frames, out_dir):
    print(f"\n{Fore.CYAN}Compiling orbit animations for {name}...{Style.RESET_ALL}")
    
    gif_path = out_dir / f"{name}_orbit.gif"
    processed_frames = [f.convert("P", palette=Image.ADAPTIVE) for f in frames]
    processed_frames[0].save(
        gif_path,
        save_all=True,
        append_images=processed_frames[1:],
        duration=125,
        loop=0,
        optimize=True
    )
    print(f"{Fore.GREEN}GIF: {gif_path}{Style.RESET_ALL}")

    webm_path = out_dir / f"{name}_orbit.webm"
    try:
        height, width = frames[0].size
        fourcc = cv2.VideoWriter_fourcc(*'VP80')
        video = cv2.VideoWriter(str(webm_path), fourcc, 8.0, (width, height))
        for frame in frames:
            cv_img = cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR)
            video.write(cv_img)
        video.release()
        print(f"{Fore.GREEN}WebM: {webm_path}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}WebM failed: {e}{Style.RESET_ALL}")

def main():
    if not API_KEY:
        print(f"{Fore.RED}GEMINI_API_KEY missing.{Style.RESET_ALL}")
        return
    client = genai.Client(api_key=API_KEY)
    test_image = "NM_stolar/NMK.2005.0638_09013.png"
    if os.path.exists(test_image):
        generate_orbit_for_image(client, test_image)
    else:
        pngs = glob.glob("bilete/*.png")
        if pngs:
            generate_orbit_for_image(client, pngs[0])

if __name__ == "__main__":
    main()
