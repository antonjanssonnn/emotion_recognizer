import sys
from PySide6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
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
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Emotion Recognizer')
        # Setup layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Image display widget
        self.image_label = QLabel(self)
        layout.addWidget(self.image_label)
        
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
            self.take_picture()
            print("Picture is captured!")
        elif event.key() == Qt.Key_R:  # Resume live video by pressing 'R'
            self.live_video = True
            print("Resuming live feed...")
        elif event.key() == Qt.Key_Q:
            print("Exiting... Bye!")
            self.close()

    def take_picture(self):
        self.live_video = False
        frame = self.emotion_analyzer.capture_frame()
        if frame is not None:
            results = self.emotion_analyzer.analyze_frame(frame)
            if results:  # If results are present, annotate the frame
                annotated_frame = self.annotate_frame(frame, results)
                self.display_image(annotated_frame)  # Display annotated frame in GUI
                self.save_image(annotated_frame)  # Save the annotated frame
            else:
                self.display_image(frame)  # Display unannotated frame if no faces detected
                self.save_image(frame)  # Save the unannotated frame
        else:
            print("No frame captured to process.")

    def save_image(self, frame):
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'captured_images/{timestamp}.png'
        cv2.imwrite(filename, frame)
        print(f"Image saved as {filename}")

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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = EmotionApp()
    ex.show()
    sys.exit(app.exec())
