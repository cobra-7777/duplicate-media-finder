import os
import hashlib
from PIL import Image
import imagehash
from concurrent.futures import ProcessPoolExecutor, as_completed

def resize_image(file_path, target_size=(500, 500), min_size=(256, 256)):
    """
    Resize an image to the target size if it's larger than min_size, otherwise keep original size.
    """
    with Image.open(file_path) as img:
        original_width, original_height = img.size
        
        # Determine if resizing is necessary
        if original_width > min_size[0] and original_height > min_size[1]:
            # Calculate the new size, maintaining aspect ratio
            img.thumbnail(target_size, Image.Resampling.LANCZOS)
        
        # No resizing if the image is already smaller than the min size
        return img

def calculate_phash(image):
    """
    Calculate the perceptual hash (pHash) of an image.
    """
    return str(imagehash.phash(image))

def get_image_resolution(file_path):
    """
    Get the resolution (width x height) of an image.
    """
    with Image.open(file_path) as img:
        width, height = img.size
        return width * height, (width, height)

def process_image(file_path, target_size=(500, 500), min_size=(256, 256)):
    """
    Resize the image, calculate its pHash, and return the hash and resolution.
    """
    try:
        resized_image = resize_image(file_path, target_size, min_size)
        file_hash = calculate_phash(resized_image)
        resolution, original_dimensions = get_image_resolution(file_path)
        return file_path, file_hash, resolution, original_dimensions
    except Exception as e:
        print(f"Skipping {file_path}: {e}")
        return None

def find_duplicates(folder_path, target_size=(500, 500), min_size=(256, 256), hash_threshold=0):
    """
    Find duplicate images in a given folder, ignoring resolution differences.
    Returns a list of tuples, where each tuple contains the paths of duplicate images and their pHashes.
    """
    files_hash = {}
    duplicates = []

    # Collect all file paths
    all_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            all_files.append(file_path)

    # Use a ProcessPoolExecutor to process images in parallel
    with ProcessPoolExecutor() as executor:
        future_to_file = {executor.submit(process_image, file_path, target_size, min_size): file_path for file_path in all_files}

        for future in as_completed(future_to_file):
            result = future.result()
            if result is None:
                continue

            file_path, file_hash, resolution, original_dimensions = result

            # Ensure file_hash is in a comparable format (hex string)
            file_hash = str(file_hash)

            # Compare with existing hashes using perceptual hashing
            duplicate_found = False
            for existing_hash, (existing_file_path, existing_resolution, existing_dimensions, existing_phash) in files_hash.items():
                # Ensure existing_phash is in a comparable format (hex string)
                existing_phash = str(existing_phash)

                if file_hash == existing_phash:  # Check if the hashes are identical
                    if resolution > existing_resolution:
                        # The current image has a higher resolution, so replace the existing one
                        duplicates.append((existing_file_path, file_path, existing_phash, file_hash))
                    else:
                        # The existing image has a higher resolution, so the current image is a duplicate
                        duplicates.append((file_path, existing_file_path, file_hash, existing_phash))
                    duplicate_found = True
                    break

            if not duplicate_found:
                files_hash[file_hash] = (file_path, resolution, original_dimensions, file_hash)

    # Debugging: Check the structure of the duplicates list
    for i, duplicate in enumerate(duplicates):
        if len(duplicate) != 4:
            print(f"Warning: Duplicate tuple at index {i} does not have 4 elements: {duplicate}")

    return duplicates