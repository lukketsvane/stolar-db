import os
import glob
from pathlib import Path
from PIL import Image
from dotenv import load_dotenv
from google import genai
from google.genai import types

def save_binary_file(file_name, data):
    with open(file_name, "wb") as f:
        f.write(data)
    print(f"File saved to: {file_name}")

def process_images(limit=3):
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not found in environment.")
        return

    client = genai.Client(api_key=api_key)
    model = "gemini-3.1-flash-image-preview"
    
    image_paths = []
    image_paths.extend(glob.glob("NM_stolar/*.png"))
    image_paths.extend(glob.glob("bilete/*.png"))
    image_paths = sorted(image_paths)
    
    if limit is not None:
        image_paths = image_paths[:limit]
        
    out_dir = Path("bg-uniform white")
    out_dir.mkdir(exist_ok=True)
    
    print(f"Processing {len(image_paths)} images...")
    
    prompt = "place it sharp against solid white background, have the subject cut sharply, and bacground be #fff 100% white."
    
    generate_content_config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_level="MINIMAL"),
        image_config=types.ImageConfig(
            aspect_ratio="1:1",
            image_size="1K",
        ),
        response_modalities=["IMAGE", "TEXT"],
    )

    for i, img_path in enumerate(image_paths):
        print(f"[{i+1}/{len(image_paths)}] Processing {img_path}")
        
        try:
            img = Image.open(img_path)
            
            contents = [prompt, img]
            
            file_name = out_dir / Path(img_path).name
            
            saved = False
            for chunk in client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=generate_content_config,
            ):
                if chunk.parts is None:
                    continue
                for part in chunk.parts:
                    if part.inline_data and part.inline_data.data:
                        save_binary_file(str(file_name), part.inline_data.data)
                        saved = True
                    elif part.text:
                        print(f"Text: {part.text}")
            
            if not saved:
                print(f"No image generated for {img_path}")
                
        except Exception as e:
            print(f"Error processing {img_path}: {e}")

if __name__ == "__main__":
    process_images(limit=3)
