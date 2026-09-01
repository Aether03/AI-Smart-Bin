import os
import shutil

base_dir = r"C:\Users\user\Desktop\AI-Smart-Bin\Dataset"
aluminium_dir = os.path.join(base_dir, r"raw_images\Aluminium_Cans\YOLODataset")
paper_dir = os.path.join(base_dir, r"raw_images\Paper\YOLODataset")
bottle_dir = os.path.join(base_dir, r"raw_images\Plastic\YOLODataset")

merged_dir = os.path.join(base_dir, "Combined_YOLODataset")

# Create merged structure
for subfolder in ["images/train", "images/val", "labels/train", "labels/val"]:
    os.makedirs(os.path.join(merged_dir, subfolder), exist_ok=True)

def copy_data(src_dir, dst_dir, prefix, class_id_offset=0):
    copied_images = 0
    for split in ["train", "val"]:
        # Handle datasets with or without train/val
        possible_img_dirs = [
            os.path.join(src_dir, "images", split),
            os.path.join(src_dir, "images")
        ]
        possible_lbl_dirs = [
            os.path.join(src_dir, "labels", split),
            os.path.join(src_dir, "labels")
        ]

        img_src = next((p for p in possible_img_dirs if os.path.exists(p)), None)
        lbl_src = next((p for p in possible_lbl_dirs if os.path.exists(p)), None)
        if not img_src or not lbl_src:
            continue

        img_dst = os.path.join(dst_dir, "images", split)
        lbl_dst = os.path.join(dst_dir, "labels", split)

        # Copy images and rename
        for file in os.listdir(img_src):
            if file.lower().endswith((".jpg", ".png", ".jpeg")):
                new_name = f"{prefix}_{file}"
                shutil.copy(os.path.join(img_src, file), os.path.join(img_dst, new_name))
                copied_images += 1

        # Copy and fix label IDs
        for file in os.listdir(lbl_src):
            if file.endswith(".txt"):
                src_file = os.path.join(lbl_src, file)
                new_name = f"{prefix}_{file}"
                dst_file = os.path.join(lbl_dst, new_name)

                with open(src_file, "r") as f:
                    lines = f.readlines()

                fixed_lines = []
                for line in lines:
                    parts = line.strip().split()
                    if parts:
                        parts[0] = str(int(parts[0]) + class_id_offset)
                        fixed_lines.append(" ".join(parts) + "\n")

                with open(dst_file, "w") as f:
                    f.writelines(fixed_lines)

    print(f"✅ {copied_images} images copied from {prefix}")

# Merge all datasets
print("🔄 Merging Aluminium dataset...")
copy_data(aluminium_dir, merged_dir, prefix="alu", class_id_offset=0)

print("🔄 Merging Paper dataset...")
copy_data(paper_dir, merged_dir, prefix="pap", class_id_offset=1)

print("🔄 Merging Bottle dataset...")
copy_data(bottle_dir, merged_dir, prefix="bot", class_id_offset=2)

# Create YAML
yaml_path = os.path.join(merged_dir, "data.yaml")
yaml_content = f"""# Combined dataset for Aluminium, Paper, and Bottles
path: {merged_dir}
train: images/train
val: images/val
test:

names:
  0: Aluminium
  1: Paper
  2: Bottle
"""

with open(yaml_path, "w") as f:
    f.write(yaml_content)

print("\n✅ Merge complete!")
print(f"📁 Combined dataset saved in: {merged_dir}")
print(f"🧾 YAML file created at: {yaml_path}")
