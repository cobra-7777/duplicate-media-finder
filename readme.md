
# Copy Cleaner - Easy media deduplication

Copy Cleaner is a robust desktop application designed to help you efficiently locate and manage duplicate images and videos on your systems. With an intuitive graphical user interface (GUI) built using PyQt, this tool leverages advanced algorithms for identifying duplicates based on perceptual hashing, file resolution, and file properties. 

You can easily review duplicates side-by-side with visual previews (inspired by the classic Windows duplicate window), choose what files to delete, and choose between different deletion methods, including secure file shredding with multiple passes for enhanced privacy.



## Features of Copy Cleaner

- **Image and Video Duplicate Detection**: Supports both images and videos, using tailored P-Hashing algorithms to identify duplicates, even with different file resolutions. This app focuses mainly on finding exact duplicates, but will also mark images that are very very similar.

- **Blazing Fast**: With efficiency in mind, this app was created to be fast. On modern hardware, this app will search through about 30 gigabytes of content in about a minute (depending on content type and hardware specifications). It mainly utilizes your CPU to compute the hashes and compare the images.

- **Scalable**: Optimized for performance and responsiveness, handling large directories with thousands or hundreds of thousands of files while maintaining responsiveness and speed.

- **Intuitive User Interface**: With a dark and minimalistic UI, the app is easy and pleasant to use. Unlike many other apps with this functionality, this app presents a visual representation of the duplicates found, so that you can compare them and choose which ones you wanna delete.

- **No Duplicates Left Unsearched**: Copy Cleaner will search all files in your chosen directory, also those inside subfolders. It will even detect duplicates across folders different folders.

- **Privacy Above All**: Given the sensitive nature of your personal image and video files, this app was created with utmost privacy in mind.
    - No outbound or inbound internet connections are made. 
    - No images or image thumbnails  are stored anywhere - its all kept in memory.
    - Different deletion types, including secure file shredding up to 15 passes, to ensure your deleted content cannot be restored.
    - Open source and free - you're free to check the code.


## Usage

Simply download the latest release on the right hand side menu of this Github page, where it says "Releases". Extract the archive, and run the EXE file, and you're ready to go!

If you wish to run the code on your own, you are free to clone it and make your own EXE, or run it directly from your IDE or terminal. I will not be helping anyone do this. If you dont know how, use the EXE i am providing. 
    
## Screenshots

![App Screenshot](https://via.placeholder.com/468x300?text=App+Screenshot+Here)


## Tech Stack

- **Python**: Core application logic.

- **PyQt**: For building the user interface.

- **Pillow (PIL)**: Image processing.

- **OpenCV**: Video frame extraction and processing.

- **ImageHash**: Perceptual hashing for duplicate detection.


## Authors

- [@cobra7777](https://github.com/cobra-7777)


## Feedback

If you have any feedback, please feel free to open an issue/request/feedback on this page.

