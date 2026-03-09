import cv2
import os
from pathlib import Path
from colorama import init, Fore, Style

init(autoreset=True)

def crop_video_to_square(input_path, output_path):
    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        return False
        
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    square_size = height
    start_x = (width - square_size) // 2
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (square_size, square_size))
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        cropped_frame = frame[0:square_size, start_x:start_x+square_size]
        out.write(cropped_frame)
        
    cap.release()
    out.release()
    return True

def main():
    noreg_dir = Path("noreg")
    videos = list(noreg_dir.rglob("*.mp4"))
    print(f"{Fore.CYAN}Found {len(videos)} videos to process.{Style.RESET_ALL}")
    
    for vid_path in videos:
        temp_out = vid_path.with_name(vid_path.stem + "_sq.mp4")
        if crop_video_to_square(vid_path, temp_out):
            vid_path.unlink()
            temp_out.rename(vid_path)
            print(f"{Fore.GREEN}Updated {vid_path.name} to square.{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
