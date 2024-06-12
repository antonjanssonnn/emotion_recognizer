import datetime
import os

import cv2
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src import DatabaseManager, EmotionAnalyzer, FrameProcessor


class EmotionApp(QWidget):
    WINDOW_WIDTH_RATIO = 0.8
    WINDOW_HEIGHT_RATIO = 0.8
    IMAGE_DIRECTORY = "captured_images"

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
        self.setWindowTitle("Emotion Recognizer")
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

            self.update_button_states(
                accept_button=True, discard_button=True, capture_button=False
            )
        else:
            print("No frame captured to process.")

    def accept_image(self):
        if self.current_results:
            self.save_image(self.current_frame)
            self.add_to_database(self.current_results)
        self.update_button_states(
            accept_button=False, discard_button=False, capture_button=True
        )
        self.live_video = True

    def discard_image(self):
        self.update_button_states(
            accept_button=False, discard_button=False, capture_button=True
        )
        self.live_video = True
        print("Image was discarded!")

    def save_image(self, frame):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"captured_images/{timestamp}.png"
        cv2.imwrite(filename, frame)
        print(f"Image saved as {filename}")

    def add_to_database(self, results):
        for result in results:
            emotion = result[0]["dominant_emotion"]
            age = result[0]["age"]
            gender = result[0]["dominant_gender"]
            self.db_manager.add_emotion(emotion, age, gender)
        print("Data added to database")

    def show_trends_dialog(self):
        self.trends_window = QDialog(self)
        self.trends_window.setWindowTitle("Emotion Trends")
        dialog_layout = QVBoxLayout(self.trends_window)

        self.tabs = QTabWidget(self.trends_window)
        self.happy_figure = plt.figure()
        self.happy_canvas = FigureCanvas(self.happy_figure)

        # Flags to track if the tabs have been viewed
        self.happy_tab_viewed = False
        self.emotion_tab_viewed = False

        # Happy Tab and Buttons
        happy_tab = QWidget()
        happy_layout = QVBoxLayout()
        happy_button_layout = QHBoxLayout()

        happy_day_button = QPushButton("Day")
        happy_week_button = QPushButton("Week")
        happy_month_button = QPushButton("Month")
        happy_year_button = QPushButton("Year")

        happy_day_button.clicked.connect(self.show_happy_trend_day)
        happy_week_button.clicked.connect(self.show_happy_trend_week)
        happy_month_button.clicked.connect(self.show_happy_trend_month)
        happy_year_button.clicked.connect(self.show_happy_trend_year)

        happy_button_layout.addWidget(happy_day_button)
        happy_button_layout.addWidget(happy_week_button)
        happy_button_layout.addWidget(happy_month_button)
        happy_button_layout.addWidget(happy_year_button)

        happy_layout.addLayout(happy_button_layout)
        happy_layout.addWidget(self.happy_canvas)
        happy_tab.setLayout(happy_layout)

        # Emotion Tabs and Buttons
        self.emotion_figure = plt.figure()
        self.emotion_canvas = FigureCanvas(self.emotion_figure)
        emotion_tab = QWidget()
        emotion_layout = QVBoxLayout()
        emotion_button_layout = QHBoxLayout()

        emotion_day_button = QPushButton("Day")
        emotion_week_button = QPushButton("Week")
        emotion_month_button = QPushButton("Month")
        emotion_year_button = QPushButton("Year")

        emotion_day_button.clicked.connect(self.show_emotion_trend_day)
        emotion_week_button.clicked.connect(self.show_emotion_trend_week)
        emotion_month_button.clicked.connect(self.show_emotion_trend_month)
        emotion_year_button.clicked.connect(self.show_emotion_trend_year)

        emotion_button_layout.addWidget(emotion_day_button)
        emotion_button_layout.addWidget(emotion_week_button)
        emotion_button_layout.addWidget(emotion_month_button)
        emotion_button_layout.addWidget(emotion_year_button)

        emotion_layout.addLayout(emotion_button_layout)
        emotion_layout.addWidget(
            self.emotion_canvas
        )  # Add the canvas to the emotion tab layout
        emotion_tab.setLayout(emotion_layout)

        self.tabs.addTab(happy_tab, "Happy Emotions Count")
        self.tabs.addTab(emotion_tab, "All Emotion Count")

        dialog_layout.addWidget(self.tabs)

        self.trends_window.setLayout(dialog_layout)

        # Show the default graph (e.g., Happy Emotions Over the Day)
        self.show_happy_trend_day()
        self.happy_tab_viewed = True

        # Connect tab change to method
        self.tabs.currentChanged.connect(self.on_tab_changed)

        self.trends_window.exec()

    def on_tab_changed(self, index):
        if index == 0 and not self.happy_tab_viewed:
            self.show_happy_trend_day()
            self.happy_tab_viewed = True
        elif index == 1 and not self.emotion_tab_viewed:
            self.show_emotion_trend_day()
            self.emotion_tab_viewed = True

    def show_emotion_trend_day(self):
        today = datetime.datetime.now().date()
        start_time = datetime.datetime.combine(today, datetime.time(6, 0))
        end_time = datetime.datetime.combine(today, datetime.time(18, 0))

        # Get emotion counts for the day
        emotion_counts = self.db_manager.get_emotion_counts(start_time, end_time)

        # Initialize a dictionary to hold the counts for each emotion and hour
        hours_in_day = 13  # 06:00 to 18:00
        emotions = set(
            [count[1] for count in emotion_counts]
        )  # Extract unique emotions
        emotion_data = {emotion: [0] * hours_in_day for emotion in emotions}

        # Fill the dictionary with the counts
        for timestamp_str, emotion, count in emotion_counts:
            timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            if 6 <= timestamp.hour <= 18:
                hour_index = timestamp.hour - 6  # Shift to 0-indexed hour starting at 6
                emotion_data[emotion][hour_index] += count

        # Prepare time labels for the x-axis
        times = [start_time + datetime.timedelta(hours=i) for i in range(hours_in_day)]

        # Use the helper function to plot the data
        self.plot_day_trend(
            self.emotion_figure,
            "Emotions Over the Day",
            "Hour of the Day",
            "Count of Emotions",
            emotion_data,
            times,
        )

    def show_emotion_trend_week(self):
        today = datetime.datetime.now().date()
        start_of_week = today - datetime.timedelta(
            days=today.weekday()
        )  # Monday of the current week
        start_time = datetime.datetime.combine(start_of_week, datetime.time(6, 0))
        end_time = datetime.datetime.combine(
            start_of_week + datetime.timedelta(days=4), datetime.time(18, 0)
        )

        # Get emotion counts for the entire week
        emotion_counts = self.db_manager.get_emotion_counts(start_time, end_time)

        # Initialize a dictionary to hold the counts for each emotion and day
        days_in_week = 5
        emotions = set(
            [count[1] for count in emotion_counts]
        )  # Extract unique emotions
        emotion_data = {emotion: [0] * days_in_week for emotion in emotions}

        # Fill the dictionary with the counts
        for timestamp_str, emotion, count in emotion_counts:
            timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            if 6 <= timestamp.hour <= 18:
                day_index = (timestamp.date() - start_of_week).days
                emotion_data[emotion][day_index] += count

        # Prepare date labels for the x-axis
        dates = [
            start_of_week + datetime.timedelta(days=i) for i in range(days_in_week)
        ]

        # Use the helper function to plot the data
        self.plot_week_trend(
            self.emotion_figure,
            "Emotions Over the Workweek",
            "Day of the Week",
            "Count of Emotions",
            emotion_data,
            dates,
        )

    def show_emotion_trend_month(self):
        today = datetime.datetime.now().date()
        start_of_month = today.replace(day=1)
        end_of_month = (start_of_month + datetime.timedelta(days=32)).replace(
            day=1
        ) - datetime.timedelta(days=1)

        # Get emotion counts for the entire month
        emotion_counts = self.db_manager.get_emotion_counts(
            start_of_month, end_of_month
        )

        # Initialize a dictionary to hold the counts for each emotion and day
        days_in_month = (end_of_month - start_of_month).days + 1
        emotions = set(
            [count[1] for count in emotion_counts]
        )  # Extract unique emotions
        emotion_data = {emotion: [0] * days_in_month for emotion in emotions}

        # Fill the dictionary with the counts
        for timestamp_str, emotion, count in emotion_counts:
            timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            day_index = (timestamp.date() - start_of_month).days
            emotion_data[emotion][day_index] += count

        # Prepare time labels for the x-axis
        times = [
            start_of_month + datetime.timedelta(days=i) for i in range(days_in_month)
        ]

        # Use the helper function to plot the data
        month_name = start_of_month.strftime("%B")
        self.plot_month_trend(
            self.emotion_figure,
            f"Emotions Over the Month {month_name}",
            "Date",
            "Count of Emotions",
            emotion_data,
            times,
        )

    def show_emotion_trend_year(self):
        today = datetime.datetime.now().date()
        start_of_year = today.replace(month=1, day=1)
        end_of_year = today.replace(month=12, day=31)

        # Get emotion counts for the entire year
        emotion_counts = self.db_manager.get_emotion_counts(start_of_year, end_of_year)

        # Initialize a dictionary to hold the counts for each emotion and month
        months_in_year = 12
        emotions = set(
            [count[1] for count in emotion_counts]
        )  # Extract unique emotions
        emotion_data = {emotion: [0] * months_in_year for emotion in emotions}

        # Fill the dictionary with the counts
        for timestamp_str, emotion, count in emotion_counts:
            timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            month_index = timestamp.month - 1
            emotion_data[emotion][month_index] += count

        # Prepare time labels for the x-axis
        times = [start_of_year.replace(month=i + 1) for i in range(months_in_year)]

        # Use the helper function to plot the data
        self.plot_year_trend(
            self.emotion_figure,
            "Emotions Over the Year",
            "Month",
            "Count of Emotions",
            emotion_data,
            times,
        )

    def show_happy_trend_day(self):
        today = datetime.datetime.now().date()
        start_of_today = datetime.datetime.combine(today, datetime.time(6, 0))
        end_of_today = datetime.datetime.combine(today, datetime.time(18, 0))

        happy_counts = self.db_manager.get_happy_emotion_counts(
            start_of_today, end_of_today
        )

        counts = [0] * 13  # Initialize counts for each work hour (6:00 to 18:00)

        for timestamp_str, count in happy_counts:
            timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            if 6 <= timestamp.hour <= 18:
                counts[
                    timestamp.hour - 6
                ] += count  # Adjust index to match 0-indexed list starting at 6:00

        happy_data = {"Happy": counts}

        # Prepare time labels for the x-axis
        times = [start_of_today + datetime.timedelta(hours=i) for i in range(13)]

        # Use the helper function to plot the data
        self.plot_day_trend(
            self.happy_figure,
            "Happy Emotions Over the Work Hours of Today",
            "Hour of the Day",
            "Count of Happy Emotions",
            happy_data,
            times,
        )

    def show_happy_trend_week(self):
        today = datetime.datetime.now().date()
        start_of_week = today - datetime.timedelta(
            days=today.weekday()
        )  # Monday of the current week
        start_time = datetime.datetime.combine(start_of_week, datetime.time(6, 0))
        end_time = datetime.datetime.combine(
            start_of_week + datetime.timedelta(days=4), datetime.time(18, 0)
        )

        # Get happy emotion counts for the entire week
        happy_counts = self.db_manager.get_happy_emotion_counts_for_week(
            start_time, end_time
        )

        # Initialize a dictionary to hold the counts for each day
        days_in_week = 5
        happy_data = {"Happy": [0] * days_in_week}

        # Fill the dictionary with the counts
        for date_str, hour_str, count in happy_counts:
            date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            if start_of_week <= date <= end_time.date():
                day_index = (date - start_of_week).days
                happy_data["Happy"][day_index] += count

        # Prepare date labels for the x-axis
        dates = [
            start_of_week + datetime.timedelta(days=i) for i in range(days_in_week)
        ]

        # Use the helper function to plot the data
        self.plot_week_trend(
            self.happy_figure,
            "Happy Emotions Over the Workweek",
            "Day of the Week",
            "Count of Happy Emotions",
            happy_data,
            dates,
        )

    def show_happy_trend_month(self):
        today = datetime.datetime.now().date()
        start_of_month = today.replace(day=1)
        end_of_month = (start_of_month + datetime.timedelta(days=32)).replace(
            day=1
        ) - datetime.timedelta(days=1)

        # Get happy emotion counts for the entire month
        happy_counts = self.db_manager.get_happy_emotion_counts(
            start_of_month, end_of_month
        )

        # Initialize a dictionary to hold the counts for each day
        days_in_month = (end_of_month - start_of_month).days + 1
        happy_data = {"Happy": [0] * days_in_month}

        # Fill the dictionary with the counts
        for timestamp_str, count in happy_counts:
            timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            day_index = (timestamp.date() - start_of_month).days
            happy_data["Happy"][day_index] += count

        # Prepare date labels for the x-axis
        dates = [
            start_of_month + datetime.timedelta(days=i) for i in range(days_in_month)
        ]

        # Use the helper function to plot the data
        month_name = start_of_month.strftime("%B")
        self.plot_month_trend(
            self.happy_figure,
            f"Happy Emotions Over the Month {month_name}",
            "Date",
            "Count of Happy Emotions",
            happy_data,
            dates,
        )

    def show_happy_trend_year(self):
        today = datetime.datetime.now().date()
        start_of_year = today.replace(month=1, day=1)
        end_of_year = today.replace(month=12, day=31)

        # Get happy emotion counts for the entire year
        happy_counts = self.db_manager.get_happy_emotion_counts(
            start_of_year, end_of_year
        )

        # Initialize a dictionary to hold the counts for each month
        months_in_year = 12
        happy_data = {"Happy": [0] * months_in_year}

        # Fill the dictionary with the counts
        for timestamp_str, count in happy_counts:
            timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            month_index = timestamp.month - 1
            happy_data["Happy"][month_index] += count

        # Prepare date labels for the x-axis
        dates = [start_of_year.replace(month=i + 1) for i in range(months_in_year)]

        # Use the helper function to plot the data
        self.plot_year_trend(
            self.happy_figure,
            "Happy Emotions Over the Year",
            "Month",
            "Count of Happy Emotions",
            happy_data,
            dates,
        )

    def plot_day_trend(self, figure, title, xlabel, ylabel, data, times):
        figure.clear()
        ax = figure.add_subplot(111)
        for label, counts in data.items():
            ax.plot(times, counts, marker="o", linestyle="-", label=label)

        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
        ax.legend()
        ax.grid(True)
        figure.canvas.draw()

    def plot_week_trend(self, figure, title, xlabel, ylabel, data, dates):
        figure.clear()
        ax = figure.add_subplot(111)
        for label, counts in data.items():
            ax.plot(dates, counts, marker="o", linestyle="-", label=label)

        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%a"))
        ax.xaxis.set_major_locator(mdates.DayLocator())
        ax.legend()
        ax.grid(True)
        figure.canvas.draw()

    def plot_month_trend(self, figure, title, xlabel, ylabel, data, dates):
        figure.clear()
        ax = figure.add_subplot(111)
        for label, counts in data.items():
            ax.plot(dates, counts, marker="o", linestyle="-", label=label)

        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d"))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
        ax.legend()
        ax.grid(True)
        figure.canvas.draw()

    def plot_year_trend(self, figure, title, xlabel, ylabel, data, dates):
        figure.clear()
        ax = figure.add_subplot(111)
        for label, counts in data.items():
            ax.plot(dates, counts, marker="o", linestyle="-", label=label)

        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.legend()
        ax.grid(True)
        figure.canvas.draw()

    def update_button_states(self, *, accept_button, discard_button, capture_button):
        self.accept_button.setEnabled(accept_button)
        self.discard_button.setEnabled(discard_button)
        self.capture_button.setEnabled(capture_button)
