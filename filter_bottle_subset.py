import json, os, requests
from tqdm import tqdm

base = r"C:\Users\user\Desktop\AI-Smart-Bin\COCO2017_bottle_lite"
ann_path = os.path.join(base, "annotations", "instances_train2017.json")
img_dir = os.path.join(base, "images")

os.makedirs(img_dir, exist_ok=True)

print("🔍 Reading annotation file...")
with open(ann_path, "r") as f:
    data = json.load(f)

bottle_id = 39  # COCO class for "bottle"
bottle_imgs = set(
    [ann["image_id"] for ann in data["annotations"] if ann["category_id"] == bottle_id]
)
print(f"Found {len(bottle_imgs)} images containing bottles.")

id_to_filename = {
    img["id"]: img["file_name"] for img in data["images"] if img["id"] in bottle_imgs
}
subset = list(id_to_filename.items())[:250]  # limit to 250 images only

url_base = "http://images.cocodataset.org/train2017/"
for img_id, fname in tqdm(subset, desc="Downloading bottle images"):
    url = url_base + fname
    out_path = os.path.join(img_dir, fname)
    if not os.path.exists(out_path):
        r = requests.get(url)
        if r.status_code == 200:
            with open(out_path, "wb") as f:
                f.write(r.content)

print("✅ Downloaded bottle-only subset images.")

# Save filtered annotations
filtered_anns = {
    "images": [img for img in data["images"] if img["id"] in bottle_imgs][:250],
    "annotations": [
        ann for ann in data["annotations"] if ann["category_id"] == bottle_id
    ],
    "categories": [cat for cat in data["categories"] if cat["id"] == bottle_id],
}

with open(os.path.join(base, "annotations", "instances_bottle_subset.json"), "w") as f:
    json.dump(filtered_anns, f)

print("✅ Saved filtered annotation JSON.")
