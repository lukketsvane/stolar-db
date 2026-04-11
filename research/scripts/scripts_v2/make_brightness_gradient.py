import pandas as pd
import numpy as np
from PIL import Image
from pathlib import Path
import os

# Oppsett
ROOT = Path("C:/Users/Shadow/Documents/GitHub/stolar-db")
IMG_DIR = ROOT / "STOLAR" / "images"
CSV_PATH = ROOT / "STOLAR" / "STOLAR.csv"
OUT_PATH = ROOT / "analysis" / "figures" / "fig-A.6.21-gradient.png"

# 16:9 Grid dimensjonar (ca. 2300 stolar)
# 64 * 36 = 2304
COLS = 64
ROWS = 36
TILE_SIZE = 128 # Storleik på kvar flis i collagen (pixlar)

def get_brightness(img_path):
    try:
        with Image.open(img_path) as img:
            img = img.convert('L') # Gråtone
            stat = np.array(img).mean()
            return stat
    except Exception as e:
        return None

def main():
    print("Lastar data...")
    df = pd.read_csv(CSV_PATH)
    objekt_ids = df['Objekt-ID'].dropna().unique()
    
    chair_data = []
    
    print("Analyserer bilete...")
    for oid in objekt_ids:
        # Finn første bilete for denne stolen
        potential_files = list(IMG_DIR.glob(f"{oid}*.jpg"))
        if not potential_files:
            continue
        
        img_path = potential_files[0]
        brightness = get_brightness(img_path)
        
        if brightness is not None:
            chair_data.append({
                'id': oid,
                'path': img_path,
                'brightness': brightness
            })
    
    # Sorter etter lysstyrke
    chair_data.sort(key=lambda x: x['brightness'])
    
    print(f"Fann {len(chair_data)} bilete. Lagar collagen...")
    
    # Lag eit tomt lerret (RG-B)
    canvas_w = COLS * TILE_SIZE
    canvas_h = ROWS * TILE_SIZE
    canvas = Image.new('RGB', (canvas_w, canvas_h), (255, 255, 255))
    
    for i, data in enumerate(chair_data):
        if i >= COLS * ROWS:
            break
            
        row = i // COLS
        col = i % COLS
        
        try:
            with Image.open(data['path']) as img:
                # Crop til kvadrat før resize
                w, h = img.size
                min_dim = min(w, h)
                left = (w - min_dim) / 2
                top = (h - min_dim) / 2
                right = (w + min_dim) / 2
                bottom = (h + min_dim) / 2
                img = img.crop((left, top, right, bottom))
                
                img = img.resize((TILE_SIZE, TILE_SIZE), Image.Resampling.LANCZOS)
                canvas.paste(img, (col * TILE_SIZE, row * TILE_SIZE))
        except:
            continue
            
    print(f"Lagrar til {OUT_PATH}...")
    canvas.save(OUT_PATH, quality=90)
    print("Ferdig!")

if __name__ == "__main__":
    main()
