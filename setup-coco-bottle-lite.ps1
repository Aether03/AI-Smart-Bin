# ================================
# Lightweight COCO 2017 "Bottle" Dataset Setup
# ================================
$base = "C:\Users\user\Desktop\COCO2017_bottle_lite"
New-Item -ItemType Directory -Force -Path "$base"
New-Item -ItemType Directory -Force -Path "$base\images"
New-Item -ItemType Directory -Force -Path "$base\annotations"

Write-Host "⬇️ Downloading COCO 2017 annotation file only..."
Invoke-WebRequest -Uri "http://images.cocodataset.org/annotations/annotations_trainval2017.zip" -OutFile "$base\annotations_trainval2017.zip"

Write-Host "📦 Extracting annotations..."
Expand-Archive -Path "$base\annotations_trainval2017.zip" -DestinationPath "$base\annotations"

Write-Host "🐍 Setting up Python environment..."
pip install pycocotools tqdm coco2yolo

Write-Host "🧩 Creating Python script to download bottle images only..."
$pyScript = @"
import json, os, requests
from tqdm import tqdm

base = r'$base'
ann_path = os.path.join(base, 'annotations', 'instances_train2017.json')
img_dir = os.path.join(base, 'images')

print('🔍 Reading annotation file...')
with open(ann_path, 'r') as f:
    data = json.load(f)

bottle_id = 39
bottle_imgs = set([ann['image_id'] for ann in data['annotations'] if ann['category_id'] == bottle_id])
print(f'Found {len(bottle_imgs)} images containing bottles.')

id_to_filename = {img['id']: img['file_name'] for img in data['images'] if img['id'] in bottle_imgs}
subset = list(id_to_filename.items())[:2500]  # Limit to first 2500 for smaller dataset

url_base = 'http://images.cocodataset.org/train2017/'
for img_id, fname in tqdm(subset, desc='Downloading bottle images'):
    url = url_base + fname
    out_path = os.path.join(img_dir, fname)
    if not os.path.exists(out_path):
        r = requests.get(url)
        if r.status_code == 200:
            with open(out_path, 'wb') as f:
                f.write(r.content)

print('✅ Downloaded bottle-only subset images.')

# Save filtered annotations
filtered_anns = {
    'images': [img for img in data['images'] if img['id'] in bottle_imgs],
    'annotations': [ann for ann in data['annotations'] if ann['category_id'] == bottle_id],
    'categories': [cat for cat in data['categories'] if cat['id'] == bottle_id]
}

with open(os.path.join(base, 'annotations', 'instances_bottle_subset.json'), 'w') as f:
    json.dump(filtered_anns, f)

print('✅ Saved filtered annotation JSON.')
"@
$pyPath = "$base\filter_bottle_subset.py"
$pyScript | Out-File -FilePath $pyPath -Encoding UTF8

Write-Host "🚀 Running Python filter..."
python $pyPath

Write-Host "🔄 Converting to YOLO format..."
coco2yolo --json_dir "$base\annotations" --image_dir "$base\images"

Write-Host "✅ Creating bottle.yaml config..."
$yamlContent = @"
path: $base
train: images
val: images

names:
  0: bottle
"@
$yamlPath = "$base\bottle.yaml"
$yamlContent | Out-File -FilePath $yamlPath -Encoding UTF8

Write-Host "🎉 DONE! You can now train with:"
Write-Host "yolo detect train data='$yamlPath' model=yolov8n.pt epochs=30 imgsz=640"
