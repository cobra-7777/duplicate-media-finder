import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QFileDialog, QMessageBox, QScrollArea, QVBoxLayout, QWidget, QHBoxLayout, QFrame, QSpacerItem, QSizePolicy, QCheckBox, QDialog, QComboBox, QRadioButton
)
from PyQt5.QtGui import QPixmap, QFont, QImage
from PyQt5.QtCore import Qt
from duplicate_detector import find_duplicates, get_image_resolution, get_frame_count, find_video_duplicates, get_video_resolution  # Import the duplicate detection module
import os
import random
import cv2
from PIL import Image
import numpy as np


## TODO: ICONS next to important stuff
## TODO: FONTS
## TODO: DISPLAY IMAGE SIZE

def convert_frame_to_pixmap(frame):
    """
    Convert an OpenCV frame to QPixmap for display.
    """
    height, width, channel = frame.shape
    bytes_per_line = 3 * width
    q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
    return QPixmap.fromImage(q_image)

class DuplicateImageFinder(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set the title and locked size of the window
        self.setWindowTitle('Duplicate Image Finder')
        self.width = 700
        self.height = 500
        self.setFixedSize(self.width, self.height)  # Increase the window size to accommodate larger scroll area

        # Logo
        self.logo_label = QLabel(self)
        self.logo_pixmap = QPixmap('path/to/your/logo.png')  # Replace with the path to your logo
        self.logo_label.setPixmap(self.logo_pixmap.scaled(150, 150, Qt.KeepAspectRatio))
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setFixedSize(150, 150)
        self.logo_label.move((self.width - 150) // 2, 50)  # Center the logo at the top

        # Button to choose folder
        self.folder_button = QPushButton('Choose Folder', self)
        self.folder_button.setFixedSize(150, 40)
        self.folder_button.move((self.width - 150) // 2, 250)  # Center the button below the logo
        self.folder_button.clicked.connect(self.choose_folder)

        # Label to show the chosen folder path
        self.folder_label = QLabel('No folder chosen', self)
        self.folder_label.setFixedSize(400, 40)
        self.folder_label.setAlignment(Qt.AlignCenter)
        self.folder_label.move((self.width - 400) // 2, 320)  # Center this label below the button

        #Radio buttons
        self.photo_radio = QRadioButton('Search for Photo Duplicates', self)
        self.video_radio = QRadioButton('Search for Video Duplicates', self)
        self.photo_radio.setFixedSize(155,30)
        self.video_radio.setFixedSize(155,30)
        self.photo_radio.setChecked(True)
        self.photo_radio.move((self.width - 155) // 2, 340)
        self.video_radio.move((self.width - 155) // 2, 360)

        # Start button
        self.start_button = QPushButton('Start', self)
        self.start_button.setFixedSize(150, 40)
        self.start_button.move((self.width - 150) // 2, 400)  # Center the button below the folder label
        self.start_button.clicked.connect(self.start_processing)

        # Store the selected folder path
        self.selected_folder = None

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select Folder')
        if folder:
            self.selected_folder = folder
            self.folder_label.setText(f'Selected Folder: {folder}')

    def start_processing(self):
        if hasattr(self, 'selected_folder'):
            if self.photo_radio.isChecked():
                duplicates = find_duplicates(self.selected_folder)  # Use your existing logic for photos
                self.comparison_window = ComparisonWindow(duplicates)
                self.comparison_window.show()
            elif self.video_radio.isChecked():
                video_duplicates = find_video_duplicates(self.selected_folder)  # Use your new logic for videos
                self.comparison_window_video = ComparisonWindowVideo(video_duplicates)
                self.comparison_window_video.show()
        else:
            QMessageBox.warning(self, "No Folder Selected", "Please choose a folder first.")


    def show_comparison_window(self, duplicates):
        self.comparison_window = ComparisonWindow(duplicates)
        self.comparison_window.show()


class ComparisonWindow(QMainWindow):
    def __init__(self, duplicates):
        super().__init__()

        self.setWindowTitle('Review Duplicates')
        self.setFixedSize(1000, 900)  # Increase window size

        # Main layout for the entire window
        main_layout = QVBoxLayout()

        # Titles layout
        titles_widget = QWidget()
        titles_layout = QHBoxLayout(titles_widget)

        to_keep_label = QLabel("To Keep")
        to_delete_label = QLabel("To Be Deleted")

        to_keep_label.setFont(QFont('Palatino Linotype', 20))
        to_delete_label.setFont(QFont('Palatino Linotype', 20))

        to_keep_label.setAlignment(Qt.AlignCenter)
        to_delete_label.setAlignment(Qt.AlignCenter)

        titles_layout.addWidget(to_keep_label)
        titles_layout.addStretch()
        titles_layout.addWidget(to_delete_label)

        main_layout.addWidget(titles_widget)

        # Scroll area for viewing duplicates
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 2px solid black;  /* Set border width, style, and color */
            }
        """)

        # Widget to hold all duplicate comparisons
        container_widget = QWidget()
        scroll_area.setWidget(container_widget)

        # Layout to arrange the duplicate comparisons vertically
        layout = QVBoxLayout(container_widget)

        # Define the maximum width for each image
        max_image_width = 370
        max_image_height = 500

        # Store and associate checkboxes
        self.checkboxes = {}

        # How many dupes
        total_duplicates = len(duplicates)

        for index, (img1_path, img2_path, img1_hash, img2_hash) in enumerate(duplicates):
            comparison_widget = QWidget()
            comparison_layout = QVBoxLayout(comparison_widget)
            comparison_layout.setSpacing(0)

            # Determine which image is to be kept (higher resolution)
            img1_name = os.path.basename(img1_path)
            img2_name = os.path.basename(img2_path)
            img1_resolution = get_image_resolution(img1_path)[1]
            img2_resolution = get_image_resolution(img2_path)[1]
            img1_folder = os.path.basename(os.path.dirname(img1_path))
            img2_folder = os.path.basename(os.path.dirname(img2_path))
            
            print(f"Comparing: {img1_name} (Resolution: {img1_resolution}) vs {img2_name} (Resolution: {img2_resolution})")

            if img1_resolution > img2_resolution:
                to_keep_path, to_delete_path = img1_path, img2_path
                to_keep_name, to_delete_name = img1_name, img2_name
                to_keep_res, to_delete_res = img1_resolution, img2_resolution
                to_keep_folder, to_delete_folder = img1_folder, img2_folder
                to_keep_phash, to_delete_phash = img1_hash, img2_hash
            elif img1_resolution < img2_resolution:
                to_keep_path, to_delete_path = img2_path, img1_path
                to_keep_name, to_delete_name = img2_name, img1_name
                to_keep_res, to_delete_res = img2_resolution, img1_resolution
                to_keep_folder, to_delete_folder = img2_folder, img1_folder
                to_keep_phash, to_delete_phash = img2_hash, img1_hash
            else:
                # Resolutions are equal, apply further checks
                if len(img1_name) < len(img2_name):
                    to_keep_path, to_delete_path = img1_path, img2_path
                    to_keep_name, to_delete_name = img1_name, img2_name
                    to_keep_res, to_delete_res = img1_resolution, img2_resolution
                    to_keep_folder, to_delete_folder = img1_folder, img2_folder
                    to_keep_phash, to_delete_phash = img1_hash, img2_hash
                elif len(img1_name) > len(img2_name):
                    to_keep_path, to_delete_path = img2_path, img1_path
                    to_keep_name, to_delete_name = img2_name, img1_name
                    to_keep_res, to_delete_res = img2_resolution, img1_resolution
                    to_keep_folder, to_delete_folder = img2_folder, img1_folder
                    to_keep_phash, to_delete_phash = img2_hash, img1_hash
                else:
                    # Name lengths are equal, prioritize alphabetically
                    if img1_name < img2_name:
                        to_keep_path, to_delete_path = img1_path, img2_path
                        to_keep_name, to_delete_name = img1_name, img2_name
                        to_keep_res, to_delete_res = img1_resolution, img2_resolution
                        to_keep_folder, to_delete_folder = img1_folder, img2_folder
                        to_keep_phash, to_delete_phash = img1_hash, img2_hash
                    else:
                        to_keep_path, to_delete_path = img2_path, img1_path
                        to_keep_name, to_delete_name = img2_name, img1_name
                        to_keep_res, to_delete_res = img2_resolution, img1_resolution
                        to_keep_folder, to_delete_folder = img2_folder, img1_folder
                        to_keep_phash, to_delete_phash = img2_hash, img1_hash

            # Horizontal layout for filenames and resolutions
            filenames_widget = QWidget()
            filenames_layout = QHBoxLayout(filenames_widget)
            filenames_layout.setSpacing(10)

            to_keep_name_label = QLabel(f"NAME: {to_keep_name}\nRESOLUTION: {to_keep_res[0]}x{to_keep_res[1]}\nP-HASH: {to_keep_phash}\nLOCATION: {to_keep_folder}")
            to_keep_name_label.setAlignment(Qt.AlignLeft)
            to_keep_name_label.setStyleSheet("color: green; font-weight: bold;")

            to_delete_name_label = QLabel(f"NAME: {to_delete_name}\nRESOLUTION: {to_delete_res[0]}x{to_delete_res[1]}\nP-HASH: {to_delete_phash}\nLOCATION: {to_delete_folder}")
            to_delete_name_label.setAlignment(Qt.AlignRight)
            to_delete_name_label.setStyleSheet("color: red; font-weight: bold;")

            filenames_layout.addWidget(to_keep_name_label)
            filenames_layout.addStretch()
            filenames_layout.addWidget(to_delete_name_label)

            comparison_layout.addWidget(filenames_widget)

            # Horizontal layout for images
            images_widget = QWidget()
            images_layout = QHBoxLayout(images_widget)
            images_layout.setSpacing(10)

            to_keep_label = QLabel()
            to_keep_pixmap = QPixmap(to_keep_path)
            to_keep_label.setPixmap(to_keep_pixmap.scaled(max_image_width, max_image_height, Qt.KeepAspectRatio))

            to_delete_label = QLabel()
            to_delete_pixmap = QPixmap(to_delete_path)
            to_delete_label.setPixmap(to_delete_pixmap.scaled(max_image_width, max_image_height, Qt.KeepAspectRatio))

            images_layout.addStretch()
            images_layout.addWidget(to_keep_label)
            images_layout.addStretch()
            images_layout.addWidget(to_delete_label)
            images_layout.addStretch()

            comparison_layout.addWidget(images_widget)

            # Add space above checkbox
            space_above_checkbox = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed)
            comparison_layout.addItem(space_above_checkbox)

            # Add a checkbox below the images to decide deletion
            checkbox_layout = QHBoxLayout()
            checkbox_layout.addStretch()

            delete_checkbox = QCheckBox("Mark for deletion")
            delete_checkbox.setChecked(True)  # Default to checked
            checkbox_layout.addWidget(delete_checkbox)

            checkbox_layout.addStretch()
            comparison_layout.addLayout(checkbox_layout)

            self.checkboxes[delete_checkbox] = (to_keep_path, to_delete_path)

            # Add space between the images and the separator
            space_above_separator = QSpacerItem(20, 30, QSizePolicy.Minimum, QSizePolicy.Fixed)
            comparison_layout.addItem(space_above_separator)

            # Separator
            if index < total_duplicates - 1:
                separator = QFrame()
                separator.setFrameShape(QFrame.HLine)
                separator.setFrameShadow(QFrame.Plain)
                separator.setStyleSheet("background-color: black;")
                separator.setMinimumHeight(4)
                comparison_layout.addWidget(separator)

            layout.addWidget(comparison_widget)

        # Instead of addStretch() here, use QSpacerItem to avoid excessive space
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        comparison_layout.addItem(spacer)

        main_layout.addWidget(scroll_area)

        # Delete button at the bottom
        delete_button = QPushButton('Delete Duplicates', self)
        delete_button.clicked.connect(self.delete_duplicates)
        main_layout.addWidget(delete_button)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def delete_duplicates(self):
        # Count files marked for deletion
        files_to_delete = [(to_delete_path, to_keep_path) for checkbox, (to_keep_path, to_delete_path) in self.checkboxes.items() if checkbox.isChecked()]

        if not files_to_delete:
            QMessageBox.information(self, "No Files Selected", "No files are marked for deletion.")
            return

        # Show deletion confirmation dialog
        dialog = DeletionConfirmationDialog(len(files_to_delete))
        if dialog.exec_() == QDialog.Accepted:
            deletion_type = dialog.get_deletion_type()

            for to_delete_path, to_keep_path in files_to_delete:
                # Log which files are being kept and deleted
                print(f"Keeping {to_keep_path}, Deleting {to_delete_path}")

                try:
                    if deletion_type == "Normal Deletion":
                        os.remove(to_delete_path)
                        print(f"File deleted: {to_delete_path}")
                    elif "Shred" in deletion_type:
                        if "1 Pass" in deletion_type:
                            shred_file(to_delete_path, passes=1)
                        elif "7 Passes" in deletion_type:
                            shred_file(to_delete_path, passes=7)
                        elif "15 Passes" in deletion_type:
                            shred_file(to_delete_path, passes=15)
                except Exception as e:
                    print(f"Error deleting file {to_delete_path}: {e}")

            QMessageBox.information(self, "Deletion Complete", f"{len(files_to_delete)} files have been deleted.")


class DeletionConfirmationDialog(QDialog):
    def __init__(self, num_files):
        super().__init__()
        self.setWindowTitle("Confirm Deletion")
        self.setFixedSize(300, 200)

        layout = QVBoxLayout()

        # Number of files to delete
        label = QLabel(f"Number of images marked for deletion: {num_files}")
        layout.addWidget(label)

        # Dropdown for deletion type
        self.deletion_type_combo = QComboBox()
        self.deletion_type_combo.addItems(["Normal Deletion", "Shred (1 Pass)", "Shred (7 Passes)", "Shred (15 Passes)"])
        layout.addWidget(self.deletion_type_combo)

        # Confirm button
        confirm_button = QPushButton("Delete")
        confirm_button.clicked.connect(self.accept)  # Close dialog on confirm
        layout.addWidget(confirm_button)

        self.setLayout(layout)

    def get_deletion_type(self):
        return self.deletion_type_combo.currentText()
    

def shred_file(file_path, passes=1):
    """
    Shred a file by overwriting it with random data for a specified number of passes.
    """
    try:
        with open(file_path, "r+b") as f:
            length = os.path.getsize(file_path)
            for _ in range(passes):
                f.seek(0)
                f.write(bytearray(random.getrandbits(8) for _ in range(length)))
        os.remove(file_path)
        print(f"File shredded: {file_path}")
    except Exception as e:
        print(f"Error shredding file {file_path}: {e}")


class ComparisonWindowVideo(QMainWindow):
    def __init__(self, duplicates):
        super().__init__()

        self.setWindowTitle('Review Video Duplicates')
        self.setFixedSize(1000, 900)

        # Main layout for the entire window
        main_layout = QVBoxLayout()

        # Store references to checkboxes and associated paths
        self.checkboxes = {}

        # Titles layout
        titles_widget = QWidget()
        titles_layout = QHBoxLayout(titles_widget)

        to_keep_label = QLabel("To Keep")
        to_delete_label = QLabel("To Be Deleted")

        to_keep_label.setFont(QFont('Palatino Linotype', 20))
        to_delete_label.setFont(QFont('Palatino Linotype', 20))

        to_keep_label.setAlignment(Qt.AlignCenter)
        to_delete_label.setAlignment(Qt.AlignCenter)

        titles_layout.addWidget(to_keep_label)
        titles_layout.addStretch()
        titles_layout.addWidget(to_delete_label)

        main_layout.addWidget(titles_widget)

        # Scroll area for viewing duplicates
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 2px solid black;  /* Set border width, style, and color */
            }
        """)

        # Widget to hold all duplicate comparisons
        container_widget = QWidget()
        scroll_area.setWidget(container_widget)

        # Layout to arrange the duplicate comparisons vertically
        layout = QVBoxLayout(container_widget)

        # Define the maximum width for each image
        max_image_width = 370
        max_image_height = 500

        # How many dupes
        total_duplicates = len(duplicates)

        for index, (vid1_path, vid2_path) in enumerate(duplicates):
            comparison_widget = QWidget()
            comparison_layout = QVBoxLayout(comparison_widget)
            comparison_layout.setSpacing(0)

            # Extract frame from middle of video for preview
            vid1_preview = self.get_video_frame_preview(vid1_path)
            vid2_preview = self.get_video_frame_preview(vid2_path)

            vid1_runtime = self.get_video_runtime(vid1_path)
            vid2_runtime = self.get_video_runtime(vid2_path)

            vid1_resolution = get_video_resolution(vid1_path)
            vid2_resolution = get_video_resolution(vid2_path)

            vid1_name = os.path.basename(vid1_path)
            vid2_name = os.path.basename(vid2_path)

            #Determine which video to keep
            if vid1_resolution[0] * vid1_resolution[1] > vid2_resolution[0] * vid2_resolution[1]:
                to_keep_path, to_delete_path = vid1_path, vid2_path
                to_keep_name, to_delete_name = vid1_name, vid2_name
                to_keep_preview, to_delete_preview = vid1_preview, vid2_preview
                to_keep_runtime, to_delete_runtime = vid1_runtime, vid2_runtime
                to_keep_resolution, to_delete_resolution = vid1_resolution, vid2_resolution
            elif vid1_resolution[0] * vid1_resolution[1] < vid2_resolution[0] * vid2_resolution[1]:
                to_keep_path, to_delete_path = vid2_path, vid1_path
                to_keep_name, to_delete_name = vid2_name, vid1_name
                to_keep_preview, to_delete_preview = vid2_preview, vid1_preview
                to_keep_runtime, to_delete_runtime = vid2_runtime, vid1_runtime
                to_keep_resolution, to_delete_resolution = vid2_resolution, vid1_resolution
            else:
                # Resolutions are equal, apply further checks
                if len(vid1_name) < len(vid2_name):
                    to_keep_path, to_delete_path = vid1_path, vid2_path
                    to_keep_name, to_delete_name = vid1_name, vid2_name
                    to_keep_preview, to_delete_preview = vid1_preview, vid2_preview
                    to_keep_runtime, to_delete_runtime = vid1_runtime, vid2_runtime
                    to_keep_resolution, to_delete_resolution = vid1_resolution, vid2_resolution
                elif len(vid1_name) > len(vid2_name):
                    to_keep_path, to_delete_path = vid2_path, vid1_path
                    to_keep_name, to_delete_name = vid2_name, vid1_name
                    to_keep_preview, to_delete_preview = vid2_preview, vid1_preview
                    to_keep_runtime, to_delete_runtime = vid2_runtime, vid1_runtime
                    to_keep_resolution, to_delete_resolution = vid2_resolution, vid1_resolution
                else:
                    # Name lengths are equal, prioritize alphabetically
                    if vid1_name < vid2_name:
                        to_keep_path, to_delete_path = vid1_path, vid2_path
                        to_keep_name, to_delete_name = vid1_name, vid2_name
                        to_keep_preview, to_delete_preview = vid1_preview, vid2_preview
                        to_keep_runtime, to_delete_runtime = vid1_runtime, vid2_runtime
                        to_keep_resolution, to_delete_resolution = vid1_resolution, vid2_resolution
                    else:
                        to_keep_path, to_delete_path = vid2_path, vid1_path
                        to_keep_name, to_delete_name = vid2_name, vid1_name
                        to_keep_preview, to_delete_preview = vid2_preview, vid1_preview
                        to_keep_runtime, to_delete_runtime = vid2_runtime, vid1_runtime
                        to_keep_resolution, to_delete_resolution = vid2_resolution, vid1_resolution

            # Format resolution for display
            to_keep_resolution_str = f"{to_keep_resolution[0]}x{to_keep_resolution[1]}"
            to_delete_resolution_str = f"{to_delete_resolution[0]}x{to_delete_resolution[1]}"
            
            # Horizontal layout for previews and labels
            filenames_widget = QWidget()
            filenames_layout = QHBoxLayout(filenames_widget)
            filenames_layout.setSpacing(10)

            to_keep_name_label = QLabel(f"NAME: {to_keep_name}\nDURATION: {to_keep_runtime}\nRESOLUTION: {to_keep_resolution_str}")
            to_keep_name_label.setAlignment(Qt.AlignLeft)
            to_keep_name_label.setStyleSheet("color: green; font-weight: bold;")

            to_delete_name_label = QLabel(f"NAME: {to_delete_name}\nDURATION: {to_delete_runtime}\nRESOLUTION: {to_delete_resolution_str}")
            to_delete_name_label.setAlignment(Qt.AlignRight)
            to_delete_name_label.setStyleSheet("color: red; font-weight: bold;")

            filenames_layout.addWidget(to_keep_name_label)
            filenames_layout.addStretch()
            filenames_layout.addWidget(to_delete_name_label)

            comparison_layout.addWidget(filenames_widget)

            #Horizontal Layout for images
            images_widget = QWidget()
            images_layout = QHBoxLayout(images_widget)
            images_layout.setSpacing(10)
            
            to_keep_label = QLabel()
            to_keep_pixmap = QPixmap(to_keep_preview)
            to_keep_label.setPixmap(to_keep_pixmap.scaled(max_image_width, max_image_height, Qt.KeepAspectRatio))

            to_delete_label = QLabel()
            to_delete_pixmap = QPixmap(to_delete_preview)
            to_delete_label.setPixmap(to_delete_pixmap.scaled(max_image_width, max_image_height, Qt.KeepAspectRatio))

            images_layout.addStretch()
            images_layout.addWidget(to_keep_label)
            images_layout.addStretch()
            images_layout.addWidget(to_delete_label)
            images_layout.addStretch()

            comparison_layout.addWidget(images_widget)

            # Add space above checkbox
            space_above_checkbox = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed)
            comparison_layout.addItem(space_above_checkbox)

            # Add a checkbox below the videos to decide deletion
            checkbox_layout = QHBoxLayout()
            checkbox_layout.addStretch()

            delete_checkbox = QCheckBox("Mark for deletion")
            delete_checkbox.setChecked(True)  # Default to checked
            checkbox_layout.addWidget(delete_checkbox)

            checkbox_layout.addStretch()
            comparison_layout.addLayout(checkbox_layout)

            # Store the checkbox and the paths in the dictionary
            self.checkboxes[delete_checkbox] = (to_keep_path, to_delete_path) # MAKE RESOLUTION COMPARISON TO "to_keep_path" variable

            # Add space between the images and the separator
            space_above_separator = QSpacerItem(20, 30, QSizePolicy.Minimum, QSizePolicy.Fixed)
            comparison_layout.addItem(space_above_separator)

            # Conditionally add a separator if this is not the last entry
            if index < len(duplicates) - 1:
                separator = QFrame()
                separator.setFrameShape(QFrame.HLine)
                separator.setFrameShadow(QFrame.Sunken)
                separator.setStyleSheet("background-color: black; height: 4px;")
                comparison_layout.addWidget(separator)

            layout.addWidget(comparison_widget)

        # Instead of addStretch() here, use QSpacerItem to avoid excessive space
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        comparison_layout.addItem(spacer)

        main_layout.addWidget(scroll_area)

        # Delete button at the bottom
        delete_button = QPushButton('Delete Duplicates', self)
        delete_button.clicked.connect(self.delete_duplicates)
        main_layout.addWidget(delete_button)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def get_video_frame_preview(self, video_path):
        """
        Extract a frame from the middle of the video to use as a preview.
        """
        frame_count = get_frame_count(video_path)
        middle_frame = frame_count // 2
        cap = cv2.VideoCapture(video_path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame)
        ret, frame = cap.read()
        cap.release()

        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return convert_frame_to_pixmap(frame_rgb)
        else:
            return QPixmap()  # Return empty pixmap if failed

    def get_video_runtime(self, video_path):
        """
        Get the runtime (duration) of the video in HH:MM:SS format.
        """
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()

        total_seconds = frame_count / fps
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    
    def delete_duplicates(self):
        # Similar logic as the ComparisonWindow class
        files_to_delete = [to_delete_path for checkbox, (to_keep_path, to_delete_path) in self.checkboxes.items() if checkbox.isChecked()]

        if not files_to_delete:
            QMessageBox.information(self, "No Files Selected", "Please mark files for deletion.")
            return

        # Show deletion confirmation dialog
        dialog = DeletionConfirmationDialog(len(files_to_delete))
        if dialog.exec_() == QDialog.Accepted:
            deletion_type = dialog.get_deletion_type()

            for to_delete_path in files_to_delete:
                print(f"Deleting {to_delete_path}")
                try:
                    if deletion_type == "Normal Deletion":
                        os.remove(to_delete_path)
                        print(f"File deleted: {to_delete_path}")
                    elif "Shred" in deletion_type:
                        if "1 Pass" in deletion_type:
                            shred_file(to_delete_path, passes=1)
                        elif "3 Passes" in deletion_type:
                            shred_file(to_delete_path, passes=3)
                        elif "7 Passes" in deletion_type:
                            shred_file(to_delete_path, passes=7)
                except Exception as e:
                    print(f"Error deleting file {to_delete_path}: {e}")

            QMessageBox.information(self, "Deletion Complete", f"{len(files_to_delete)} files have been deleted.")



def main():
    app = QApplication(sys.argv)
    window = DuplicateImageFinder()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()