from PySide6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QPushButton, QMessageBox, QDialog, QTabWidget, QHBoxLayout
from PySide6.QtGui import QKeyEvent
from PySide6.QtCore import QTimer, Qt
import cv2
import os
import datetime
from src import EmotionAnalyzer, FrameProcessor, DatabaseManager
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

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
        self.trend_button = QPushButton("Show Trends", self)
        layout.addWidget(self.capture_button)
        layout.addWidget(self.accept_button)
        layout.addWidget(self.discard_button)
        layout.addWidget(self.trend_button)

        self.accept_button.setEnabled(False)
        self.discard_button.setEnabled(False)

        self.capture_button.clicked.connect(self.capture_image)
        self.accept_button.clicked.connect(self.accept_image)
        self.discard_button.clicked.connect(self.discard_image)
        self.trend_button.clicked.connect(self.show_trends_dialog)

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

    def show_trends_dialog(self):
        self.trends_window = QDialog(self)
        self.trends_window.setWindowTitle("Emotion Trends")
        dialog_layout = QVBoxLayout(self.trends_window)

        self.tabs = QTabWidget(self.trends_window)
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)

        happy_tab = QWidget()
        happy_layout = QVBoxLayout()
        button_layout = QHBoxLayout()

        day_button = QPushButton("Day")
        week_button = QPushButton("Week")
        month_button = QPushButton("Month")
        year_button = QPushButton("Year")

        day_button.clicked.connect(self.show_happy_trend_day)
        week_button.clicked.connect(self.show_happy_trend_week)
        month_button.clicked.connect(self.show_happy_trend_month)
        year_button.clicked.connect(self.show_happy_trend_year)

        button_layout.addWidget(day_button)
        button_layout.addWidget(week_button)
        button_layout.addWidget(month_button)
        button_layout.addWidget(year_button)

        happy_layout.addLayout(button_layout)
        happy_layout.addWidget(self.canvas)
        happy_tab.setLayout(happy_layout)

        self.tabs.addTab(happy_tab, "Happy Emotions Count")

        dialog_layout.addWidget(self.tabs)

        self.trends_window.setLayout(dialog_layout)
        self.trends_window.exec()

    def show_happy_trend_day(self):
        today = datetime.datetime.now().date()
        start_of_today = datetime.datetime.combine(today, datetime.time.min)
        end_of_today = datetime.datetime.combine(today, datetime.time.max)

        happy_counts = self.db_manager.get_happy_emotion_counts(start_of_today, end_of_today)

        counts = [0] * 24  # Initialize counts for each hour of the day

        for timestamp_str, count in happy_counts:
            timestamp = datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            counts[timestamp.hour] += count

        hours = list(range(24))
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.plot(hours, counts, marker='o', linestyle='-')
        ax.set_title('Happy Emotions Over the Hours of Today')
        ax.set_xlabel('Hour of the Day')
        ax.set_ylabel('Count of Happy Emotions')
        ax.set_xticks(range(24))
        ax.grid(True)
        self.canvas.draw()

    def show_happy_trend_week(self):
        today = datetime.datetime.now().date()
        start_of_week = today - datetime.timedelta(days=today.weekday())  # Monday of the current week
        end_of_week = start_of_week + datetime.timedelta(days=4)  # Friday of the current week

        happy_counts = self.db_manager.get_happy_emotion_counts_for_week(start_of_week, end_of_week)

        week_counts = {day: [0] * 24 for day in range(5)}  # 5 days, 24 hours each

        for date_str, hour_str, count in happy_counts:
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            hour = int(hour_str)
            if start_of_week <= date <= end_of_week:
                if 6 <= hour <= 18:  # Filter for work hours
                    day_index = (date - start_of_week).days
                    week_counts[day_index][hour] += count

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        for day_index, day_counts in week_counts.items():
            hours = list(range(6, 19))  # Work hours 06:00 to 18:00
            counts = day_counts[6:19]
            ax.plot(hours, counts, marker='o', linestyle='-', label=f'Day {day_index + 1} (Monday={1})')

        ax.set_title('Happy Emotions Over the Workweek')
        ax.set_xlabel('Hour of the Day')
        ax.set_ylabel('Count of Happy Emotions')
        ax.set_xticks(range(6, 19))
        ax.grid(True)
        ax.legend()
        self.canvas.draw()

    def show_happy_trend_month(self):
        today = datetime.datetime.now().date()
        start_of_month = today.replace(day=1)
        end_of_month = (start_of_month + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)

        happy_counts = self.db_manager.get_happy_emotion_counts(start_of_month, end_of_month)

        day_counts = [0] * (end_of_month.day + 1)

        for timestamp_str, count in happy_counts:
            timestamp = datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            day_counts[timestamp.day] += count

        days = list(range(1, end_of_month.day + 1))
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.plot(days, day_counts[1:], marker='o', linestyle='-')
        ax.set_title('Happy Emotions Over the Days of the Month')
        ax.set_xlabel('Day of the Month')
        ax.set_ylabel('Count of Happy Emotions')
        ax.set_xticks(days)
        ax.grid(True)
        self.canvas.draw()

    def show_happy_trend_year(self):
        today = datetime.datetime.now().date()
        start_of_year = today.replace(month=1, day=1)
        end_of_year = today.replace(month=12, day=31)

        happy_counts = self.db_manager.get_happy_emotion_counts(start_of_year, end_of_year)

        month_counts = [0] * 13  # Initialize counts for each month

        for timestamp_str, count in happy_counts:
            timestamp = datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            month_counts[timestamp.month] += count

        months = list(range(1, 13))
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.plot(months, month_counts[1:], marker='o', linestyle='-')
        ax.set_title('Happy Emotions Over the Months of the Year')
        ax.set_xlabel('Month of the Year')
        ax.set_ylabel('Count of Happy Emotions')
        ax.set_xticks(months)
        ax.grid(True)
        self.canvas.draw()

    def update_button_states(self, *, accept_button, discard_button, capture_button):
        self.accept_button.setEnabled(accept_button)
        self.discard_button.setEnabled(discard_button)
        self.capture_button.setEnabled(capture_button)
