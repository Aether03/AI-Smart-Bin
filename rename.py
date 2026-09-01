import os
import shutil

# Folder containing your files
folder = r"C:\Users\user\Desktop\AI-Smart-Bin\Dataset\raw_images\Plastic"

# Change directory to the folder
os.chdir(folder)

# Get all files in the directory
files = os.listdir(folder)

# Separate images and JSON files
image_files = sorted([f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
json_files = sorted([f for f in files if f.lower().endswith('.json')])

# Sanity check: make sure both lists are the same length
if len(image_files) != len(json_files):
    print("⚠️ Warning: The number of images and JSON files do not match!")
else:
    # Starting index for new names
    start_index = 501

    for i, (img, jsn) in enumerate(zip(image_files, json_files), start=start_index):
        # Get file extensions
        img_ext = os.path.splitext(img)[1]

        # Create new names
        new_img_name = f"image_{i}{img_ext}"
        new_json_name = f"image_{i}.json"

        # Rename files safely
        shutil.move(os.path.join(folder, img), os.path.join(folder, new_img_name))
        shutil.move(os.path.join(folder, jsn), os.path.join(folder, new_json_name))

    print(f"✅ Successfully renamed {len(image_files)} image and JSON pairs.")