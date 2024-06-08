import sys
from PySide6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QPushButton
from PySide6.QtGui import QScreen, QImage, QPixmap, QKeyEvent
from PySide6.QtCore import QTimer, Qt
import cv2
from emotion import EmotionAnalyzer
import datetime


class EmotionApp(QWidget):
    def __init__(self):
        super().__init__()
        self.emotion_analyzer = EmotionAnalyzer()
        self.live_video = True
        self.current_frame = None
        self.current_results = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Emotion Recognizer')
        # Setup layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Image display widget
        self.image_label = QLabel(self)
        layout.addWidget(self.image_label)

        # Capture, Accept, and Discard buttons
        self.capture_button = QPushButton("Capture", self)
        self.accept_button = QPushButton("Accept", self)
        self.discard_button = QPushButton("Discard", self)
        layout.addWidget(self.capture_button)
        layout.addWidget(self.accept_button)
        layout.addWidget(self.discard_button)

        # Disable Accept and Discard buttons initially
        self.accept_button.setEnabled(False)
        self.discard_button.setEnabled(False)

        # Connect buttons to their respective functions
        self.capture_button.clicked.connect(self.capture_image)
        self.accept_button.clicked.connect(self.accept_image)
        self.discard_button.clicked.connect(self.discard_image)

        # Timer for capturing images
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(20)  # Update every 20 ms

    def showEvent(self, event):
        super().showEvent(event)
        # Adjust window size based on screen size
        screen = QApplication.primaryScreen()
        screen_size = screen.size()
        width, height = screen_size.width(), screen_size.height()
        window_width = width * 0.8
        window_height = height * 0.8
        self.resize(window_width, window_height)
        self.move((width - window_width) // 2, (height - window_height) // 2)
        self.setFixedSize(window_width, window_height)

    def update_frame(self):
        if self.live_video:
            frame = self.emotion_analyzer.capture_frame()
            if frame is not None:
                self.display_image(frame)

    def display_image(self, frame):
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        q_img = QImage(image.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        scaled_pixmap = pixmap.scaled(self.image_label.width(), self.image_label.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled_pixmap)

    def closeEvent(self, event):
        print("Cleaning up resources...")
        self.emotion_analyzer.close()
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
        frame = self.emotion_analyzer.capture_frame()
        if frame is not None:
            results = self.emotion_analyzer.analyze_frame(frame)
            if results:  # If results are present, annotate the frame
                annotated_frame = self.annotate_frame(frame, results)
                self.display_image(annotated_frame)  # Display annotated frame in GUI
                self.current_frame = annotated_frame  # Save the current frame for later use
                self.current_results = results  # Save the current results for later use
            else:
                self.display_image(frame)  # Display unannotated frame if no faces detected
                self.current_frame = frame  # Save the current frame for later use
                self.current_results = None
            
            # Enable Accept and Discard buttons, disable Capture button
            self.update_button_states(accept_button=True,
                                      discard_button=True,
                                      capture_button=False,
                                     )
        else:
            print("No frame captured to process.")

    def accept_image(self):
        # Save the current frame and add data to the database if there are results
        if self.current_results:
            self.save_image(self.current_frame)
            self.add_to_database(self.current_results)
        # Disable Accept and Discard buttons, enable Capture button and resume live feed
        self.update_button_states(accept_button=False,
                                  discard_button=False,
                                  capture_button=True,
                                 )
        self.live_video = True

    def discard_image(self):
        # Disable Accept and Discard buttons, enable Capture button and resume live feed
        self.update_button_states(accept_button=False,
                                  discard_button=False,
                                  capture_button=True,
                                 )
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
            self.emotion_analyzer.cursor.execute('INSERT INTO emotions (emotion, age, gender) VALUES (?, ?, ?)', (emotion, str(age), gender))
            self.emotion_analyzer.conn.commit()
        print("Data added to database")

    def annotate_frame(self, frame, results):
        for result in results:
            region = result[0]['region']
            x, y, w, h = region['x'], region['y'], region['w'], region['h']

            # Draw the bounding box
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            emotion = result[0]['dominant_emotion']
            age = result[0]['age']
            gender = result[0]['dominant_gender']

            # Draw text for emotion, age, gender
            cv2.putText(frame, f'Age: {age}', (x, y + h + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            cv2.putText(frame, f'Emotion: {emotion}', (x, y + h + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            cv2.putText(frame, f'Gender: {gender}', (x, y + h + 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

            # Add emoji
            if emotion in self.emotion_analyzer.emotion_emoji_map:
                emoji_path = self.emotion_analyzer.emotion_emoji_map[emotion]
                frame = self.emotion_analyzer.add_emoji_to_frame(frame, emoji_path, (x, y - 50))

        return frame
    
    def update_button_states(self, *, accept_button, discard_button, capture_button):
        self.accept_button.setEnabled(accept_button)
        self.discard_button.setEnabled(discard_button)
        self.capture_button.setEnabled(capture_button)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = EmotionApp()
    ex.show()
    sys.exit(app.exec())
