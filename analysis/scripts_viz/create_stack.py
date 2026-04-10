import os
import sys
from PIL import Image
from pathlib import Path

def create_stack(obj_id, chair_dir, output_dir):
    chair_img_path = os.path.join(chair_dir, f"{obj_id}_bguw.png")
    table_img_path = os.path.join(chair_dir, f"table_{obj_id}.png")
    
    if not os.path.exists(chair_img_path) or not os.path.exists(table_img_path):
        return
    
    img_chair = Image.open(chair_img_path).convert('RGB')
    img_table = Image.open(table_img_path).convert('RGB')
    
    # Target height for the stack (e.g. 1080px for standard FHD slide height)
    target_h = 1080
    
    # Resize chair image
    chair_w = int(img_chair.width * (target_h / img_chair.height))
    img_chair = img_chair.resize((chair_w, target_h), Image.Resampling.LANCZOS)
    
    # Resize table image
    table_w = int(img_table.width * (target_h / img_table.height))
    img_table = img_table.resize((table_w, target_h), Image.Resampling.LANCZOS)
    
    # Combine horizontally
    combined = Image.new('RGB', (chair_w + table_w, target_h), (250, 250, 247)) # Match PAPER color
    combined.paste(img_chair, (0, 0))
    combined.paste(img_table, (chair_w, 0))
    
    output_path = os.path.join(output_dir, f"stack_{obj_id}.jpg")
    combined.save(output_path, quality=90)

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python create_stack.py <obj_id> <chair_dir> <output_dir>")
        sys.exit(1)
    create_stack(sys.argv[1], sys.argv[2], sys.argv[3])
