import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QFileDialog, QMessageBox, QScrollArea, QVBoxLayout, QWidget, QHBoxLayout, QFrame, QSpacerItem, QSizePolicy, QCheckBox, QDialog, QComboBox, QRadioButton, QProgressBar
)
from PyQt5.QtGui import QPixmap, QFont, QImage, QIcon
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from duplicate_detector import find_duplicates, get_image_resolution, get_frame_count, find_video_duplicates, get_video_resolution, get_video_runtime  # Import the duplicate detection module
import os
import random
import cv2
from PIL import Image
import numpy as np
from pywinstyles import apply_style


## TODO: ICONS next to important stuff
## TODO: FONTS
## TODO: DISPLAY IMAGE SIZE
## TODO: Ui work, progress bar/dynamic loading icons
## BUG: Not correct deletion when theres 3 duplicates in varying sizes. - might be fix, test 3 images in differing res
## NAME: COPY CLEANER
## TODO: Change button color etc, find a style, for example purple.
## TODO: Back to main menu after deletion.
## BUG: Hangout when having to draw large amount of photos in comparisonwindow

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

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
        self.setWindowTitle('CopyCleaner - Easy Media Deduplication')
        self.width = 600
        self.height = 700
        self.setFixedSize(self.width, self.height)
        self.setStyleSheet('background-color: #111111;')
        self.setWindowIcon(QIcon(resource_path('resources/IconOnly.ico')))
        apply_style(self, "dark")

        self.button_font = QFont('Impact', 16)
        self.text_font = QFont('Impact', 11)

        # Logo
        self.logo_label = QLabel(self)
        self.logo_pixmap = QPixmap(resource_path('resources/FullLogo.png'))  # Replace with the path to your logo
        self.logo_label.setPixmap(self.logo_pixmap.scaled(300, 300, Qt.KeepAspectRatio))
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setFixedSize(300, 300)
        self.logo_label.move((self.width - 300) // 2, 0)  # Center the logo at the top

        # Button to choose folder
        self.folder_button = QPushButton('Choose Folder', self)
        self.folder_button.setFixedSize(180, 40)
        self.folder_button.setStyleSheet("""
            QPushButton {
                background-color: #1E88E5;
                border: 3px solid #1565C0;
                border-radius: 10px;
                color: black;
            }
            QPushButton:hover {
                background-color: #64B5F6;
                border-color: #1565C0;
            }
            QPushButton:pressed {
                background-color: #1E88E5;
                border-color: #1565C0;
            }
        """)
        self.folder_button.setFont(self.button_font)
        self.folder_button.move((self.width - 180) // 2, 300)  # Center the button below the logo
        self.folder_button.clicked.connect(self.choose_folder)

        # Label to show the chosen folder path
        self.folder_label = QLabel('No folder chosen', self)
        self.folder_label.setFixedSize(600, 40)
        self.folder_label.setAlignment(Qt.AlignCenter)
        self.folder_label.setStyleSheet('color: white;')
        self.folder_label.setFont(self.text_font)
        self.folder_label.move((self.width - 600) // 2, 340)  # Center this label below the button

        #Radio buttons
        self.photo_radio = QRadioButton('Search for Photo Duplicates', self)
        self.video_radio = QRadioButton('Search for Video Duplicates', self)
        self.photo_radio.setFixedSize(200,30)
        self.video_radio.setFixedSize(200,30)
        self.photo_radio.setChecked(True)
        self.photo_radio.move((self.width - 200) // 2, 400)
        self.video_radio.move((self.width - 200) // 2, 430)
        radio_button_style = """
            QRadioButton {
                color: white; /* Text color for a dark background */
                background-color: transparent; /* Background color */
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
            QRadioButton::indicator::unchecked {
                border: 1px solid white; /* Border for unchecked state */
                background-color: #333333; /* Dark gray background for unchecked */
            }
            QRadioButton::indicator::checked {
                border: 1px solid white; /* Border for checked state */
                background-color: #00FF00; /* Green background for checked state */
            }
        """
        self.photo_radio.setStyleSheet(radio_button_style)
        self.video_radio.setStyleSheet(radio_button_style)
        self.photo_radio.setFont(self.text_font)
        self.video_radio.setFont(self.text_font)

        # Start button
        self.start_button = QPushButton('Search for Duplicates', self)
        self.start_button.setFixedSize(250, 55)
        self.start_button.move((self.width - 250) // 2, 500)  # Center the button below the folder label
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #1E88E5;
                border: 3px solid #1565C0;
                border-radius: 10px;
                color: black;
            }
            QPushButton:hover {
                background-color: #64B5F6;
                border-color: #1565C0;
            }
            QPushButton:pressed {
                background-color: #1E88E5;
                border-color: #1565C0;
            }
        """)
        self.start_button.setFont(self.button_font)
        self.start_button.clicked.connect(self.start_processing)

        # Progress bar (initially hidden)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setFixedSize(400, 30)
        self.progress_bar.move((self.width - 400) // 2, 500)  # Same position as the start button
        self.progress_bar.setVisible(False)

        # Store the selected folder path
        self.selected_folder = None
        self.worker_thread = None

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select Folder')
        if folder:
            self.selected_folder = folder
            self.folder_label.setText(f'Selected Folder: {folder}')

    def start_processing(self):
        if not self.selected_folder:
            QMessageBox.critical(self, "Error", "Please choose a folder before starting!")
            return

        self.start_button.setVisible(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        search_type = 'photo' if self.photo_radio.isChecked() else 'video'
        self.worker_thread = DuplicateFinderWorker(self.selected_folder, search_type)
        self.worker_thread.progress_update.connect(self.progress_bar.setValue)
        self.worker_thread.comparison_complete.connect(self.on_comparison_complete)
        self.worker_thread.start()

    def on_comparison_complete(self, comparison_results):
        if not comparison_results:
            QMessageBox.information(self, "No Duplicates Found", "No duplicates were found in the selected folder.")
            self.reset_ui()
            return

        # Prepare the comparison window based on the results
        if self.photo_radio.isChecked():
            self.show_comparison_window(comparison_results)
        elif self.video_radio.isChecked():
            self.show_comparison_window_videos(comparison_results)

        self.reset_ui()

    def reset_ui(self):
        """Reset the UI to initial state after processing is complete."""
        self.start_button.setVisible(True)
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)


    def show_comparison_window(self, comparison_results):
        self.comparison_window = ComparisonWindow(comparison_results)
        self.comparison_window.show()

    def show_comparison_window_videos(self, video_comparison_results):
        self.comparison_window_videos = ComparisonWindowVideo(video_comparison_results)
        self.comparison_window_videos.show()


class ComparisonWindow(QMainWindow):
    def __init__(self, comparison_results):
        super().__init__()

        self.setWindowTitle('Review Duplicates')
        self.setFixedSize(1000, 900)  # Increase window size
        apply_style(self, "dark")

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
        total_duplicates = len(comparison_results)

        for index, (to_keep, to_delete) in enumerate(comparison_results):
            # Extract precomputed data
            to_keep_path, to_keep_name, to_keep_res, to_keep_folder, to_keep_phash = to_keep
            to_delete_path, to_delete_name, to_delete_res, to_delete_folder, to_delete_phash = to_delete

            comparison_widget = QWidget()
            comparison_layout = QVBoxLayout(comparison_widget)
            comparison_layout.setSpacing(0)

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
    def __init__(self, comparison_results):
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
        total_duplicates = len(comparison_results)

        for index, (to_keep, to_delete) in enumerate(comparison_results):
            # Extract precomputed data
            to_keep_path, to_keep_name, to_keep_runtime, to_keep_resolution, to_keep_preview = to_keep
            to_delete_path, to_delete_name, to_delete_runtime, to_delete_resolution, to_delete_preview = to_delete

            comparison_widget = QWidget()
            comparison_layout = QVBoxLayout(comparison_widget)
            comparison_layout.setSpacing(0)

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
            if index < len(comparison_results) - 1:
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

class DuplicateFinderWorker(QThread):
    progress_update = pyqtSignal(int)  # Signal to update progress bar
    comparison_complete = pyqtSignal(list)  # Signal to emit the comparison results

    def __init__(self, folder_path, search_type):
        super().__init__()
        self.folder_path = folder_path
        self.search_type = search_type

    def run(self):
        # Find duplicates
        if self.search_type == 'photo':
            duplicates = find_duplicates(self.folder_path, self.update_finding_progress)
        elif self.search_type == 'video':
            duplicates = find_video_duplicates(self.folder_path, self.update_comparing_progress)
        else:
            duplicates = []

        # If duplicates found, perform comparisons
        if duplicates:
            comparison_results = self.compare_duplicates(duplicates)
            self.comparison_complete.emit(comparison_results)
        else:
            self.comparison_complete.emit([])

    def update_progress(self, progress):
        self.progress_update.emit(progress)

    def update_finding_progress(self, progress):
        # Adjust progress to fit within the first 50% range
        adjusted_progress = int(progress * 0.5)  # Mapping to 0-50 range
        self.update_progress(adjusted_progress)

    def update_comparing_progress(self, progress):
        # Adjust progress to fit within the remaining 50% range
        adjusted_progress = 50 + int(progress * 0.5)  # Mapping to 50-100 range
        self.update_progress(adjusted_progress)

    def compare_duplicates(self, duplicates):
        comparison_results = []
        total_comparisons = len(duplicates)
        
        # Choose the comparison method based on the search type
        if self.search_type == 'photo':
            for index, (img1_path, img2_path, img1_hash, img2_hash) in enumerate(duplicates):
                comparison_result = self.compare_two_images(img1_path, img2_path, img1_hash, img2_hash)
                comparison_results.append(comparison_result)
                self.update_comparing_progress(int((index + 1) / total_comparisons * 100))
                # Yield to the event loop
                QThread.msleep(1)  # Short sleep to allow UI updates
                QApplication.processEvents()  # Process UI events to keep UI responsive
        elif self.search_type == 'video':
            for index, (vid1_path, vid2_path) in enumerate(duplicates):
                comparison_result = self.compare_two_videos(vid1_path, vid2_path)
                comparison_results.append(comparison_result)
                self.update_comparing_progress(int((index + 1) / total_comparisons * 100))
                # Yield to the event loop
                QThread.msleep(1)  # Short sleep to allow UI updates
                QApplication.processEvents()  # Process UI events to keep UI responsive
        
        return comparison_results

    def compare_two_images(self, img1_path, img2_path, img1_hash, img2_hash):
        img1_name = os.path.basename(img1_path)
        img2_name = os.path.basename(img2_path)
        img1_resolution = get_image_resolution(img1_path)[1]
        img2_resolution = get_image_resolution(img2_path)[1]
        img1_folder = os.path.basename(os.path.dirname(img1_path))
        img2_folder = os.path.basename(os.path.dirname(img2_path))
        print(f'IN COMPARE FUNCTION: Comparing {img1_name} AND {img2_name}')

        if img1_resolution > img2_resolution:
            to_keep = (img1_path, img1_name, img1_resolution, img1_folder, img1_hash)
            to_delete = (img2_path, img2_name, img2_resolution, img2_folder, img2_hash)
        elif img1_resolution < img2_resolution:
            to_keep = (img2_path, img2_name, img2_resolution, img2_folder, img2_hash)
            to_delete = (img1_path, img1_name, img1_resolution, img1_folder, img1_hash)
        else:
            if len(img1_name) < len(img2_name) or (len(img1_name) == len(img2_name) and img1_name < img2_name):
                to_keep = (img1_path, img1_name, img1_resolution, img1_folder, img1_hash)
                to_delete = (img2_path, img2_name, img2_resolution, img2_folder, img2_hash)
            else:
                to_keep = (img2_path, img2_name, img2_resolution, img2_folder, img2_hash)
                to_delete = (img1_path, img1_name, img1_resolution, img1_folder, img1_hash)

        return (to_keep, to_delete)
    
    def compare_two_videos(self, vid1_path, vid2_path):
        vid1_name = os.path.basename(vid1_path)
        vid2_name = os.path.basename(vid2_path)
        vid1_resolution = get_video_resolution(vid1_path)
        vid2_resolution = get_video_resolution(vid2_path)
        print(f'paths: {vid1_path} 2: {vid2_path}')
        vid1_runtime = get_video_runtime(vid1_path)
        vid2_runtime = get_video_runtime(vid2_path)
        vid1_folder = os.path.basename(os.path.dirname(vid1_path))
        vid2_folder = os.path.basename(os.path.dirname(vid2_path))

        print(f'IN COMPARE FUNCTION: Comparing {vid1_name} AND {vid2_name}')

        # Compare based on resolution and then on runtime
        if vid1_resolution[0] * vid1_resolution[1] > vid2_resolution[0] * vid2_resolution[1]:
            to_keep = (vid1_path, vid1_name, vid1_runtime, vid1_resolution, self.get_video_frame_preview(vid1_path))
            to_delete = (vid2_path, vid2_name, vid2_runtime, vid2_resolution, self.get_video_frame_preview(vid2_path))
        elif vid1_resolution[0] * vid1_resolution[1] < vid2_resolution[0] * vid2_resolution[1]:
            to_keep = (vid2_path, vid2_name, vid2_runtime, vid2_resolution, self.get_video_frame_preview(vid2_path))
            to_delete = (vid1_path, vid1_name, vid1_runtime, vid1_resolution, self.get_video_frame_preview(vid1_path))
        else:
            # If resolutions are equal, use name length and alphabetical order
            if len(vid1_name) < len(vid2_name) or (len(vid1_name) == len(vid2_name) and vid1_name < vid2_name):
                to_keep = (vid1_path, vid1_name, vid1_runtime, vid1_resolution, self.get_video_frame_preview(vid1_path))
                to_delete = (vid2_path, vid2_name, vid2_runtime, vid2_resolution, self.get_video_frame_preview(vid2_path))
            else:
                to_keep = (vid2_path, vid2_name, vid2_runtime, vid2_resolution, self.get_video_frame_preview(vid2_path))
                to_delete = (vid1_path, vid1_name, vid1_runtime, vid1_resolution, self.get_video_frame_preview(vid1_path))

        return (to_keep, to_delete)

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
        




def main():
    app = QApplication(sys.argv)
    window = DuplicateImageFinder()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()