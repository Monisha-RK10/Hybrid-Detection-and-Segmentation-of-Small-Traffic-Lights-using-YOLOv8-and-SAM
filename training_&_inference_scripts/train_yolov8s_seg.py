from ultralytics import YOLO

# Step 8: Load model & yaml to train the model.
# Train YOLOv8n segmenter model

!yolo task=segment mode=train model=yolov8s-seg.pt \
    data=/content/drive/MyDrive/TrafficSignal/segmentation_updated/data.yaml \
    epochs=250 imgsz=640 save=True
