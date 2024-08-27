import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QFileDialog, QMessageBox, QScrollArea, QVBoxLayout, QWidget, QHBoxLayout, QFrame, QSpacerItem, QSizePolicy
)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt
from duplicate_detector import find_duplicates, get_image_resolution  # Import the duplicate detection module
import os


## TODO: Switch two images if you want the other one deleted instead
## TODO: Video support?
## TODO: ICONS next to important stuff
## TODO: FONTS
## TODO: FILE SHREDDING TOGGLE
## TODO: DISPLAY IMAGE SIZE
## TODO: DELETE FUNCTIONALITY

class DuplicateImageFinder(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set the title and locked size of the window
        self.setWindowTitle('Duplicate Image Finder')
        self.setFixedSize(900, 900)  # Increase the window size to accommodate larger scroll area

        # Logo
        self.logo_label = QLabel(self)
        self.logo_pixmap = QPixmap('path/to/your/logo.png')  # Replace with the path to your logo
        self.logo_label.setPixmap(self.logo_pixmap.scaled(150, 150, Qt.KeepAspectRatio))
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setFixedSize(150, 150)
        self.logo_label.move(375, 50)  # Center the logo at the top

        # Button to choose folder
        self.folder_button = QPushButton('Choose Folder', self)
        self.folder_button.setFixedSize(150, 40)
        self.folder_button.move(375, 250)  # Center the button below the logo
        self.folder_button.clicked.connect(self.choose_folder)

        # Label to show the chosen folder path
        self.folder_label = QLabel('No folder chosen', self)
        self.folder_label.setFixedSize(400, 40)
        self.folder_label.setAlignment(Qt.AlignCenter)
        self.folder_label.move(250, 320)  # Center this label below the button

        # Start button
        self.start_button = QPushButton('Start', self)
        self.start_button.setFixedSize(150, 40)
        self.start_button.move(375, 400)  # Center the button below the folder label
        self.start_button.clicked.connect(self.start_processing)

        # Store the selected folder path
        self.selected_folder = None

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select Folder')
        if folder:
            self.selected_folder = folder
            self.folder_label.setText(f'Selected Folder: {folder}')

    def start_processing(self):
        if self.selected_folder:
            duplicates = find_duplicates(self.selected_folder)
            if duplicates:
                self.show_comparison_window(duplicates)
            else:
                QMessageBox.information(self, 'No Duplicates Found', 'No duplicate images found in the selected folder.')
        else:
            QMessageBox.warning(self, 'No Folder Selected', 'Please choose a folder first!')

    def show_comparison_window(self, duplicates):
        self.comparison_window = ComparisonWindow(duplicates)
        self.comparison_window.show()


class ComparisonWindow(QMainWindow):
    def __init__(self, duplicates):
        super().__init__()

        self.setWindowTitle('Review Duplicates')
        self.setFixedSize(900, 900)  # Increase window size

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

        # Widget to hold all duplicate comparisons
        container_widget = QWidget()
        scroll_area.setWidget(container_widget)

        # Layout to arrange the duplicate comparisons vertically
        layout = QVBoxLayout(container_widget)

        # Define the maximum width for each image
        max_image_width = 370
        max_image_height = 500

        for img1_path, img2_path, img1_hash, img2_hash in duplicates:
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
            

            if img1_resolution >= img2_resolution:
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

            # Separator
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


    def delete_duplicates(self):
        # Here you'd implement the deletion logic
        QMessageBox.information(self, 'Delete Duplicates', 'Duplicates have been deleted!')
        self.close()


def main():
    app = QApplication(sys.argv)
    window = DuplicateImageFinder()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()