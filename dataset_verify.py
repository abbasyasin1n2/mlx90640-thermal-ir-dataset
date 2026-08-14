import os
import glob
import json
import random
import joblib
import numpy as np
import cv2
import matplotlib.pyplot as plt
from PIL import Image

# Base dataset directory
DATASET_DIR = r"dataset-IR"
if not os.path.exists(DATASET_DIR):
    DATASET_DIR = r"e:\MLX90640\Abbas Dataset\dataset-IR"

print(f"Dataset Directory set to: {os.path.abspath(DATASET_DIR)}")


def audit_dataset_integrity(base_dir):
    """
    Audits all subfolders in dataset-IR to check frame count alignment
    between .joblib, .json, and _image directories.
    """
    subfolders = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    subfolders.sort()
    
    summary = []
    for folder in subfolders:
        fpath = os.path.join(base_dir, folder)
        joblib_path = os.path.join(fpath, f"{folder}.joblib")
        json_path = os.path.join(fpath, f"{folder}.json")
        img_dir = os.path.join(fpath, f"{folder}_image")
        
        joblib_count = len(joblib.load(joblib_path)) if os.path.exists(joblib_path) else 0
        img_count = len(glob.glob(os.path.join(img_dir, "*.*"))) if os.path.exists(img_dir) else 0
        
        json_count = 0
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                jdata = json.load(f)
                if folder in jdata:
                    json_count = len(jdata[folder])
                    
        summary.append({
            "folder": folder,
            "joblib_frames": joblib_count,
            "json_labels": json_count,
            "image_files": img_count,
            "aligned": (joblib_count == img_count == json_count)
        })
        
    print(f"\n{'Subfolder Name':<32} | {'Joblib':<8} | {'JSON':<8} | {'Images':<8} | {'Aligned?':<8}")
    print("-" * 75)
    for s in summary:
        print(f"{s['folder']:<32} | {s['joblib_frames']:<8} | {s['json_labels']:<8} | {s['image_files']:<8} | {str(s['aligned']):<8}")


def process_thermal_pixels(pixels, sensor_shape=(24, 32), target_shape=(320, 240)):
    """
    Processes raw MLX90640 thermal pixels:
      1. Converts to float numpy array.
      2. Imputes NaNs with local median.
      3. Reshapes to 24x32 grid.
      4. Upscales to 320x240 using cubic interpolation.
    """
    px = np.array(pixels, dtype=float)
    
    # Handle NaN values (defective pixels)
    if np.isnan(px).any():
        median_val = np.nanmedian(px)
        px[np.isnan(px)] = median_val if not np.isnan(median_val) else 0.0
        
    thermal_2d = px.reshape(sensor_shape)
    upscaled = cv2.resize(thermal_2d, target_shape, interpolation=cv2.INTER_CUBIC)
    return thermal_2d, upscaled


def plot_global_verification(base_dir=DATASET_DIR, num_samples=10, colormap='inferno', random_seed=42):
    """
    Plots a 2-row comparison for random sample frames across the entire dataset:
      Row 1: Joblib thermal pixel array upscaled to 320x240
      Row 2: Saved PNG image from the corresponding subfolder image directory
    """
    subfolders = sorted([d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))])
    
    all_frames = []
    
    for folder in subfolders:
        fpath = os.path.join(base_dir, folder)
        joblib_path = os.path.join(fpath, f"{folder}.joblib")
        img_dir = os.path.join(fpath, f"{folder}_image")
        
        if not os.path.exists(joblib_path):
            continue
            
        jdata = joblib.load(joblib_path)
        for idx, item in enumerate(jdata):
            all_frames.append({
                'folder_name': folder,
                'img_dir': img_dir,
                'item': item
            })
            
    total_frames = len(all_frames)
    if total_frames == 0:
        print("No frames found in dataset.")
        return
        
    random.seed(random_seed)
    num_samples = min(num_samples, total_frames)
    sampled_frames = random.sample(all_frames, num_samples)
    
    cols = 5
    rows = 4  # 2 rows for joblib, 2 for actual
    
    fig, axes = plt.subplots(rows, cols, figsize=(4 * cols, 14))
    
    fig.suptitle(f"Global Verification Plot ({num_samples} Random Frames)", fontsize=16, fontweight='bold', y=0.98)
    
    for i, frame_data in enumerate(sampled_frames):
        col_idx = i % cols
        row_offset = (i // cols) * 2  # 0 for first 5 items, 2 for next 5
        
        folder_name = frame_data['folder_name']
        img_dir = frame_data['img_dir']
        item = frame_data['item']
        
        frame_num = item.get('frame_number', 0)
        timestamp = item.get('timestamp', 0)
        pixels = item.get('pixels', [])
        
        # Process joblib thermal pixels
        _, upscaled = process_thermal_pixels(pixels, target_shape=(320, 240))
        
        valid_px = np.array(pixels, dtype=float)
        min_t, max_t = np.nanmin(valid_px), np.nanmax(valid_px)
        
        # Row 1/3: Joblib upscaled plot
        ax_joblib = axes[row_offset, col_idx]
        im0 = ax_joblib.imshow(upscaled, cmap=colormap)
        short_folder = folder_name.replace('Single_Person_', 'SP_').replace('Empty_Room_', 'ER_')
        ax_joblib.set_title(f"{short_folder}\nFrame: {frame_num}\nTemp: [{min_t:.1f}°C - {max_t:.1f}°C]", fontsize=9)
        ax_joblib.axis('off')
        plt.colorbar(im0, ax=ax_joblib, fraction=0.046, pad=0.04)
        
        # Row 2/4: Saved PNG image match
        ax_png = axes[row_offset + 1, col_idx]
        ts_ms = int(timestamp * 1000)
        img_name = f"{folder_name}_{frame_num}_{ts_ms}.png"
        img_path = os.path.join(img_dir, img_name)
        
        # Fallback matching by frame number
        if not os.path.exists(img_path) and os.path.exists(img_dir):
            matches = glob.glob(os.path.join(img_dir, f"*{frame_num}*.png"))
            if matches:
                img_path = matches[0]
                
        if os.path.exists(img_path):
            img = Image.open(img_path)
            ax_png.imshow(img)
            ax_png.set_title(f"Saved Image\n{os.path.basename(img_path)}", fontsize=8)
        else:
            ax_png.text(0.5, 0.5, "Image Not Found", ha='center', va='center', color='red', fontsize=12)
            ax_png.set_title(f"Missing Image", fontsize=9)
        ax_png.axis('off')
        
    plt.tight_layout()
    plt.savefig("test_plot.png")
    plt.close()


if __name__ == "__main__":
    print("=" * 80)
    print("RUNNING DATASET INTEGRITY AUDIT")
    print("=" * 80)
    audit_dataset_integrity(DATASET_DIR)
    
    print("\nGenerating global verification plot (10 random frames)...")
    plot_global_verification(base_dir=DATASET_DIR, num_samples=10, colormap='inferno')
    print("Saved to test_plot.png")
