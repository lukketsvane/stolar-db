import time
import os
import glob
import shutil
import cv2
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

def crop_video_to_square(input_path, output_path):
    """
    Crops a 16:9 video to a 1:1 square aspect ratio by cutting off the sides.
    """
    print(f"{Fore.BLUE}Cropping video to 1:1 aspect ratio...{Style.RESET_ALL}")
    
    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        print(f"{Fore.RED}Error: Could not open video {input_path}{Style.RESET_ALL}")
        return False
        
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v') # Using mp4v for compatibility
    
    # Calculate crop coordinates (center crop)
    square_size = min(width, height)
    start_x = (width - square_size) // 2
    start_y = (height - square_size) // 2
    
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (square_size, square_size))
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Crop frame: [y:y+h, x:x+w]
        cropped_frame = frame[start_y:start_y+square_size, start_x:start_x+square_size]
        out.write(cropped_frame)
        
    cap.release()
    out.release()
    print(f"{Fore.GREEN}Cropped video saved to {output_path}{Style.RESET_ALL}")
    return True

def get_folder_name(filename):
    """
    Extracts folder name from filename.
    Example: NMK.2005.0638_09013.png -> NMK.2005.0638
    """
    if "_" in filename:
        return filename.split("_", 1)[0]
    return Path(filename).stem

def process_image(img_path):
    img_path = Path(img_path)
    filename = img_path.name
    stem = img_path.stem
    
    folder_name = get_folder_name(filename)
    target_dir = Path("noreg") / folder_name
    
    if not target_dir.exists():
        print(f"{Fore.RED}Target directory {target_dir} does not exist. Skipping.{Style.RESET_ALL}")
        return

    # New filename with _bguw suffix, if not already present
    if not stem.endswith("_bguw"):
        new_filename = f"{stem}_bguw.png"
        new_img_path = target_dir / new_filename
        
        # Move and rename if not already there
        if img_path.exists():
            print(f"{Fore.BLUE}Moving {img_path} to {new_img_path}{Style.RESET_ALL}")
            shutil.move(str(img_path), str(new_img_path))
        elif not new_img_path.exists():
            print(f"{Fore.RED}Error: Source {img_path} not found and {new_img_path} does not exist.{Style.RESET_ALL}")
            return
    else:
        new_img_path = img_path
        new_filename = filename
    
    # Generate video
    video_out = target_dir / f"{Path(new_filename).stem}_orbit.mp4"
    video_temp = target_dir / f"{Path(new_filename).stem}_orbit_temp.mp4"
    
    if video_out.exists():
        print(f"{Fore.CYAN}Skipping video generation for {new_filename}, video already exists.{Style.RESET_ALL}")
        return

    print(f"{Fore.YELLOW}Generating 360° Orbit Video for: {new_filename}{Style.RESET_ALL}")
    
    max_retries = 5
    base_delay = 60 # Start with 60 seconds delay for 429

    for attempt in range(max_retries):
        try:
            # Configure video generation
            video_config = types.GenerateVideosConfig(
                aspect_ratio="16:9",
                number_of_videos=1,
                duration_seconds=4,
                resolution="720p",
            )

            prompt = "A cinematic 360-degree orbit shot around the object in the image. The camera moves smoothly in a full circle at a constant speed, capturing every detail against the background."
            
            source = types.GenerateVideosSource(
                prompt=prompt,
                image=types.Image.from_file(location=str(new_img_path))
            )

            print(f"{Fore.BLUE}Sending request to Veo 3.1... (Attempt {attempt + 1}/{max_retries}){Style.RESET_ALL}")
            operation = client.models.generate_videos(
                model=MODEL,
                source=source,
                config=video_config,
            )

            while not operation.done:
                print(f"{Fore.BLUE}Waiting for video generation... (10s polling){Style.RESET_ALL}")
                time.sleep(10)
                operation = client.operations.get(operation)

            result = operation.result
            if not result or not result.generated_videos:
                print(f"{Fore.RED}Error: No video generated for {new_filename}{Style.RESET_ALL}")
                return

            generated_video = result.generated_videos[0]
            print(f"{Fore.GREEN}Downloading temporary video...{Style.RESET_ALL}")
            
            video_bytes = client.files.download(file=generated_video.video)
            with open(video_temp, "wb") as f:
                f.write(video_bytes)
                
            # Crop the temporary video to 1:1 square
            if crop_video_to_square(video_temp, video_out):
                # Remove temp video after successful crop
                if video_temp.exists():
                    os.remove(video_temp)
                print(f"{Fore.GREEN}Success! Square video saved to {video_out}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Error: Failed to crop video for {new_filename}{Style.RESET_ALL}")
            
            # If we reached here, success!
            break

        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                delay = base_delay * (2 ** attempt)
                print(f"{Fore.YELLOW}Quota exceeded (429). Retrying in {delay} seconds...{Style.RESET_ALL}")
                time.sleep(delay)
            else:
                print(f"{Fore.RED}Failed to process {new_filename}: {e}{Style.RESET_ALL}")
                break

def main():
    if not API_KEY:
        print(f"{Fore.RED}GEMINI_API_KEY not found in .env{Style.RESET_ALL}")
        return

    # Use images from bg-uniform white as source
    source_dir = Path("bg-uniform white")
    image_paths = sorted(list(source_dir.glob("*.png")))
    
    if not image_paths:
        # Check if they are already moved to noreg
        print(f"{Fore.YELLOW}No images found in '{source_dir}'. Checking noreg subfolders for _bguw.png...{Style.RESET_ALL}")
        image_paths = sorted(list(Path("noreg").rglob("*_bguw.png")))
    
    if not image_paths:
        print(f"{Fore.YELLOW}No images found to process.{Style.RESET_ALL}")
        return

    print(f"{Fore.CYAN}{Style.BRIGHT}Starting Organization and Veo Generation (1:1 crop) for {len(image_paths)} image(s)...{Style.RESET_ALL}")
    
    for img_path in image_paths:
        process_image(img_path)

if __name__ == "__main__":
    main()
