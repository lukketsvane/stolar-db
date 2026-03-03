import os
import glob
import concurrent.futures
from pathlib import Path
from PIL import Image
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
    
    # Check if the GIF is already fully generated to allow fast resuming
    gif_path = out_dir / f"{stem_name}_orbit.gif"
    if gif_path.exists():
        print(f"{Fore.CYAN}{Style.DIM}Skipping completed orbit for {stem_name}{Style.RESET_ALL}")
        return

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

    current_input_img = None

    for i in range(1, 9):
        frame_path = out_dir / f"{stem_name}_{i:02d}.png"
        
        if frame_path.exists():
            print(f"{Fore.BLUE}Skipping existing frame {i:02d} for {stem_name}{Style.RESET_ALL}")
            current_frame_img = Image.open(frame_path)
            frames.append(current_frame_img)
            current_input_img = current_frame_img
            continue

        print(f"{Fore.YELLOW}Generating frame {i:02d}/08 for {stem_name} (Rotating +45°)...{Style.RESET_ALL}")
        
        # Build prompt and contents
        if i == 1:
            prompt = (
                f"{system_instruction}\n\n"
                "Attached are the original image and the black-background (0° front) reference. "
                "Generate a new version rotated 45° clockwise from the 0° front orientation."
            )
            contents = [prompt, Image.open(img_path)]
            if black_bg_path.exists():
                contents.append(Image.open(black_bg_path))
        else:
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
                print(f"{Fore.RED}Failed to generate frame {i:02d} for {stem_name}{Style.RESET_ALL}")
                break
                
        except Exception as e:
            print(f"{Fore.RED}Error in frame {i:02d} for {stem_name}: {e}{Style.RESET_ALL}")
            break

    if len(frames) == 8:
        create_animations(stem_name, frames, out_dir, gif_path)

def create_animations(name, frames, out_dir, gif_path):
    print(f"\n{Fore.CYAN}Compiling orbit animations for {name}...{Style.RESET_ALL}")
    
    try:
        processed_frames = [f.convert("P", palette=Image.ADAPTIVE) for f in frames]
        processed_frames[0].save(
            gif_path,
            save_all=True,
            append_images=processed_frames[1:],
            duration=125,
            loop=0,
            optimize=True
        )
        print(f"{Fore.GREEN}GIF created: {gif_path}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}GIF creation failed: {e}{Style.RESET_ALL}")

    # Video compilation skipped as per user request
    print(f"{Fore.CYAN}Skipping WebM/MP4 compilation (OpenCV bypassed).{Style.RESET_ALL}")

def process_all_images(limit=None):
    if not API_KEY:
        print(f"{Fore.RED}{Style.BRIGHT}GEMINI_API_KEY missing from .env{Style.RESET_ALL}")
        return

    client = genai.Client(api_key=API_KEY)
    
    image_paths = []
    image_paths.extend(glob.glob("NM_stolar/*.png"))
    image_paths.extend(glob.glob("bilete/*.png"))
    image_paths = sorted(image_paths)
    
    if limit is not None:
        image_paths = image_paths[:limit]
        
    print(f"\n{Fore.CYAN}{Style.BRIGHT}==========================================")
    print(f" STARTING FULL ORBIT GENERATION")
    print(f" Source images: {len(image_paths)}")
    print(f" Parallel workers: 10")
    print(f"=========================================={Style.RESET_ALL}\n")

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for img_path in image_paths:
            futures.append(executor.submit(generate_orbit_for_image, client, img_path))
        
        concurrent.futures.wait(futures)

if __name__ == "__main__":
    process_all_images(limit=None)
