import os
import cv2
import numpy as np
from PIL import Image
from tqdm import tqdm
import math
from multiprocessing import Pool

def get_image_info(img_path):
    try:
        img = cv2.imread(img_path)
        if img is None: return None
        img_small = cv2.resize(img, (64, 64))
        gray = cv2.cvtColor(img_small, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray)
        hsv = cv2.cvtColor(img_small, cv2.COLOR_BGR2HSV)
        avg_hsv = np.mean(hsv, axis=(0, 1))
        return {'path': img_path, 'brightness': brightness, 'hue': avg_hsv[0], 'val': avg_hsv[2]}
    except: return None

def create_2d_grid(image_infos, cols, rows, tile_size, output_path):
    # 1. Sort by Hue initially
    image_infos.sort(key=lambda x: x['hue'])
    
    # 2. Distribute into 'cols' groups
    num_per_col = len(image_infos) // cols
    grid = [[None for _ in range(rows)] for _ in range(cols)]
    
    for c in range(cols):
        col_group = image_infos[c*num_per_col : (c+1)*num_per_col]
        # 3. Sort each column group by Brightness
        col_group.sort(key=lambda x: x['brightness'])
        for r in range(min(rows, len(col_group))):
            grid[c][r] = col_group[r]
            
    # Create canvas
    canvas = Image.new('RGB', (cols * tile_size, rows * tile_size), (255, 255, 255))
    
    for c in tqdm(range(cols), desc="Pasting 2D Grid"):
        for r in range(rows):
            info = grid[c][r]
            if info is None: continue
            try:
                img = Image.open(info['path']).convert('RGB')
                img.thumbnail((tile_size, tile_size), Image.Resampling.LANCZOS)
                x = c * tile_size + (tile_size - img.width) // 2
                y = r * tile_size + (tile_size - img.height) // 2
                canvas.paste(img, (x, y))
            except: pass
            
    canvas.save(output_path, quality=95)
    print(f"Saved 2D grid to {output_path}")

def main():
    img_dir = 'STOLAR/bguw'
    files = [os.path.join(img_dir, f) for f in os.listdir(img_dir) if f.lower().endswith('.png')]
    with Pool() as pool:
        image_infos = [info for info in pool.map(get_image_info, files) if info is not None]
    
    # 64 x 36 is 2304. We have 2092 images.
    create_2d_grid(image_infos, 64, 36, 128, 'analysis/figures/chairs_2d_hue_brightness.jpg')

if __name__ == '__main__':
    main()
