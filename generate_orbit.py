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
    # Model: Gemini 3.1 / Nano Banana 2
    model = "gemini-3.1-flash-image-preview"
    stem_name = Path(img_path).stem
    out_dir = Path("orbit-16") / stem_name
    out_dir.mkdir(parents=True, exist_ok=True)
    
    frames = []
    gif_path = out_dir / f"{stem_name}_orbit_16.gif"
    
    if gif_path.exists():
        print(f"{Fore.CYAN}{Style.DIM}Skipping completed 16-step orbit for {stem_name}{Style.RESET_ALL}")
        return

    # Persona and Rules (System Instruction)
    # Updated to 22.5° steps for 16 frames total (360 / 16 = 22.5)
    system_instruction = (
        "You are a product photography turntable.\n\n"
        "RULES:\n"
        "1. Generate EXACTLY 1 image per response. No text, no commentary, no questions.\n"
        "2. Rotate the subject exactly 22.5° clockwise around its vertical axis from the previous view.\n"
        "3. Sharp subject cutout against solid white background (#ffffff, 100% white).\n"
        "4. Maintain identical: lighting, scale, vertical position, camera distance, focal length.\n"
        "5. The object must NOT deform, gain, or lose detail between frames.\n"
        "6. Use the conversation history to maintain perfect consistency across the 360° orbit."
    )

    print(f"\n{Fore.CYAN}{Style.BRIGHT}Starting 16-STEP CHAT-BASED Orbit Generation for: {stem_name}")
    print(f"Goal: 16 frames (22.5° steps), White BG, orbit-16/ folder")
    print(f"----------------------------------------------------------{Style.RESET_ALL}")

    # Initialize a Chat Session for this specific chair
    chat = client.chats.create(
        model=model,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            thinking_config=types.ThinkingConfig(thinking_level="MINIMAL"),
            image_config=types.ImageConfig(
                aspect_ratio="1:1",
                image_size="512",
            ),
            response_modalities=["IMAGE", "TEXT"],
        )
    )

    for i in range(1, 17):
        frame_path = out_dir / f"{stem_name}_{i:02d}.png"
        
        # Check if frame exists locally (resuming)
        if frame_path.exists():
            print(f"{Fore.BLUE}Existing frame {i:02d} found in orbit-16. Re-syncing...{Style.RESET_ALL}")
            current_frame_img = Image.open(frame_path)
            frames.append(current_frame_img)
            continue

        print(f"{Fore.YELLOW}Generating frame {i:02d}/16 for {stem_name} (+22.5°)...{Style.RESET_ALL}")
        
        if i == 1:
            # First turn: Initial Image -> Front View (0 deg)
            msg = [
                "The provided image is the original reference. "
                "Render the object at 0° (front facing view) sharply against a solid white background (#ffffff).",
                Image.open(img_path)
            ]
        else:
            # Subsequent turns: 22.5° increment
            msg = f"Rotate the subject exactly 22.5° further clockwise from the last orientation."

        saved = False
        try:
            for chunk in chat.send_message_stream(msg):
                if chunk.parts is None:
                    continue
                for part in chunk.parts:
                    if part.inline_data and part.inline_data.data:
                        save_binary_file(str(frame_path), part.inline_data.data)
                        saved = True
                        frames.append(Image.open(frame_path))
                    elif part.text:
                        print(f"{Fore.MAGENTA}Model Text: {part.text}{Style.RESET_ALL}")
            
            if not saved:
                print(f"{Fore.RED}Failed to generate frame {i:02d} for {stem_name}{Style.RESET_ALL}")
                break
                
        except Exception as e:
            print(f"{Fore.RED}Error in frame {i:02d} for {stem_name}: {e}{Style.RESET_ALL}")
            break

    if len(frames) == 16:
        create_animations(stem_name, frames, out_dir, gif_path)

def create_animations(name, frames, out_dir, gif_path):
    print(f"\n{Fore.CYAN}Compiling 16-step orbit GIF for {name}...{Style.RESET_ALL}")
    try:
        processed_frames = [f.convert("P", palette=Image.ADAPTIVE) for f in frames]
        processed_frames[0].save(
            gif_path,
            save_all=True,
            append_images=processed_frames[1:],
            duration=80, # Faster duration for more frames (approx 12.5 fps)
            loop=0,
            optimize=True
        )
        print(f"{Fore.GREEN}16-step Orbit GIF created: {gif_path}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}GIF creation failed: {e}{Style.RESET_ALL}")

def process_all_images(limit=None):
    if not API_KEY:
        print(f"{Fore.RED}GEMINI_API_KEY missing.{Style.RESET_ALL}")
        return
    client = genai.Client(api_key=API_KEY)
    
    image_paths = sorted(glob.glob("NM_stolar/*.png") + glob.glob("bilete/*.png"))
    if limit:
        image_paths = image_paths[:limit]
        
    print(f"\n{Fore.CYAN}{Style.BRIGHT}==========================================")
    print(f" STARTING 16-STEP ORBIT GENERATION")
    print(f" Target folder: orbit-16/")
    print(f" Parallel workers: 10")
    print(f"=========================================={Style.RESET_ALL}\n")

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(generate_orbit_for_image, client, p) for p in image_paths]
        concurrent.futures.wait(futures)

if __name__ == "__main__":
    process_all_images(limit=None)
