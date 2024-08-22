import os
import hashlib
from PIL import Image

def resize_image(file_path, target_size=(256, 256)):
    """
    Resize an image to the target size.
    """
    with Image.open(file_path) as img:
        img = img.resize(target_size, Image.Resampling.LANCZOS)
        return img

def calculate_md5(image):
    """
    Calculate the MD5 hash of an image.
    """
    hash_md5 = hashlib.md5()
    img_bytes = image.tobytes()
    hash_md5.update(img_bytes)
    return hash_md5.hexdigest()

def find_duplicates(folder_path, target_size=(256, 256)):
    """
    Find duplicate images in a given folder, ignoring resolution differences.
    Returns a list of tuples, where each tuple contains the paths of duplicate images.
    """
    files_hash = {}
    duplicates = []

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            
            # Resize the image and calculate the MD5 hash
            try:
                resized_image = resize_image(file_path, target_size)
                file_hash = calculate_md5(resized_image)
            except Exception as e:
                print(f"Skipping {file_path}: {e}")
                continue

            if file_hash in files_hash:
                duplicates.append((files_hash[file_hash], file_path))
            else:
                files_hash[file_hash] = file_path

    return duplicates