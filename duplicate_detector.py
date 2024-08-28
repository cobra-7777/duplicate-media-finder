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
    processed_files = set()  # Track files that are already marked for deletion or processed

    # Collect all file paths
    all_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            all_files.append(file_path)

    # Use a ProcessPoolExecutor to process images in parallel
    with ProcessPoolExecutor() as executor:
        future_to_file = {executor.submit(process_image, file_path, target_size, min_size): file_path for file_path in all_files}

        results = []
        for future in as_completed(future_to_file):
            result = future.result()
            if result is None:
                continue
            results.append(result)

    # Sort results by resolution (highest to lowest)
    results.sort(key=lambda x: (-x[2], len(os.path.basename(x[0])), os.path.basename(x[0])))

    # Compare each image against the highest resolution image in its duplicate set
    for i in range(len(results)):
        file_path1, file_hash1, resolution1, original_dimensions1 = results[i]
        
        if file_path1 in processed_files:
            continue  # Skip already processed or deleted files

        # Use this file as the base for comparison in the current set
        best_image = (file_path1, file_hash1, resolution1, original_dimensions1)
        best_path, best_hash, best_resolution, best_dimensions = best_image

        for j in range(i + 1, len(results)):
            file_path2, file_hash2, resolution2, original_dimensions2 = results[j]

            if file_path2 in processed_files:
                continue  # Skip already processed or deleted files

            # Calculate the Hamming distance between the hashes
            distance = hamming_distance(best_hash, file_hash2)

            if distance <= hash_threshold:  # Check if the hashes are within the threshold
                if resolution2 < best_resolution:
                    # The second image is a duplicate and of lower resolution
                    duplicates.append((file_path2, best_path, file_hash2, best_hash))
                    processed_files.add(file_path2)  # Mark this image as processed
                else:
                    # If the new image is of higher resolution or equal but different, update best_image
                    if resolution2 > best_resolution:
                        # If resolution2 is better, update the best image
                        processed_files.add(best_path)  # The old best is now considered processed
                        best_image = (file_path2, file_hash2, resolution2, original_dimensions2)
                        best_path, best_hash, best_resolution, best_dimensions = best_image
                    # If they are equal in resolution and one should be kept over the other
                    duplicates.append((best_path, file_path2, best_hash, file_hash2))
                    processed_files.add(file_path2)

        # Mark the current best image as processed after comparing with all others
        processed_files.add(best_path)

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
    Returns a list of tuples, where each tuple contains the paths of duplicate videos and their frame hashes.
    """
    video_files_hash = {}
    video_duplicates = []
    processed_videos = set()  # Track videos that are already marked for deletion or processed

    # Collect all video file paths
    all_videos = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.mpeg', '.av1', '.m4s', '.mp4v', '.mpv')):  # Check for video file extensions
                file_path = os.path.join(root, file)
                all_videos.append(file_path)

    # Process each video to get its representative frame hashes
    with ProcessPoolExecutor() as executor:
        future_to_video = {executor.submit(calculate_dynamic_phash_for_frames, file_path): file_path for file_path in all_videos}

        results = []
        for future in as_completed(future_to_video):
            result = future.result()
            file_path = future_to_video[future]
            if result is None or any(h is None for h in result):
                print(f"Skipping video due to frame extraction error: {file_path}")
                continue
            # Calculate video resolution or other relevant metrics if needed
            video_resolution = get_video_resolution(file_path)
            results.append((file_path, result, video_resolution))

    # Sort results by resolution (highest to lowest), then by filename length, then alphabetically
    results.sort(key=lambda x: (-x[2][0] * x[2][1], len(os.path.basename(x[0])), os.path.basename(x[0])))

    # Compare each video against the highest resolution video in its duplicate set
    for i in range(len(results)):
        video_path1, video_hashes1, resolution1 = results[i]
        
        if video_path1 in processed_videos:
            continue  # Skip already processed or deleted videos

        # Use this video as the base for comparison in the current set
        best_video = (video_path1, video_hashes1, resolution1)
        best_path, best_hashes, best_resolution = best_video

        for j in range(i + 1, len(results)):
            video_path2, video_hashes2, resolution2 = results[j]

            if video_path2 in processed_videos:
                continue  # Skip already processed or deleted videos

            # Ensure same number of frames checked
            if len(best_hashes) != len(video_hashes2):
                continue

            # Calculate the Hamming distance between the frame hashes
            is_duplicate = all(
                abs(imagehash.hex_to_hash(h1) - imagehash.hex_to_hash(h2)) <= hash_threshold
                for h1, h2 in zip(best_hashes, video_hashes2)
            )

            if is_duplicate:  # Check if all frame hashes are within the threshold
                if resolution2[0] * resolution2[1] < best_resolution[0] * best_resolution[1]:
                    # The second video is a duplicate and of lower resolution
                    video_duplicates.append((video_path2, best_path))
                    processed_videos.add(video_path2)  # Mark this video as processed
                else:
                    # If the new video is of higher resolution or equal but different, update best_video
                    if resolution2[0] * resolution2[1] > best_resolution[0] * best_resolution[1] or \
                       (resolution2 == best_resolution and len(os.path.basename(video_path2)) < len(os.path.basename(best_path))):
                        # If resolution2 is better or same resolution but shorter name, update the best video
                        processed_videos.add(best_path)  # The old best is now considered processed
                        best_video = (video_path2, video_hashes2, resolution2)
                        best_path, best_hashes, best_resolution = best_video
                    # If they are equal in resolution and one should be kept over the other
                    video_duplicates.append((best_path, video_path2))
                    processed_videos.add(video_path2)

        # Mark the current best video as processed after comparing with all others
        processed_videos.add(best_path)

    return video_duplicates

def get_video_resolution(video_path):
    """
    Get the resolution of a video as (width, height).
    """
    cap = cv2.VideoCapture(video_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    return width, height  # Return width and height as a tuple