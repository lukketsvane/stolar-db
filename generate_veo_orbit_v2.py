import time
import os
import glob
from pathlib import Path
from google import genai
from google.genai import types
from dotenv import load_dotenv
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Load environment and API key
load_dotenv()
API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL = "veo-3.1-generate-preview"

# Initialize client with v1beta version required for Veo
client = genai.Client(
    http_options={"api_version": "v1beta"},
    api_key=API_KEY,
)

def generate_video_for_image(img_path):
    out_dir = Path("orbit-videos")
    out_dir.mkdir(exist_ok=True)
    
    stem_name = Path(img_path).stem
    video_out = out_dir / f"{stem_name}_orbit.mp4"
    
    if video_out.exists():
        print(f"{Fore.CYAN}Skipping {stem_name}, video already exists.{Style.RESET_ALL}")
        return

    print(f"\n{Fore.YELLOW}Generating 360° Orbit Video for: {stem_name}{Style.RESET_ALL}")
    
    max_retries = 5
    base_delay = 60 # Start with 60 seconds delay for 429

    for attempt in range(max_retries):
        try:
            # 2. Configure video generation
            video_config = types.GenerateVideosConfig(
                aspect_ratio="16:9",
                number_of_videos=1,
                duration_seconds=4, # Minimal duration for Veo 3.1
                resolution="720p",
            )

            # Descriptive prompt for 360 orbit
            prompt = "A cinematic 360-degree orbit shot around the object in the image. The camera moves smoothly in a full circle at a constant speed, capturing every detail against the background."
            
            # Using GenerateVideosSource as suggested by the user's snippet structure
            # (but corrected class name)
            source = types.GenerateVideosSource(
                prompt=prompt,
                image=types.Image.from_file(location=img_path)
            )

            print(f"{Fore.BLUE}Sending request to Veo 3.1... (Attempt {attempt + 1}/{max_retries}){Style.RESET_ALL}")
            operation = client.models.generate_videos(
                model=MODEL,
                source=source,
                config=video_config,
            )

            # 4. Poll for completion
            while not operation.done:
                print(f"{Fore.BLUE}Waiting for video generation... (10s polling){Style.RESET_ALL}")
                time.sleep(10)
                operation = client.operations.get(operation)

            # 5. Handle result
            result = operation.result
            if not result or not result.generated_videos:
                print(f"{Fore.RED}Error: No video generated for {stem_name}{Style.RESET_ALL}")
                return

            # 6. Save the generated video
            generated_video = result.generated_videos[0]
            print(f"{Fore.GREEN}Downloading and saving video to {video_out}...{Style.RESET_ALL}")
            
            # Download the video bytes
            video_bytes = client.files.download(file=generated_video.video)
            with open(video_out, "wb") as f:
                f.write(video_bytes)
                
            print(f"{Fore.GREEN}Success! Video saved to {video_out}{Style.RESET_ALL}")
            
            # If we reached here, success!
            break

        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                delay = base_delay * (2 ** attempt)
                print(f"{Fore.YELLOW}Quota exceeded (429). Retrying in {delay} seconds...{Style.RESET_ALL}")
                time.sleep(delay)
            else:
                print(f"{Fore.RED}Failed to process {stem_name}: {e}{Style.RESET_ALL}")
                break

def main():
    if not API_KEY:
        print(f"{Fore.RED}GEMINI_API_KEY not found in .env{Style.RESET_ALL}")
        return

    # Use images from bg-uniform white as source
    image_paths = sorted(glob.glob("bg-uniform white/*.png"))
    
    if not image_paths:
        print(f"{Fore.YELLOW}No images found in 'bg-uniform white/'.{Style.RESET_ALL}")
        return

    print(f"{Fore.CYAN}{Style.BRIGHT}Starting Veo 3.1 Video Generation for {len(image_paths)} image(s)...{Style.RESET_ALL}")
    
    # Process all images
    for img_path in image_paths:
        generate_video_for_image(img_path)

if __name__ == "__main__":
    main()
