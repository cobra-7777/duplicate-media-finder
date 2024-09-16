import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QFileDialog, QMessageBox, QScrollArea, QVBoxLayout, QWidget, QHBoxLayout, QFrame, QSpacerItem, QSizePolicy, QCheckBox, QDialog, QComboBox, QRadioButton, QProgressBar
)
from PyQt5.QtGui import QPixmap, QFont, QImage, QIcon
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from duplicate_detector import find_duplicates, get_image_resolution, get_frame_count, find_video_duplicates, get_video_resolution, get_video_runtime  # Import the duplicate detection module
import os
from random import getrandbits
from cv2 import VideoCapture, cvtColor, COLOR_BGR2RGB, CAP_PROP_POS_FRAMES
from pywinstyles import apply_style
import logging_wrapper

## TODO: ICONS next to important stuff
## TODO: FONTS
## TODO: DISPLAY IMAGE SIZE
## TODO: Ui work, progress bar/dynamic loading icons
## BUG: Not correct deletion when theres 3 duplicates in varying sizes. - might be fix, test 3 images in differing res
## TODO: Change button color etc, find a style, for example purple.

# Setup the logger
logging_wrapper.setup_logger()

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

def truncate_name(name, max_length=50):
    """
    Truncate the file name if it exceeds the maximum length.
    """
    if len(name) > max_length:
        return name[:max_length] + '...'  # Truncate and add ellipsis
    return name

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

        self.button_font = QFont('Calibri Bold', 16)
        self.text_font = QFont('Segoe UI', 11)
        logging_wrapper.log_info('Drawing the main UI...')

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
                background-color: #AC3AA7;
                border: 3px solid #982FBD;
                border-radius: 10px;
                color: black;
            }
            QPushButton:hover {
                background-color: #D45379;
                border-color: #982FBD;
            }
            QPushButton:pressed {
                background-color: #AC3AA7;
                border-color: #982FBD;
            }
        """)
        self.folder_button.setFont(self.button_font)
        self.folder_button.move((self.width - 180) // 2, 300)  # Center the button below the logo
        self.folder_button.clicked.connect(self.choose_folder)

        # Widget to hold both icon and text
        folder_widget = QWidget(self)
        folder_layout = QHBoxLayout(folder_widget)

        # Icon QLabel
        icon_label = QLabel(self)
        folder_icon = QPixmap(resource_path('resources/folder.png')).scaled(25, 25, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        icon_label.setPixmap(folder_icon)

        # Text QLabel
        folder_text_label = QLabel('No folder chosen', self)
        folder_text_label.setStyleSheet('color: white;')
        folder_text_label.setFont(self.text_font)

        # Add icon and text labels to layout
        folder_layout.addWidget(icon_label)
        folder_layout.addWidget(folder_text_label)
        folder_layout.setAlignment(Qt.AlignCenter)  # Center align both icon and text

        # Set folder_widget properties and add it to the main window
        folder_widget.setLayout(folder_layout)
        folder_widget.setFixedSize(600, 40)
        folder_widget.move((self.width - 600) // 2, 340)  # Position widget

        self.folder_label = folder_text_label  # To access the text label directly later

        #Radio buttons
        self.photo_radio = QRadioButton('Search for Photo Duplicates', self)
        self.video_radio = QRadioButton('Search for Video Duplicates', self)
        self.photo_radio.setFixedSize(215,30)
        self.video_radio.setFixedSize(215,30)
        self.photo_radio.setChecked(True)
        self.photo_radio.move((self.width - 215) // 2, 400)
        self.video_radio.move((self.width - 215) // 2, 430)
        radio_button_style = """
            QRadioButton {
                color: white; /* Text color for a dark background */
                background-color: transparent; /* Background color */
                spacing: 10px; /* Space between indicator and text */
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
                border-radius: 8px; /* Makes the indicator round */
            }
            QRadioButton::indicator::unchecked {
                border: 2px solid #CCCCCC; /* Lighter border for unchecked state */
                background-color: #333333; /* Dark gray background for unchecked */
                border-radius: 8px; /* Rounded corners for indicator */
            }
            QRadioButton::indicator::checked {
                border: 2px solid #932CC3; /* Border color when checked */
                background-color: #AC3AA7; /* Checked color */
                border-radius: 8px; /* Rounded corners for indicator */
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
                background-color: #AC3AA7;
                border: 3px solid #982FBD;
                border-radius: 10px;
                color: black;
            }
            QPushButton:hover {
                background-color: #D45379;
                border-color: #982FBD;
            }
            QPushButton:pressed {
                background-color: #AC3AA7;
                border-color: #982FBD;
            }
        """)
        self.start_button.setFont(self.button_font)
        self.start_button.clicked.connect(self.start_processing)

        # Progress bar for loading widgets
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setFixedSize(400, 30)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)  # Show text inside the progress bar
        self.progress_bar.setFormat("Searching... %p%")  # Custom text format inside the progress bar
        self.progress_bar.setAlignment(Qt.AlignCenter)  # Align text to center

        # Style the progress bar
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;  /* Align text to center */
                background-color: white;
                color: black;  /* Text color inside the progress bar */
            }
            QProgressBar::chunk {
                background-color: #AA39A9;  /* Change the progress color */
                width: 20px;
            }
        """)
        self.progress_bar.move((self.width - 400) // 2, 500)
        self.progress_bar.setVisible(False)

        # Store the selected folder path
        self.selected_folder = None
        self.worker_thread = None

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select Folder')
        if folder:
            self.selected_folder = folder
            self.folder_label.setText(f'Selected Folder: {folder}')
            logging_wrapper.log_info(f"Folder: '{folder}' was selected.")

    def start_processing(self):
        if not self.selected_folder:
            error_dialog = ErrorDialog("Error", "Please select a folder that contains media files,\nor subfolders with media files to search through.")
            error_dialog.exec_()
            logging_wrapper.log_error("A folder with no media files was chosen.")
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
            self.reset_ui()
            success_dialog = SuccessDialog('All Good!', "We've searched far and wide, but it seems that there\nare no duplicate media files in this directory. Yay!")
            success_dialog.exec_()
            logging_wrapper.log_info('Processing returned no duplicates found.')
            #self.reset_ui()
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
        logging_wrapper.log_info("Drawing comparison window...")
        self.comparison_window.show()

    def show_comparison_window_videos(self, video_comparison_results):
        self.comparison_window_videos = ComparisonWindowVideo(video_comparison_results)
        logging_wrapper.log_info("Drawing comparison video window...")
        self.comparison_window_videos.show()


class ComparisonWindow(QMainWindow):
    def __init__(self, comparison_results):
        super().__init__()

        self.setWindowTitle('Review Duplicates')
        self.setFixedSize(1000, 900)
        self.setStyleSheet('background-color: #111111;')
        self.setWindowIcon(QIcon(resource_path('resources/IconOnly.ico')))
        apply_style(self, "dark")

        self.default_pixmap = QPixmap(resource_path('resources/nopreview.png'))

        self.button_font = QFont('Calibri Bold', 16)

        # Main layout for the entire window
        self.main_layout = QVBoxLayout()

        # Titles layout
        titles_widget = QWidget()
        titles_layout = QHBoxLayout(titles_widget)

        # Load icons
        keep_icon = QPixmap(resource_path('resources/keep.png')).scaled(35, 35, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        delete_icon = QPixmap(resource_path('resources/delete.png')).scaled(35, 35, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        to_keep_icon = QLabel()
        to_keep_icon.setPixmap(keep_icon)
        to_keep_icon.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        to_delete_icon = QLabel()
        to_delete_icon.setPixmap(delete_icon)
        to_delete_icon.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        to_keep_label = QLabel("TO KEEP")
        to_delete_label = QLabel("TO BE DELETED")

        to_keep_label.setFont(QFont('Segoe UI', 20))
        to_delete_label.setFont(QFont('Segoe UI', 20))

        to_keep_label.setStyleSheet('color: white;')
        to_delete_label.setStyleSheet('color: white;')

        to_keep_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        to_delete_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        titles_layout.addWidget(to_keep_icon)
        titles_layout.addWidget(to_keep_label)
        titles_layout.addStretch()
        titles_layout.addWidget(to_delete_label)
        titles_layout.addWidget(to_delete_icon)

        self.main_layout.addWidget(titles_widget)

        # Scroll area for viewing duplicates
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True) ##932CC3
        self.scroll_area.setStyleSheet("""
            QScrollBar:vertical {
                border: none;
                background-color: #2d2d2d;  /* Dark background color */
                width: 10px;  /* Adjust the width of the scrollbar */
                margin: 0px 0px 0px 0px;
            }

            QScrollBar::handle:vertical {
                background-color: #932CC3;  /* Lighter gray for the handle */
                min-height: 30px;  /* Minimum height for the handle */
                border-radius: 5px;  /* Rounded corners for the handle */
            }

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;  /* Remove arrows (if you want) */
                height: 0px;  /* Set height to 0 to hide arrows */
            }

            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;  /* Background for pages (if you want to remove) */
            }
            
            QScrollArea {
                border: 2px solid #932CC3;                           
            }
        """)

        # Widget to hold all duplicate comparisons
        self.container_widget = QWidget()
        self.scroll_area.setWidget(self.container_widget)

        # Layout to arrange the duplicate comparisons vertically
        self.layout = QVBoxLayout(self.container_widget)

        self.main_layout.addWidget(self.scroll_area)

        # Progress bar for loading widgets
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)  # Show text inside the progress bar
        self.progress_bar.setFormat("Loading Duplicates... %p%")  # Custom text format inside the progress bar
        self.progress_bar.setAlignment(Qt.AlignCenter)  # Align text to center

        # Style the progress bar
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;  /* Align text to center */
                background-color: white;
                color: black;  /* Text color inside the progress bar */
            }
            QProgressBar::chunk {
                background-color: #AA39A9;  /* Change the progress color */
                width: 20px;
            }
        """)
        self.main_layout.addWidget(self.progress_bar)

        # Progress bar for deleting
        self.delete_progress_bar = QProgressBar(self)
        self.delete_progress_bar.setValue(0)
        self.delete_progress_bar.setTextVisible(True)  # Show text inside the progress bar
        self.delete_progress_bar.setFormat("Deleting Duplicates... %p%")  # Custom text format inside the progress bar
        self.delete_progress_bar.setAlignment(Qt.AlignCenter)  # Align text to center
        self.delete_progress_bar.hide()

        # Style the progress bar
        self.delete_progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;  /* Align text to center */
                background-color: white;
                color: black;  /* Text color inside the progress bar */
            }
            QProgressBar::chunk {
                background-color: #AA39A9;  /* Change the progress color */
                width: 20px;
            }
        """)
        self.main_layout.addWidget(self.delete_progress_bar)

        # Store references to checkboxes and associated paths
        self.checkboxes = {}
        self.comparison_results = comparison_results
        self.current_index = 0

        # Timer for incremental loading
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_next_batch)
        self.timer.start(10)  # Adjust the interval as needed

        # Delete button, initially hidden
        self.delete_button = QPushButton('Review Deletion', self)
        self.delete_button.clicked.connect(self.show_deletion_dialog)
        self.delete_button.setStyleSheet("""
            QPushButton {
                background-color: #AC3AA7;
                border: 3px solid #982FBD;
                border-radius: 10px;
                color: black;
            }
            QPushButton:hover {
                background-color: #D45379;
                border-color: #982FBD;
            }
            QPushButton:pressed {
                background-color: #AC3AA7;
                border-color: #982FBD;
            }
        """)
        self.delete_button.setFixedSize(240,45)
        self.delete_button.setFont(self.button_font)
        self.delete_button.hide()  # Start hidden

        button_layout = QHBoxLayout()
        button_layout.addStretch()  # Add stretchable space to the left
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()  # Add stretchable space to the right

        self.main_layout.addLayout(button_layout)

        # Initialize the batch size
        self.batch_size = 8  # Number of items to load per batch

        central_widget = QWidget()
        central_widget.setLayout(self.main_layout)
        self.setCentralWidget(central_widget)

    def load_next_batch(self):
        """Load the next batch of comparison widgets."""
        for _ in range(self.batch_size):
            if self.current_index >= len(self.comparison_results):
                self.timer.stop()
                # Hide progress bar and show delete button when done
                self.progress_bar.hide()
                self.update_delete_button_text()
                self.delete_button.show()
                return

            to_keep, to_delete = self.comparison_results[self.current_index]
            self.create_comparison_widget(to_keep, to_delete)
            self.current_index += 1

            # Update progress bar
            self.progress_bar.setValue(int((self.current_index / len(self.comparison_results)) * 100))

    def create_comparison_widget(self, to_keep, to_delete):
        """Create and add widgets based on the provided data."""
        to_keep_path, to_keep_name, to_keep_res, to_keep_folder, to_keep_phash = to_keep
        to_delete_path, to_delete_name, to_delete_res, to_delete_folder, to_delete_phash = to_delete

        # Truncate names if too long
        to_keep_name = truncate_name(to_keep_name)
        to_delete_name = truncate_name(to_delete_name)

        comparison_widget = QWidget()
        comparison_layout = QVBoxLayout(comparison_widget)
        comparison_layout.setSpacing(0)

        # Horizontal layout for filenames and resolutions
        filenames_widget = QWidget()
        filenames_layout = QHBoxLayout(filenames_widget)
        filenames_layout.setSpacing(10)

        to_keep_name_label = QLabel(f"NAME: {to_keep_name}\nRESOLUTION: {to_keep_res[0]}x{to_keep_res[1]}\nP-HASH: {to_keep_phash}\nLOCATION: {to_keep_folder}")
        to_keep_name_label.setAlignment(Qt.AlignLeft)
        to_keep_name_label.setFont(QFont('Segoe UI', 10))
        to_keep_name_label.setStyleSheet("color: green; font-weight: bold;")

        to_delete_name_label = QLabel(f"NAME: {to_delete_name}\nRESOLUTION: {to_delete_res[0]}x{to_delete_res[1]}\nP-HASH: {to_delete_phash}\nLOCATION: {to_delete_folder}")
        to_delete_name_label.setAlignment(Qt.AlignRight)
        to_delete_name_label.setFont(QFont('Segoe UI', 10))
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
        if to_keep_pixmap.isNull():
            to_keep_pixmap = self.default_pixmap.scaled(370,500,Qt.KeepAspectRatio)
        to_keep_label.setPixmap(to_keep_pixmap.scaled(370, 500, Qt.KeepAspectRatio))


        to_delete_label = QLabel()
        to_delete_pixmap = QPixmap(to_delete_path)
        if to_delete_pixmap.isNull():
            to_delete_pixmap = self.default_pixmap.scaled(370,500,Qt.KeepAspectRatio)
        to_delete_label.setPixmap(to_delete_pixmap.scaled(370, 500, Qt.KeepAspectRatio))


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

        delete_checkbox = QCheckBox("Mark For Deletion")
        delete_checkbox.setStyleSheet('color: white;')
        delete_checkbox.setFont(QFont('Segoe UI', 14))
        delete_checkbox.setChecked(True)
        delete_checkbox.setStyleSheet("""
            QCheckBox {
                color: white;
                font-size: 14pt; /* Font size */
            }
            QCheckBox::indicator {
                width: 18px; /* Width of the checkbox */
                height: 18px; /* Height of the checkbox */
            }
            QCheckBox::indicator:checked {
                background-color: #932CC3; /* Custom color for checked state */
                border: 2px solid white; /* Border color and size */
            }
            QCheckBox::indicator:unchecked {
                background-color: #333333; /* Custom color for unchecked state */
                border: 2px solid white; /* Border color and size */
            }
        """)

        # Connect state change signal to update function
        delete_checkbox.stateChanged.connect(self.update_delete_button_text)

        checkbox_layout.addWidget(delete_checkbox)

        checkbox_layout.addStretch()
        comparison_layout.addLayout(checkbox_layout)

        self.checkboxes[delete_checkbox] = (to_keep_path, to_delete_path)

        # Add space between the images and the separator
        space_above_separator = QSpacerItem(20, 30, QSizePolicy.Minimum, QSizePolicy.Fixed)
        comparison_layout.addItem(space_above_separator)

        # Separator
        if self.current_index < len(self.comparison_results) - 1:
            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setFrameShadow(QFrame.Plain)
            separator.setStyleSheet("background-color: #932CC3;") ##932CC3
            separator.setMinimumHeight(4)
            comparison_layout.addWidget(separator)

        self.layout.addWidget(comparison_widget)

        # Instead of addStretch() here, use QSpacerItem to avoid excessive space
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        comparison_layout.addItem(spacer)
    
    def update_delete_button_text(self):
        # Count the checked checkboxes
        marked_for_deletion = sum(checkbox.isChecked() for checkbox in self.checkboxes)
        # Update the button text
        self.delete_button.setText(f'Review Deletion ({marked_for_deletion})')

    def show_deletion_dialog(self):
        num_files = len([checkbox for checkbox in self.checkboxes if checkbox.isChecked()])
        if num_files == 0:
            error_dialog = ErrorDialog('Error', 'Whoops!\nSeems like you forgot to mark any files for deletion.')
            error_dialog.exec_()
            return
        
        dialog = DeletionConfirmationDialog(num_files)
        if dialog.exec_() == QDialog.Accepted:
            self.delete_progress_bar.setVisible(True)
            self.delete_button.setVisible(False)
            deletion_type = dialog.get_deletion_type()
            self.start_deletion(deletion_type)

    def start_deletion(self, deletion_type):
        self.deletion_worker = DeletionWorker(self.checkboxes, deletion_type)
        self.deletion_worker.progress_update.connect(self.update_progress_bar)
        self.deletion_worker.deletion_complete.connect(self.on_deletion_complete)
        self.deletion_worker.start()

    def update_progress_bar(self, value):
        self.delete_progress_bar.setValue(value)

    def on_deletion_complete(self):
        self.delete_progress_bar.setVisible(False)
        success_delete_dialog = SuccessDialog('Deletion Complete!', f'Woohoo!\nSuccessfully deleted the marked duplicates!')
        success_delete_dialog.exec_()
        self.close()


class DeletionConfirmationDialog(QDialog):
    def __init__(self, num_files):
        super().__init__()
        self.setWindowTitle("Confirm Deletion")
        self.setFixedSize(610, 330)
        apply_style(self, "dark")
        self.setWindowIcon(QIcon(resource_path('resources/deleteico.ico')))
        self.setStyleSheet('background-color: #111111;')
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout()

        # Number of files to delete
        label = QLabel(f"You've marked {num_files} duplicate files for deletion.\nIf this is a mistake, close this window, and you can check through\nthe duplicates again, and choose which ones are marked for deletion.")
        label.setFont(QFont('Segoe UI', 14))
        label.setStyleSheet('color: white;')
        layout.addWidget(label)

        space_above_separator = QSpacerItem(20, 30, QSizePolicy.Minimum, QSizePolicy.Fixed)
        layout.addItem(space_above_separator)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Plain)
        separator.setStyleSheet("background-color: #932CC3;")  # #932CC3
        separator.setMinimumHeight(4)
        layout.addWidget(separator)

        
        space_above_separator = QSpacerItem(20, 30, QSizePolicy.Minimum, QSizePolicy.Fixed)
        layout.addItem(space_above_separator)

        # Label to explain the dropdown usage
        deletion_type_label = QLabel("Choose the deletion type for the selected duplicates:")
        deletion_type_label.setStyleSheet('color: white;')  # Style to match the rest of your UI
        deletion_type_label.setFont(QFont('Segoe UI', 14))
        layout.addWidget(deletion_type_label)

        # Dropdown for deletion type with improved styling
        h_layout = QHBoxLayout()
        self.deletion_type_combo = QComboBox()
        self.deletion_type_combo.addItems(["Normal Deletion", "Shred (1 Pass)", "Shred (7 Passes) (Military Standard)", "Shred (15 Passes)"])
        self.deletion_type_combo.setStyleSheet("""
            QComboBox {
                background-color: #333333; /* Dark background for dropdown */
                color: white; /* Text color for dropdown */
                border: 1px solid #932CC3; /* Border color to match theme */
                border-radius: 5px;
                padding: 5px; /* Padding inside the dropdown */
            }
            QComboBox QAbstractItemView {
                background-color: #333333; /* Dark background for dropdown items */
                color: white; /* Text color for all dropdown items */
                selection-background-color: #444444; /* Highlight color when an item is selected */
                selection-color: white; /* Text color of the selected item */
            }
        """)
        self.deletion_type_combo.setFont(QFont('Segoe UI', 14))
        # Set the dropdown to expand
        self.deletion_type_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        h_layout.addWidget(self.deletion_type_combo)

        # Tooltip icon
        tooltip_icon = QLabel()
        tooltip_pixmap = QPixmap(resource_path('resources/tooltip.png')).scaled(30, 30, Qt.KeepAspectRatio)
        tooltip_icon.setPixmap(tooltip_pixmap)
        tooltip_icon.setToolTip("Information about different types of deletion:\n\n"
                                "- Normal Deletion: Deletes the files like you would normally in Windows.\n\n"
                                "- Shred (1 Pass): Overwrites the files 1 time with random data,\nbefore deleting them, making the files difficult to recover.\n\n"
                                "- Shred (7 Passes): Overwrites the files 7 times with random data,\nbefore deleting them, making the files almost impossible to recover.\nThis is the military standard for deleting classified files.\n\n"
                                "- Shred (15 Passes): Overwrites the files 15 times with random data,\nbefore deleting them, making the files virtually impossible recover.")

        # Add the tooltip icon to the horizontal layout
        h_layout.addWidget(tooltip_icon)
        
        layout.addLayout(h_layout)
        
        # Instead of addStretch() here, use QSpacerItem to avoid excessive space
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(spacer)

        # Confirm button
        confirm_button = QPushButton("Delete Selected Duplicates")
        confirm_button.clicked.connect(self.accept)  # Close dialog on confirm
        confirm_button.setStyleSheet("""
            QPushButton {
                background-color: #AC3AA7;
                border: 3px solid #982FBD;
                border-radius: 10px;
                color: black;
            }
            QPushButton:hover {
                background-color: #D45379;
                border-color: #982FBD;
            }
            QPushButton:pressed {
                background-color: #AC3AA7;
                border-color: #982FBD;
            }
        """)
        confirm_button.setFont(QFont('Calibri Bold', 16))
        confirm_button.setFixedSize(270, 50)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(confirm_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)


        self.setLayout(layout)

    def get_deletion_type(self):
        return self.deletion_type_combo.currentText()
    
class ErrorDialog(QDialog):
    def __init__(self, title, text):
        super().__init__()
        self.setWindowTitle(title)
        self.setFixedSize(400, 160)
        apply_style(self, "dark")
        self.setWindowIcon(QIcon(resource_path('resources/error.ico')))
        self.setStyleSheet('background-color: #111111;')
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout()

        # Number of files to delete
        label = QLabel(f"{text}")
        label.setFont(QFont('Segoe UI', 12))
        label.setStyleSheet('color: white;')
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        space_above_separator = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed)
        layout.addItem(space_above_separator)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Plain)
        separator.setStyleSheet("background-color: #932CC3;")  # #932CC3
        separator.setMinimumHeight(4)
        layout.addWidget(separator)
        layout.addStretch()


        space_below_separator = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed)
        #layout.addItem(space_below_separator)

        # Confirm button
        confirm_button = QPushButton("Okay")
        confirm_button.clicked.connect(self.accept)  # Close dialog on confirm
        confirm_button.setStyleSheet("""
            QPushButton {
                background-color: #AC3AA7;
                border: 3px solid #982FBD;
                border-radius: 10px;
                color: black;
            }
            QPushButton:hover {
                background-color: #D45379;
                border-color: #982FBD;
            }
            QPushButton:pressed {
                background-color: #AC3AA7;
                border-color: #982FBD;
            }
        """)
        confirm_button.setFont(QFont('Calibri Bold', 16))
        confirm_button.setFixedSize(220, 30)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(confirm_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)
        layout.addStretch()

        self.setLayout(layout)

class SuccessDialog(QDialog):
    def __init__(self, title, text):
        super().__init__()
        self.setWindowTitle(title)
        self.setFixedSize(400, 160)
        apply_style(self, "dark")
        self.setWindowIcon(QIcon(resource_path('resources/success.ico')))
        self.setStyleSheet('background-color: #111111;')
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout()

        # Number of files to delete
        label = QLabel(f"{text}")
        label.setFont(QFont('Segoe UI', 12))
        label.setStyleSheet('color: white;')
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        space_above_separator = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed)
        layout.addItem(space_above_separator)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Plain)
        separator.setStyleSheet("background-color: #932CC3;")  # #932CC3
        separator.setMinimumHeight(4)
        layout.addWidget(separator)
        layout.addStretch()


        space_below_separator = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed)
        #layout.addItem(space_below_separator)

        # Confirm button
        confirm_button = QPushButton("Okay")
        confirm_button.clicked.connect(self.accept)  # Close dialog on confirm
        confirm_button.setStyleSheet("""
            QPushButton {
                background-color: #AC3AA7;
                border: 3px solid #982FBD;
                border-radius: 10px;
                color: black;
            }
            QPushButton:hover {
                background-color: #D45379;
                border-color: #982FBD;
            }
            QPushButton:pressed {
                background-color: #AC3AA7;
                border-color: #982FBD;
            }
        """)
        confirm_button.setFont(QFont('Calibri Bold', 16))
        confirm_button.setFixedSize(220, 30)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(confirm_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)
        layout.addStretch()

        self.setLayout(layout)


class ComparisonWindowVideo(QMainWindow):
    def __init__(self, comparison_results):
        super().__init__()

        self.setWindowTitle('Review Video Duplicates')
        self.setFixedSize(1000, 900)
        self.setStyleSheet('background-color: #111111;')
        self.setWindowIcon(QIcon(resource_path('resources/IconOnly.ico')))
        apply_style(self, "dark")

        self.default_pixmap = QPixmap(resource_path('resources/nopreview.png'))

        self.button_font = QFont('Calibri Bold', 16)

        # Main layout for the entire window
        self.main_layout = QVBoxLayout()

        # Titles layout
        titles_widget = QWidget()
        titles_layout = QHBoxLayout(titles_widget)

        # Load icons
        keep_icon = QPixmap('resources/keep.png').scaled(35, 35, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        delete_icon = QPixmap('resources/delete.png').scaled(35, 35, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        to_keep_icon = QLabel()
        to_keep_icon.setPixmap(keep_icon)
        to_keep_icon.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        to_delete_icon = QLabel()
        to_delete_icon.setPixmap(delete_icon)
        to_delete_icon.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        to_keep_label = QLabel("TO KEEP")
        to_delete_label = QLabel("TO BE DELETED")

        to_keep_label.setFont(QFont('Segoe UI', 20))
        to_delete_label.setFont(QFont('Segoe UI', 20))

        to_keep_label.setStyleSheet('color: white;')
        to_delete_label.setStyleSheet('color: white;')

        to_keep_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        to_delete_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        titles_layout.addWidget(to_keep_icon)
        titles_layout.addWidget(to_keep_label)
        titles_layout.addStretch()
        titles_layout.addWidget(to_delete_label)
        titles_layout.addWidget(to_delete_icon)

        self.main_layout.addWidget(titles_widget)

        # Scroll area for viewing duplicates
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True) ##932CC3
        self.scroll_area.setStyleSheet("""
            QScrollBar:vertical {
                border: none;
                background-color: #2d2d2d;  /* Dark background color */
                width: 10px;  /* Adjust the width of the scrollbar */
                margin: 0px 0px 0px 0px;
            }

            QScrollBar::handle:vertical {
                background-color: #932CC3;  /* Lighter gray for the handle */
                min-height: 30px;  /* Minimum height for the handle */
                border-radius: 5px;  /* Rounded corners for the handle */
            }

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;  /* Remove arrows (if you want) */
                height: 0px;  /* Set height to 0 to hide arrows */
            }

            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;  /* Background for pages (if you want to remove) */
            }
            
            QScrollArea {
                border: 2px solid #932CC3;                           
            }
        """)

        # Widget to hold all duplicate comparisons
        self.container_widget = QWidget()
        self.scroll_area.setWidget(self.container_widget)

        # Layout to arrange the duplicate comparisons vertically
        self.layout = QVBoxLayout(self.container_widget)

        self.main_layout.addWidget(self.scroll_area)

        # Progress bar for loading widgets
        self.progress_bar_comp = QProgressBar(self)
        self.progress_bar_comp.setValue(0)
        self.progress_bar_comp.setTextVisible(True)  # Show text inside the progress bar
        self.progress_bar_comp.setFormat("Loading Duplicates... %p%")  # Custom text format inside the progress bar
        self.progress_bar_comp.setAlignment(Qt.AlignCenter)  # Align text to center

        # Style the progress bar
        self.progress_bar_comp.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;  /* Align text to center */
                background-color: white;
                color: black;  /* Text color inside the progress bar */
            }
            QProgressBar::chunk {
                background-color: #AA39A9;  /* Change the progress color */
                width: 20px;
            }
        """)
        self.main_layout.addWidget(self.progress_bar_comp)


        # Progress bar for deleting
        self.delete_progress_bar = QProgressBar(self)
        self.delete_progress_bar.setValue(0)
        self.delete_progress_bar.setTextVisible(True)  # Show text inside the progress bar
        self.delete_progress_bar.setFormat("Deleting Duplicates... %p%")  # Custom text format inside the progress bar
        self.delete_progress_bar.setAlignment(Qt.AlignCenter)  # Align text to center
        self.delete_progress_bar.hide()

        # Style the progress bar
        self.delete_progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;  /* Align text to center */
                background-color: white;
                color: black;  /* Text color inside the progress bar */
            }
            QProgressBar::chunk {
                background-color: #AA39A9;  /* Change the progress color */
                width: 20px;
            }
        """)
        self.main_layout.addWidget(self.delete_progress_bar)

        # Store references to checkboxes and associated paths
        self.checkboxes = {}
        self.comparison_results = comparison_results
        self.current_index = 0

        # Timer for incremental loading
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_next_batch)
        self.timer.start(10)  # Adjust the interval as needed

        # Delete button, initially hidden
        self.delete_button = QPushButton('Review Deletion', self)
        self.delete_button.clicked.connect(self.show_deletion_dialog)
        self.delete_button.setStyleSheet("""
            QPushButton {
                background-color: #AC3AA7;
                border: 3px solid #982FBD;
                border-radius: 10px;
                color: black;
            }
            QPushButton:hover {
                background-color: #D45379;
                border-color: #982FBD;
            }
            QPushButton:pressed {
                background-color: #AC3AA7;
                border-color: #982FBD;
            }
        """)
        self.delete_button.setFixedSize(240,45)
        self.delete_button.setFont(self.button_font)
        self.delete_button.hide()  # Start hidden

        button_layout = QHBoxLayout()
        button_layout.addStretch()  # Add stretchable space to the left
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()  # Add stretchable space to the right

        self.main_layout.addLayout(button_layout)

        # Initialize the batch size
        self.batch_size = 8  # Number of items to load per batch

        central_widget = QWidget()
        central_widget.setLayout(self.main_layout)
        self.setCentralWidget(central_widget)

    def load_next_batch(self):
        """Load the next batch of comparison widgets."""
        for _ in range(self.batch_size):
            if self.current_index >= len(self.comparison_results):
                self.timer.stop()
                # Hide progress bar and show delete button when done
                self.progress_bar_comp.hide()
                self.update_delete_button_text()
                self.delete_button.show()
                return

            to_keep, to_delete = self.comparison_results[self.current_index]
            self.create_comparison_widget(to_keep, to_delete)
            self.current_index += 1

            # Update progress bar
            self.progress_bar_comp.setValue(int((self.current_index / len(self.comparison_results)) * 100))

    def create_comparison_widget(self, to_keep, to_delete):
        """Create and add widgets based on the provided data."""
        to_keep_path, to_keep_name, to_keep_runtime, to_keep_resolution, to_keep_preview, to_keep_folder = to_keep
        to_delete_path, to_delete_name, to_delete_runtime, to_delete_resolution, to_delete_preview, to_delete_folder = to_delete

        # Truncate names if too long
        to_keep_name = truncate_name(to_keep_name)
        to_delete_name = truncate_name(to_delete_name)

        comparison_widget = QWidget()
        comparison_layout = QVBoxLayout(comparison_widget)
        comparison_layout.setSpacing(0)

        to_keep_resolution_str = f"{to_keep_resolution[0]}x{to_keep_resolution[1]}"
        to_delete_resolution_str = f"{to_delete_resolution[0]}x{to_delete_resolution[1]}"

        # Horizontal layout for filenames and resolutions
        filenames_widget = QWidget()
        filenames_layout = QHBoxLayout(filenames_widget)
        filenames_layout.setSpacing(10)

        to_keep_name_label = QLabel(f"NAME: {to_keep_name}\nDURATION: {to_keep_runtime}\nRESOLUTION: {to_keep_resolution_str}\nLOCATION: {to_keep_folder}")
        to_keep_name_label.setAlignment(Qt.AlignLeft)
        to_keep_name_label.setFont(QFont('Segoe UI', 10))
        to_keep_name_label.setStyleSheet("color: green; font-weight: bold;")

        to_delete_name_label = QLabel(f"NAME: {to_delete_name}\nDURATION: {to_delete_runtime}\nRESOLUTION: {to_delete_resolution_str}\nLOCATION: {to_delete_folder}")
        to_delete_name_label.setAlignment(Qt.AlignRight)
        to_delete_name_label.setFont(QFont('Segoe UI', 10))
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
        to_keep_pixmap = QPixmap(to_keep_preview)
        if to_keep_pixmap.isNull():
            to_keep_pixmap = self.default_pixmap.scaled(370,500,Qt.KeepAspectRatio)
        to_keep_label.setPixmap(to_keep_pixmap.scaled(370, 500, Qt.KeepAspectRatio))

        to_delete_label = QLabel()
        to_delete_pixmap = QPixmap(to_delete_preview)
        if to_delete_pixmap.isNull():
            to_delete_pixmap = self.default_pixmap.scaled(370,500,Qt.KeepAspectRatio)
        to_delete_label.setPixmap(to_delete_pixmap.scaled(370, 500, Qt.KeepAspectRatio))

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

        delete_checkbox = QCheckBox("Mark For Deletion")
        delete_checkbox.setStyleSheet('color: white;')
        delete_checkbox.setFont(QFont('Segoe UI', 14))
        delete_checkbox.setChecked(True)
        delete_checkbox.setStyleSheet("""
            QCheckBox {
                color: white;
                font-size: 14pt; /* Font size */
            }
            QCheckBox::indicator {
                width: 18px; /* Width of the checkbox */
                height: 18px; /* Height of the checkbox */
            }
            QCheckBox::indicator:checked {
                background-color: #932CC3; /* Custom color for checked state */
                border: 2px solid white; /* Border color and size */
            }
            QCheckBox::indicator:unchecked {
                background-color: #333333; /* Custom color for unchecked state */
                border: 2px solid white; /* Border color and size */
            }
        """)

        # Connect state change signal to update function
        delete_checkbox.stateChanged.connect(self.update_delete_button_text)

        checkbox_layout.addWidget(delete_checkbox)

        checkbox_layout.addStretch()
        comparison_layout.addLayout(checkbox_layout)

        self.checkboxes[delete_checkbox] = (to_keep_path, to_delete_path)

        # Add space between the images and the separator
        space_above_separator = QSpacerItem(20, 30, QSizePolicy.Minimum, QSizePolicy.Fixed)
        comparison_layout.addItem(space_above_separator)

        # Separator
        if self.current_index < len(self.comparison_results) - 1:
            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setFrameShadow(QFrame.Plain)
            separator.setStyleSheet("background-color: #932CC3;") ##932CC3
            separator.setMinimumHeight(4)
            comparison_layout.addWidget(separator)

        self.layout.addWidget(comparison_widget)

        # Instead of addStretch() here, use QSpacerItem to avoid excessive space
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        comparison_layout.addItem(spacer)
    
    def update_delete_button_text(self):
        # Count the checked checkboxes
        marked_for_deletion = sum(checkbox.isChecked() for checkbox in self.checkboxes)
        # Update the button text
        self.delete_button.setText(f'Review Deletion ({marked_for_deletion})')

    def get_video_frame_preview(self, video_path):
        """
        Extract a frame from the middle of the video to use as a preview.
        """
        frame_count = get_frame_count(video_path)
        middle_frame = frame_count // 2
        cap = VideoCapture(video_path)
        cap.set(CAP_PROP_POS_FRAMES, middle_frame)
        ret, frame = cap.read()
        cap.release()

        if ret:
            frame_rgb = cvtColor(frame, COLOR_BGR2RGB)
            return convert_frame_to_pixmap(frame_rgb)
        else:
            return QPixmap()  # Return empty pixmap if failed


    def show_deletion_dialog(self):
        num_files = len([checkbox for checkbox in self.checkboxes if checkbox.isChecked()])
        if num_files == 0:
            error_dialog = ErrorDialog('Error', 'Whoops!\nSeems like you forgot to mark any files for deletion.')
            error_dialog.exec_()
            return
        
        dialog = DeletionConfirmationDialog(num_files)
        if dialog.exec_() == QDialog.Accepted:
            self.delete_progress_bar.setVisible(True)
            self.delete_button.setVisible(False)
            deletion_type = dialog.get_deletion_type()
            self.start_deletion(deletion_type)

    def start_deletion(self, deletion_type):
        self.deletion_worker = DeletionWorker(self.checkboxes, deletion_type)
        self.deletion_worker.progress_update.connect(self.update_progress_bar)
        self.deletion_worker.deletion_complete.connect(self.on_deletion_complete)
        self.deletion_worker.start()

    def update_progress_bar(self, value):
        self.delete_progress_bar.setValue(value)

    def on_deletion_complete(self):
        self.delete_progress_bar.setVisible(False)
        success_delete_dialog = SuccessDialog('Deletion Complete!', f'Woohoo!\nSuccessfully deleted the marked duplicates!')
        success_delete_dialog.exec_()
        self.close()

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
            duplicates = find_video_duplicates(self.folder_path, self.update_finding_progress)
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
            to_keep = (vid1_path, vid1_name, vid1_runtime, vid1_resolution, self.get_video_frame_preview(vid1_path), vid1_folder)
            to_delete = (vid2_path, vid2_name, vid2_runtime, vid2_resolution, self.get_video_frame_preview(vid2_path), vid2_folder)
        elif vid1_resolution[0] * vid1_resolution[1] < vid2_resolution[0] * vid2_resolution[1]:
            to_keep = (vid2_path, vid2_name, vid2_runtime, vid2_resolution, self.get_video_frame_preview(vid2_path), vid2_folder)
            to_delete = (vid1_path, vid1_name, vid1_runtime, vid1_resolution, self.get_video_frame_preview(vid1_path), vid1_folder)
        else:
            # If resolutions are equal, use name length and alphabetical order
            if len(vid1_name) < len(vid2_name) or (len(vid1_name) == len(vid2_name) and vid1_name < vid2_name):
                to_keep = (vid1_path, vid1_name, vid1_runtime, vid1_resolution, self.get_video_frame_preview(vid1_path), vid1_folder)
                to_delete = (vid2_path, vid2_name, vid2_runtime, vid2_resolution, self.get_video_frame_preview(vid2_path), vid2_folder)
            else:
                to_keep = (vid2_path, vid2_name, vid2_runtime, vid2_resolution, self.get_video_frame_preview(vid2_path), vid2_folder)
                to_delete = (vid1_path, vid1_name, vid1_runtime, vid1_resolution, self.get_video_frame_preview(vid1_path), vid1_folder)

        return (to_keep, to_delete)

    def get_video_frame_preview(self, video_path):
        """
        Extract a frame from the middle of the video to use as a preview.
        """
        frame_count = get_frame_count(video_path)
        middle_frame = frame_count // 2
        cap = VideoCapture(video_path)
        cap.set(CAP_PROP_POS_FRAMES, middle_frame)
        ret, frame = cap.read()
        cap.release()

        if ret:
            frame_rgb = cvtColor(frame, COLOR_BGR2RGB)
            return convert_frame_to_pixmap(frame_rgb)
        else:
            return QPixmap()  # Return empty pixmap if failed
        
def shred_file(file_path, passes=1):
    """
    Shred a file by overwriting it with random data for a specified number of passes.
    """
    try:
        with open(file_path, "r+b") as f:
            length = os.path.getsize(file_path)
            for _ in range(passes):
                f.seek(0)
                f.write(bytearray(getrandbits(8) for _ in range(length)))
        os.remove(file_path)
        print(f"File shredded: {file_path}")
    except Exception as e:
        print(f"Error shredding file {file_path}: {e}")

class DeletionWorker(QThread):
    progress_update = pyqtSignal(int)
    deletion_complete = pyqtSignal()

    def __init__(self, checkboxes, deletion_type):
        super().__init__()
        self.checkboxes = checkboxes
        self.deletion_type = deletion_type

    def run(self):
        total_files = len([checkbox for checkbox in self.checkboxes if checkbox.isChecked()])
        deleted_count = 0

        for checkbox, (to_keep_path, to_delete_path) in self.checkboxes.items():
            if checkbox.isChecked():
                try:
                    if self.deletion_type == "Normal Deletion":
                        os.remove(to_delete_path)
                    elif "Shred" in self.deletion_type:
                        if "1 Pass" in self.deletion_type:
                            shred_file(to_delete_path, passes=1)
                        elif "7 Passes" in self.deletion_type:
                            shred_file(to_delete_path, passes=7)
                        elif "15 Passes" in self.deletion_type:
                            shred_file(to_delete_path, passes=15)
                except Exception as e:
                    print(f"Error deleting file {to_delete_path}: {e}")
                deleted_count += 1
                self.progress_update.emit(int((deleted_count / total_files) * 100))

        self.deletion_complete.emit()
        

def main():
    app = QApplication(sys.argv)
    window = DuplicateImageFinder()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()