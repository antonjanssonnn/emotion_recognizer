import sys
from PySide6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QPushButton
from PySide6.QtGui import QKeyEvent
from PySide6.QtCore import QTimer, Qt
import cv2
import os
import datetime
from src import EmotionAnalyzer, FrameProcessor, DatabaseManager


class EmotionApp(QWidget):
    WINDOW_WIDTH_RATIO = 0.8
    WINDOW_HEIGHT_RATIO = 0.8
    IMAGE_DIRECTORY = 'captured_images'

    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.emotion_analyzer = EmotionAnalyzer()
        self.frame_processor = FrameProcessor()
        self.live_video = True
        self.current_frame = None
        self.current_results = None
        self.ensure_directory_exists(self.IMAGE_DIRECTORY)
        self.initUI()

    def ensure_directory_exists(self, directory):
        """Ensures the specified directory exists."""
        if not os.path.exists(directory):
            os.makedirs(directory)

    def initUI(self):
        self.setWindowTitle('Emotion Recognizer')
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.image_label = QLabel(self)
        layout.addWidget(self.image_label)

        self.capture_button = QPushButton("Capture", self)
        self.accept_button = QPushButton("Accept", self)
        self.discard_button = QPushButton("Discard", self)
        layout.addWidget(self.capture_button)
        layout.addWidget(self.accept_button)
        layout.addWidget(self.discard_button)

        self.accept_button.setEnabled(False)
        self.discard_button.setEnabled(False)

        self.capture_button.clicked.connect(self.capture_image)
        self.accept_button.clicked.connect(self.accept_image)
        self.discard_button.clicked.connect(self.discard_image)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(20)

    def showEvent(self, event):
        super().showEvent(event)
        screen = QApplication.primaryScreen()
        screen_size = screen.size()
        width, height = screen_size.width(), screen_size.height()
        window_width = width * self.WINDOW_WIDTH_RATIO
        window_height = height * self.WINDOW_HEIGHT_RATIO
        self.resize(window_width, window_height)
        self.move((width - window_width) // 2, (height - window_height) // 2)
        self.setFixedSize(window_width, window_height)

    def update_frame(self):
        if self.live_video:
            frame = self.frame_processor.capture_frame()
            if frame is not None:
                self.display_image(frame)

    def display_image(self, frame):
        self.frame_processor.display_image(self.image_label, frame)

    def closeEvent(self, event):
        print("Cleaning up resources...")
        self.frame_processor.release_resources()
        self.db_manager.close()
        event.accept()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Space:
            self.capture_image()
            print("Picture is captured!")
        elif event.key() == Qt.Key_R:
            self.live_video = True
            print("Resuming live feed...")
        elif event.key() == Qt.Key_Q:
            print("Exiting... Bye!")
            self.close()

    def capture_image(self):
        self.live_video = False
        frame = self.frame_processor.capture_frame()
        if frame is not None:
            results = self.emotion_analyzer.analyze_frame(frame)
            if results:
                annotated_frame = self.frame_processor.annotate_frame(frame, results)
                self.display_image(annotated_frame)
                self.current_frame = annotated_frame
                self.current_results = results
            else:
                self.display_image(frame)
                self.current_frame = frame
                self.current_results = None
            
            self.update_button_states(accept_button=True, discard_button=True, capture_button=False)
        else:
            print("No frame captured to process.")

    def accept_image(self):
        if self.current_results:
            self.save_image(self.current_frame)
            self.add_to_database(self.current_results)
        self.update_button_states(accept_button=False, discard_button=False, capture_button=True)
        self.live_video = True

    def discard_image(self):
        self.update_button_states(accept_button=False, discard_button=False, capture_button=True)
        self.live_video = True
        print("Image was discarded!")

    def save_image(self, frame):
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'captured_images/{timestamp}.png'
        cv2.imwrite(filename, frame)
        print(f"Image saved as {filename}")

    def add_to_database(self, results):
        for result in results:
            emotion = result[0]['dominant_emotion']
            age = result[0]['age']
            gender = result[0]['dominant_gender']
            self.db_manager.add_emotion(emotion, age, gender)
        print("Data added to database")

    def update_button_states(self, *, accept_button, discard_button, capture_button):
        self.accept_button.setEnabled(accept_button)
        self.discard_button.setEnabled(discard_button)
        self.capture_button.setEnabled(capture_button)
