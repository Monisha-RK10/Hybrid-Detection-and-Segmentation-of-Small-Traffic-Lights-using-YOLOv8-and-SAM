import os
import glob
import torch
import cv2
import numpy as np
from tqdm import tqdm
from ultralytics import YOLO
from segment_anything import sam_model_registry, SamPredictor

# Step 9: Load trained YOLOv8 model and segment the images by sending image & boxes (labels) to SAM model.

# ==========================
# 1. Setup & Model Loading
# ==========================
device = "cuda" if torch.cuda.is_available() else "cpu"
print("Using device:", device)

# Load YOLOv8
yolo_model = YOLO("/content/drive/MyDrive/TrafficSignal/best.pt")

# Load SAM (Segment Anything (ViT-B variant) and initializes its SamPredictor)
sam_checkpoint = "/content/sam_vit_b_01ec64.pth"
sam = sam_model_registry["vit_b"](checkpoint=sam_checkpoint).to(device)
predictor = SamPredictor(sam)

# ==========================
# 2. Paths
# ==========================
input_dir = "/content/drive/MyDrive/TrafficSignal/test/images"
output_dir = "/content/drive/MyDrive/TrafficSignal/result_SAM"
os.makedirs(output_dir, exist_ok=True)

# ==========================
# 3. Helper: Save Overlay
# ==========================
def save_image_with_masks(image_bgr, boxes, masks, save_path):
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB).copy()
    overlay = image_rgb.copy()

    for mask in masks:
        color = np.array([255, 0, 255], dtype=np.uint8)
        overlay[mask] = overlay[mask] * 0.2 + color * 0.8

    blended = cv2.addWeighted(image_rgb, 0.7, overlay, 0.3, 0)

    # Draw boxes
    for box in boxes:
        x1, y1, x2, y2 = map(int, box)
        cv2.rectangle(blended, (x1, y1), (x2, y2), (0, 0, 255), 2)

    # Save as BGR image for OpenCV
    blended_bgr = cv2.cvtColor(blended, cv2.COLOR_RGB2BGR)
    cv2.imwrite(save_path, blended_bgr)

# ==========================
# 4. Run for all images
# ==========================
image_paths = glob.glob(os.path.join(input_dir, "*.png")) + glob.glob(os.path.join(input_dir, "*.jpg"))

for image_path in tqdm(image_paths, desc="Processing images"):
    image = cv2.imread(image_path)
    if image is None:
        print(f"Failed to load {image_path}")
        continue

    # YOLOv8 detection
    results = yolo_model.predict(image, conf=0.25)[0]
    boxes = results.boxes.xyxy.cpu().numpy().astype(int)

    # SAM mask prediction
    predictor.set_image(image)
    masks = []
    for box in boxes:
        input_box = np.array(box)
        mask, _, _ = predictor.predict(
            point_coords=None,
            point_labels=None,
            box=input_box[None, :],
            multimask_output=False
        )
        if mask is not None and mask[0].any():
            masks.append(mask[0])

    # Save image with overlays
    file_name = os.path.basename(image_path)
    save_path = os.path.join(output_dir, file_name)
    save_image_with_masks(image, boxes, masks, save_path)

print(f"\n Done! All results saved in: {output_dir}")
