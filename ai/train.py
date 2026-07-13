from ultralytics import YOLO

model = YOLO("yolo11n-seg.pt")

model.train(
    data="ai/dataset/data.yaml",
    epochs=5,
    imgsz=640,
    batch=4,
    workers=2,
    device="cpu",
    project="ai/runs",
    name="pressonai"
)

print("Training Finished")