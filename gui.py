import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QFileDialog, QMessageBox, QScrollArea, QVBoxLayout, QWidget, QHBoxLayout, QFrame
)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt
from duplicate_detector import find_duplicates  # Import the duplicate detection module
import os


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

        to_delete_label = QLabel("To Be Deleted")
        to_keep_label = QLabel("To Keep")

        to_delete_label.setFont(QFont('Palatino Linotype', 20))
        to_keep_label.setFont(QFont('Palatino Linotype', 20))

        to_delete_label.setAlignment(Qt.AlignCenter)
        to_keep_label.setAlignment(Qt.AlignCenter)

        titles_layout.addWidget(to_keep_label)
        titles_layout.addStretch()  # Add some space between the titles
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
        max_image_width = 370  # Slightly reduced to prevent horizontal scrolling
        max_image_height = 500  # Adjusted for best viewing experience

        for img1_path, img2_path in duplicates:
            comparison_widget = QWidget()
            comparison_layout = QVBoxLayout(comparison_widget)
            comparison_layout.setSpacing(0)  # Remove space between widgets

            # Horizontal layout for filenames
            filenames_widget = QWidget()
            filenames_layout = QHBoxLayout(filenames_widget)
            filenames_layout.setSpacing(0)  # Remove space between filenames and images

            img1_name = QLabel(os.path.basename(img1_path))
            img1_name.setAlignment(Qt.AlignHCenter)
            img1_name.setContentsMargins(0, 0, 0, 0)
            img1_name.setFixedSize(img1_name.sizeHint())  # Ensures the QLabel is tightly sized
            img1_name.setStyleSheet("border: none;")  # Removes any border that might add extra space
            img2_name = QLabel(os.path.basename(img2_path))
            img2_name.setAlignment(Qt.AlignHCenter)
            img2_name.setContentsMargins(0, 0, 0, 0)
            img2_name.setFixedSize(img2_name.sizeHint())  # Ensures the QLabel is tightly sized
            img2_name.setStyleSheet("border: none;")  # Removes any border that might add extra space
            filenames_layout.addWidget(img1_name)
            filenames_layout.addStretch()
            filenames_layout.addWidget(img2_name)

            comparison_layout.addWidget(filenames_widget)

            # Horizontal layout for images
            images_widget = QWidget()
            images_layout = QHBoxLayout(images_widget)
            images_layout.setSpacing(0)  # Remove space between images

            img1_label = QLabel()
            img1_pixmap = QPixmap(img1_path)
            img1_label.setPixmap(img1_pixmap.scaled(max_image_width, max_image_height, Qt.KeepAspectRatio))

            img2_label = QLabel()
            img2_pixmap = QPixmap(img2_path)
            img2_label.setPixmap(img2_pixmap.scaled(max_image_width, max_image_height, Qt.KeepAspectRatio))

            images_layout.addStretch()
            images_layout.addWidget(img1_label)
            images_layout.addStretch()
            images_layout.addWidget(img2_label)
            images_layout.addStretch()

            comparison_layout.addWidget(images_widget)
            comparison_layout.addStretch()

            # Separator
            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setFrameShadow(QFrame.Sunken)
            separator.setStyleSheet("background-color: black; height: 3px;")
            comparison_layout.addWidget(separator)
            comparison_layout.addStretch()
            layout.addWidget(comparison_widget)

        main_layout.addWidget(scroll_area)

        # Delete button at the bottom
        delete_button = QPushButton('Delete Duplicates', self)
        delete_button.clicked.connect(self.delete_duplicates)
        main_layout.addWidget(delete_button)

        # Set scroll area
        scroll_area.setGeometry(50, 50, 800, 800)  # Increased the size of the scroll area
        scroll_area.move(50, 50)  # Position the scroll area within the window

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