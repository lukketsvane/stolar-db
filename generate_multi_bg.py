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
    # Print in green for success
    print(f"{Fore.GREEN}File saved: {file_name}{Style.RESET_ALL}")

def generate_image_task(client, img_path, color_name, hex_code, out_dir, prompt_suffix=""):
    model = "gemini-3.1-flash-image-preview"
    prompt = f"place it sharp against solid {color_name} background, have the subject cut sharply, and bacground be {hex_code} 100% {color_name}."
    if prompt_suffix:
        prompt += f" {prompt_suffix}"
    
    out_dir = Path(out_dir)
    out_dir.mkdir(exist_ok=True)
    file_name = out_dir / Path(img_path).name
    
    # Check if already exists to skip
    if file_name.exists():
        # Print in dim/cyan for skip
        print(f"{Fore.CYAN}{Style.DIM}Skipping {file_name}, already exists.{Style.RESET_ALL}")
        return

    try:
        img = Image.open(img_path)
        
        generate_content_config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_level="MINIMAL"),
            image_config=types.ImageConfig(
                aspect_ratio="1:1",
                image_size="2K",
            ),
            response_modalities=["IMAGE", "TEXT"],
        )

        saved = False
        print(f"{Fore.YELLOW}Generating {color_name} for {img_path}...{Style.RESET_ALL}")
        
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=[prompt, img],
            config=generate_content_config,
        ):
            if chunk.parts is None:
                continue
            for part in chunk.parts:
                if part.inline_data and part.inline_data.data:
                    save_binary_file(str(file_name), part.inline_data.data)
                    saved = True
                elif part.text:
                    print(f"{Fore.MAGENTA}Text [{color_name}]: {part.text}{Style.RESET_ALL}")
        
        if not saved:
            print(f"{Fore.RED}No image generated for {img_path} ({color_name}){Style.RESET_ALL}")
            
    except Exception as e:
        print(f"{Fore.RED}Error processing {img_path} ({color_name}): {e}{Style.RESET_ALL}")

def process_all_images(limit=None):
    if not API_KEY:
        print(f"{Fore.RED}{Style.BRIGHT}GEMINI_API_KEY not found in environment.{Style.RESET_ALL}")
        return

    client = genai.Client(api_key=API_KEY)
    
    image_paths = []
    image_paths.extend(glob.glob("NM_stolar/*.png"))
    image_paths.extend(glob.glob("bilete/*.png"))
    image_paths = sorted(image_paths)
    
    if limit is not None:
        image_paths = image_paths[:limit]
    
    configs = [
        ("100% white", "#fff", "bg-uniform white", ""),
        ("SOLID STARK black", "#000", "bg-uniform black", "have the object front face camera straight on")
    ]
    
    total_tasks = len(image_paths) * len(configs)
    print(f"\n{Fore.CYAN}{Style.BRIGHT}==========================================")
    print(f" STARTING IMAGE PROCESSING")
    print(f" Source images: {len(image_paths)}")
    print(f" Configurations: {len(configs)}")
    print(f" Total tasks: {total_tasks}")
    print(f" Parallel workers: 10")
    print(f"=========================================={Style.RESET_ALL}\n")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for img_path in image_paths:
            for color_name, hex_code, out_dir, suffix in configs:
                futures.append(executor.submit(generate_image_task, client, img_path, color_name, hex_code, out_dir, suffix))
        
        concurrent.futures.wait(futures)
    
    print(f"\n{Fore.GREEN}{Style.BRIGHT}Done processing all tasks!{Style.RESET_ALL}")

if __name__ == "__main__":
    process_all_images(limit=None)
