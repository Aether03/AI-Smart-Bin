import json, os, random, shutil
from PIL import Image
from pathlib import Path

# === CONFIGURATION ===
json_path = r"C:\Users\user\Desktop\AI-Smart-Bin\COCO2017_bottle_lite\annotations\instances_bottle_subset.json"
img_dir = r"C:\Users\user\Desktop\AI-Smart-Bin\COCO2017_bottle_lite\images"
output_dir = r"C:\Users\user\Desktop\AI-Smart-Bin\COCO2017_bottle_yolo"

split_ratio = 0.8  # 80% train, 20% val
random.seed(42)    # For reproducibility

# === PREPARE OUTPUT FOLDERS ===
for sub in ["train/images", "train/labels", "val/images", "val/labels"]:
    os.makedirs(os.path.join(output_dir, sub), exist_ok=True)

# === LOAD COCO ANNOTATIONS ===
with open(json_path, "r") as f:
    coco = json.load(f)

print(f"📄 Loaded {len(coco['images'])} images and {len(coco['annotations'])} annotations.")

# === GET CATEGORY INFO ===
categories = coco.get("categories", [])
cat_map = {cat["id"]: i for i, cat in enumerate(categories)}
cat_names = [cat["name"] for cat in categories]

# === MAP IMAGE IDs TO FILENAMES ===
img_map = {img["id"]: img["file_name"] for img in coco["images"]}
img_ids = list(img_map.keys())
random.shuffle(img_ids)

# === SPLIT INTO TRAIN/VAL ===
split_index = int(len(img_ids) * split_ratio)
train_ids = set(img_ids[:split_index])
val_ids = set(img_ids[split_index:])

# === TEMP: STORE ANNOTATIONS BY IMAGE ID ===
anns_by_image = {}
for ann in coco["annotations"]:
    anns_by_image.setdefault(ann["image_id"], []).append(ann)

# === CONVERT BBOX FUNCTION ===
def convert_bbox(bbox, img_w, img_h):
    x, y, w, h = bbox
    x_center = (x + w / 2) / img_w
    y_center = (y + h / 2) / img_h
    return x_center, y_center, w / img_w, h / img_h

count_train, count_val = 0, 0
for img_id, img_name in img_map.items():
    src_img = os.path.join(img_dir, img_name)
    if not os.path.exists(src_img):
        continue

    # Get image size
    with Image.open(src_img) as im:
        img_w, img_h = im.size

    anns = anns_by_image.get(img_id, [])
    lines = []
    for ann in anns:
        cls_id = cat_map[ann["category_id"]]
        x_c, y_c, w, h = convert_bbox(ann["bbox"], img_w, img_h)
        lines.append(f"{cls_id} {x_c:.6f} {y_c:.6f} {w:.6f} {h:.6f}")

    # Determine subset
    subset = "train" if img_id in train_ids else "val"
    img_dst = os.path.join(output_dir, f"{subset}/images/{img_name}")
    label_dst = os.path.join(output_dir, f"{subset}/labels/{Path(img_name).stem}.txt")

    shutil.copy(src_img, img_dst)
    with open(label_dst, "w") as f:
        f.write("\n".join(lines))

    if subset == "train":
        count_train += 1
    else:
        count_val += 1

print(f"✅ Conversion complete!")
print(f"   • {count_train} training images")
print(f"   • {count_val} validation images")

# === CREATE data.yaml ===
yaml_path = os.path.join(output_dir, "data.yaml")
train_path = os.path.join(output_dir, "train/images").replace("\\", "/")
val_path = os.path.join(output_dir, "val/images").replace("\\", "/")

with open(yaml_path, "w") as f:
    f.write(f"train: {train_path}\n")
    f.write(f"val: {val_path}\n")
    f.write(f"nc: {len(cat_names)}\n")
    f.write("names:\n")
    for i, name in enumerate(cat_names):
        f.write(f"  {i}: {name}\n")

print(f"🧾 data.yaml generated at: {yaml_path}")
print(f"✅ Ready for YOLO training!")
