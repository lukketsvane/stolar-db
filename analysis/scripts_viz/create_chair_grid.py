import os
import cv2
import numpy as np
from PIL import Image
from tqdm import tqdm
import math
import colorsys
from multiprocessing import Pool

def get_image_info(img_path):
    try:
        # Load image
        img = cv2.imread(img_path)
        if img is None:
            return None
        
        # Resize for faster processing
        img_small = cv2.resize(img, (64, 64))
        
        # Calculate brightness (mean of grayscale)
        gray = cv2.cvtColor(img_small, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray)
        
        # Average color in HSV for Hue sorting
        hsv = cv2.cvtColor(img_small, cv2.COLOR_BGR2HSV)
        avg_hsv = np.mean(hsv, axis=(0, 1))
        
        # Complexity proxy (Edge density)
        edges = cv2.Canny(gray, 100, 200)
        complexity = np.sum(edges) / 255.0
        
        return {
            'path': img_path,
            'brightness': brightness,
            'hue': avg_hsv[0],      # Hue
            'saturation': avg_hsv[1],# Saturation
            'value': avg_hsv[2],     # Value (Brightness in HSV)
            'complexity': complexity
        }
    except Exception as e:
        # print(f"Error processing {img_path}: {e}")
        return None

def create_grid(image_infos, cols, rows, tile_size, output_path, sort_key='brightness', reverse=False):
    # Sort images
    sorted_infos = sorted(image_infos, key=lambda x: x[sort_key], reverse=reverse)
    
    # Create blank canvas
    canvas_w = cols * tile_size
    canvas_h = rows * tile_size
    canvas = Image.new('RGB', (canvas_w, canvas_h), (255, 255, 255))
    
    for i, info in enumerate(sorted_infos):
        if i >= cols * rows:
            break
            
        r = i // cols
        c = i % cols
        
        try:
            img = Image.open(info['path']).convert('RGB')
            # Resize to tile size
            # Use Resampling.NEAREST for speed or LANCZOS for quality
            # User wants "max gpu power", suggesting high quality.
            img.thumbnail((tile_size, tile_size), Image.Resampling.LANCZOS)
            
            # Center in the tile
            x = c * tile_size + (tile_size - img.width) // 2
            y = r * tile_size + (tile_size - img.height) // 2
            
            canvas.paste(img, (x, y))
        except Exception as e:
            pass
            
    canvas.save(output_path, quality=90)
    print(f"Saved grid to {output_path}")

def main():
    img_dir = 'STOLAR/bguw'
    files = [os.path.join(img_dir, f) for f in os.listdir(img_dir) if f.lower().endswith('.png')]
    print(f"Found {len(files)} images.")
    
    # Use Pool for parallel processing
    print("Analyzing images in parallel...")
    with Pool() as pool:
        image_infos = list(tqdm(pool.imap(get_image_info, files), total=len(files), desc="Analyzing"))
            
    image_infos = [info for info in image_infos if info is not None]
    print(f"Successfully analyzed {len(image_infos)} images.")
    
    # 16:9 Grid
    # n=4 => 64x36 = 2304 slots
    cols, rows = 64, 36
    tile_size = 128
    
    # Attempt 1: Dark to Light (Brightness Gradient)
    create_grid(image_infos, cols, rows, tile_size, 'analysis/figures/chairs_brightness_gradient.jpg', sort_key='brightness', reverse=False)
    
    # Attempt 2: By Hue (Color Gradient)
    create_grid(image_infos, cols, rows, tile_size, 'analysis/figures/chairs_hue_gradient.jpg', sort_key='hue', reverse=False)
    
    # Attempt 3: By Complexity (Simple to Complex)
    create_grid(image_infos, cols, rows, tile_size, 'analysis/figures/chairs_complexity_gradient.jpg', sort_key='complexity', reverse=False)

    # Attempt 4: 16x9 Exactly (Top 144 by complexity)
    create_grid(image_infos[:144], 16, 9, 256, 'analysis/figures/chairs_top144_16x9.jpg', sort_key='complexity', reverse=True)

if __name__ == '__main__':
    os.makedirs('analysis/figures', exist_ok=True)
    main()
