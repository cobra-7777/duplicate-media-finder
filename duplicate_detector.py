import os
import hashlib
from PIL import Image
import imagehash
from concurrent.futures import ProcessPoolExecutor, as_completed
import cv2

def resize_image(file_path, target_size=(500, 500), min_size=(256, 256)):
    """
    Resize an image to the target size if it's larger than min_size, otherwise keep original size.
    """
    try:
        with Image.open(file_path) as img:
            original_width, original_height = img.size
            
            # Determine if resizing is necessary
            if original_width > min_size[0] and original_height > min_size[1]:
                # Calculate the new size, maintaining aspect ratio
                img.thumbnail(target_size, Image.Resampling.LANCZOS)
            else:
                print(f"Image {file_path} is smaller than minimum size, skipping resizing.")

            # Ensure the image is still valid after resizing
            if img is None:
                raise ValueError("Image became None after resizing.")

            return img.copy()  # Return a copy of the image to avoid 'NoneType' issues
    except Exception as e:
        print(f"Error resizing image {file_path}: {e}")
        return None

def calculate_phash(image):
    """
    Calculate the perceptual hash (pHash) of an image.
    """
    return str(imagehash.phash(image))

def hamming_distance(hash1, hash2):
    """
    Calculate the Hamming distance between two hexadecimal strings.
    """
    # Convert hex strings to binary representations
    bin1 = bin(int(hash1, 16))[2:].zfill(64)
    bin2 = bin(int(hash2, 16))[2:].zfill(64)

    # Compute Hamming distance
    return sum(c1 != c2 for c1, c2 in zip(bin1, bin2))

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

def find_duplicates(folder_path, target_size=(500, 500), min_size=(256, 256), hash_threshold=2):
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

            # Compare with existing hashes using perceptual hashing
            duplicate_found = False
            for existing_hash, (existing_file_path, existing_resolution, existing_dimensions, existing_phash) in files_hash.items():
                # Calculate the Hamming distance between the hashes
                distance = hamming_distance(file_hash, existing_phash)

                if distance <= hash_threshold:  # Check if the hashes are within the threshold
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


## VIDEO

def get_frame_count(video_path):
    """
    Get the total number of frames in a video.
    """
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    return total_frames

def extract_frame(video_path, frame_number):
    """
    Extract a specific frame from a video file.
    """
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)  # Set to the specific frame
    ret, frame = cap.read()
    cap.release()

    if ret:
        return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    else:
        return None

def calculate_dynamic_phash_for_frames(video_path, percentages=[0.05, 0.5, 0.8]):
    """
    Calculate perceptual hashes for frames at specific percentages of the video.
    """
    frame_count = get_frame_count(video_path)
    if frame_count == 0:
        print(f"Video has no frames or could not be read: {video_path}")
        return None

    hashes = []
    for percentage in percentages:
        frame_number = int(frame_count * percentage)
        frame = extract_frame(video_path, frame_number)
        if frame:
            frame_hash = imagehash.phash(frame)
            hashes.append(str(frame_hash))
        else:
            hashes.append(None)
    return hashes

def find_video_duplicates(folder_path, hash_threshold=2):
    """
    Find duplicate videos in a given folder by hashing multiple representative frames.
    """
    video_files_hash = {}
    video_duplicates = []

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.mpeg', '.av1', '.m4s', '.mp4v', '.mpv', '')):  # Check for video file extensions
                file_path = os.path.join(root, file)
                video_hashes = calculate_dynamic_phash_for_frames(file_path)

                if video_hashes is None or any(h is None for h in video_hashes):
                    print(f"Skipping video due to frame extraction error: {file_path}")
                    continue

                # Check if video is a potential duplicate
                for existing_hash_key, existing_hashes in video_files_hash.items():
                    if len(existing_hashes) == len(video_hashes):  # Ensure same number of frames checked
                        is_duplicate = all(
                            abs(imagehash.hex_to_hash(h1) - imagehash.hex_to_hash(h2)) <= hash_threshold
                            for h1, h2 in zip(video_hashes, existing_hashes)
                        )
                        if is_duplicate:
                            video_duplicates.append((existing_hash_key, file_path))
                            break
                else:
                    # Only add to hash list if not found to be a duplicate
                    video_files_hash[file_path] = video_hashes

    return video_duplicates