import datetime

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
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src import DatabaseManager, EmotionTexts, FrameProcessor
from src.emotion_analyzer import EmotionAnalyzer
from src.face_detection import FaceDetector


class EmotionApp(QWidget):
    WINDOW_WIDTH_RATIO = 0.6
    WINDOW_HEIGHT_RATIO = 0.6

    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.face_detector = FaceDetector(model_name="mtcnn")
        self.emotion_analyzer = EmotionAnalyzer()
        self.frame_processor = FrameProcessor()
        self.emotion_texts = EmotionTexts()

        self.firstPageWidget = QWidget()
        self.mainPageWidget = QWidget()
        self.stackedWidget = QStackedWidget()
        self.stackedWidget.addWidget(self.firstPageWidget)
        self.stackedWidget.addWidget(self.mainPageWidget)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        layout.setSpacing(0)  # Remove spacing
        layout.addWidget(self.stackedWidget)
        self.setLayout(layout)
        self.live_video = True
        self.current_frame = None
        self.current_results = None
        self.current_happy_button = None
        self.current_emotion_button = None
        self.stackedWidget.setCurrentWidget(self.firstPageWidget)
        self.firstPage()
        self.initUI()

    def firstPage(self):
        self.firstPageWidget.setWindowTitle("Welcome to Emotion Recognizer")
        self.firstPageWidget.setStyleSheet("background-color: white")
        firstpage_layout = QVBoxLayout(self.firstPageWidget)
        self.setLayout(firstpage_layout)

        welcome_label = QLabel("Welcome to Emotion Recognizer")
        welcome_label.setStyleSheet("color: white; font-size: 24px")
        firstpage_layout.addWidget(welcome_label, alignment=Qt.AlignCenter)

        continue_button = QPushButton("Continue")
        continue_button.setStyleSheet("font-size: 18px")
        firstpage_layout.addWidget(continue_button, alignment=Qt.AlignCenter)
        continue_button.clicked.connect(self.changeScreen)

    def changeScreen(self):
        self.stackedWidget.setCurrentWidget(self.mainPageWidget)

    def initUI(self):
        self.mainPageWidget.setWindowTitle("Emotion Recognizer")
        self.mainPageWidget.setStyleSheet("background-color: white")
        main_layout = QVBoxLayout(self.mainPageWidget)
        self.setLayout(main_layout)

        self.setup_image_display(main_layout)
        self.setup_buttons(main_layout)
        self.setup_timer()

    def setup_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(20)

    def setup_buttons(self, main_layout):
        self.capture_button = QPushButton("", self)
        self.capture_button.setFixedSize(100, 100)  # Adjust the size as needed
        self.capture_button.setStyleSheet("border-radius: 50%; background-color: grey;")

        vertical_layout = QVBoxLayout()
        vertical_layout.addStretch()
        vertical_layout.addWidget(self.image_label, alignment=Qt.AlignCenter)
        vertical_layout.addWidget(self.capture_button, alignment=Qt.AlignCenter)
        vertical_layout.addStretch()

        horisontal_layout = QHBoxLayout()
        horisontal_layout.addStretch()
        horisontal_layout.addLayout(vertical_layout)
        horisontal_layout.addStretch()
        main_layout.addLayout(horisontal_layout)

        button_layout = (
            QHBoxLayout()
        )  # Create a horizontal layout for centering the button
        button_layout.addStretch()
        button_layout.addWidget(self.capture_button)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)  # Add the button layout to the main layout

        self.accept_button = QPushButton("Accept", self)
        self.discard_button = QPushButton("Discard", self)
        self.trend_button = QPushButton("Show Trends", self)
        self.capture_button.setVisible(True)
        self.accept_button.setVisible(False)
        self.discard_button.setVisible(False)
        self.trend_button.setVisible(False)
        main_layout.addWidget(self.accept_button)
        main_layout.addWidget(self.discard_button)
        main_layout.addWidget(self.trend_button)

        self.accept_button.setEnabled(False)
        self.discard_button.setEnabled(False)

        self.capture_button.clicked.connect(self.capture_image)
        self.accept_button.clicked.connect(self.accept_image)
        self.discard_button.clicked.connect(self.discard_image)
        self.trend_button.clicked.connect(self.show_trends_dialog)

    def setup_image_display(self, main_layout):
        self.image_label = QLabel(self)
        main_layout.addWidget(self.image_label, 0, alignment=Qt.AlignCenter)

        # Get the size of the application window
        window_width, window_height = self.size().width(), self.size().height()

        # Calculate the size with 25% margins on each side
        label_width = int(window_width)  # 50% of window width
        label_height = int(window_height)  # 50% of window height
        self.image_label.setStyleSheet("border: 5px solid pink")
        self.image_label.setFixedSize(label_width, label_height)

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
            self.capture_button.setVisible(False)
            self.accept_button.setVisible(True)
            self.discard_button.setVisible(True)
            self.trend_button.setVisible(True)
            self.capture_image()
            print("Picture is captured!")
        elif event.key() == Qt.Key_R:
            self.accept_button.setVisible(False)
            self.discard_button.setVisible(False)
            self.trend_button.setVisible(False)
            self.capture_button.setVisible(True)
            self.live_video = True
            print("Resuming live feed...")
        elif event.key() == Qt.Key_Q:
            print("Exiting... Bye!")
            self.close()

    def capture_image(self):
        self.live_video = False
        frame = self.frame_processor.capture_frame()
        self.capture_button.setVisible(False)
        self.accept_button.setVisible(True)
        self.discard_button.setVisible(True)
        self.trend_button.setVisible(True)
        if frame is not None:
            # MTCNN face detection
            self.face_detector = FaceDetector(model_name="mtcnn")
            mtcnn_face_boxes = self.face_detector.detect_faces(frame)
            mtcnn_results = self.process_face_boxes(frame, mtcnn_face_boxes, "MTCNN")

            # HaarCascade face detection
            self.face_detector = FaceDetector(model_name="haarcascade")
            cascade_face_boxes = self.face_detector.detect_faces(frame)
            cascade_results = self.process_face_boxes(
                frame, cascade_face_boxes, "HaarCascade"
            )

            # Compare results
            self.compare_results(mtcnn_results, cascade_results)

            # Choose which results to use for the final image display and database entry
            # Here we choose MTCNN results for example
            self.current_results = mtcnn_results if mtcnn_results else cascade_results

            # Display annotated frame
            if self.current_results:
                annotated_frame = self.frame_processor.annotate_frame(
                    frame, self.current_results
                )
                self.display_image(annotated_frame)
                self.current_frame = annotated_frame
            else:
                self.display_image(frame)
                self.current_frame = frame

            self.update_button_states(
                accept_button=True, discard_button=True, capture_button=False
            )
        else:
            print("No frame captured to process.")

    def process_face_boxes(self, frame, face_boxes, model_name):
        results = []
        for box in face_boxes:
            x, y, w, h = box["x"], box["y"], box["w"], box["h"]
            face_roi = frame[y : y + h, x : x + w]
            emotion_result = self.emotion_analyzer.analyze_emotions(face_roi)
            emotion_result[0]["region"] = box
            emotion_result[0][
                "model_name"
            ] = model_name  # Adding model name for comparison
            results.append(emotion_result)
        return results

    def compare_results(self, mtcnn_results, cascade_results):
        print("MTCNN Results:")
        for result in mtcnn_results:
            print(result)

        print("\nCascade Results:")
        for result in cascade_results:
            print(result)

    def accept_image(self):
        if self.current_results:
            self.add_to_database(self.current_results)
        self.update_button_states(
            accept_button=False, discard_button=False, capture_button=True
        )
        self.accept_button.setVisible(False)
        self.discard_button.setVisible(False)
        self.trend_button.setVisible(False)
        self.capture_button.setVisible(True)
        self.live_video = True

    def discard_image(self):
        self.update_button_states(
            accept_button=False, discard_button=False, capture_button=True
        )
        self.live_video = True
        self.accept_button.setVisible(False)
        self.discard_button.setVisible(False)
        self.trend_button.setVisible(False)
        self.capture_button.setVisible(True)
        print("Image was discarded!")

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
        self.happy_button_layout = QHBoxLayout()

        self.happy_day_button = QPushButton("Day")
        self.happy_week_button = QPushButton("Week")
        self.happy_month_button = QPushButton("Month")
        self.happy_year_button = QPushButton("Year")

        self.happy_day_button.clicked.connect(lambda: self.show_happy_trend_day(True))
        self.happy_week_button.clicked.connect(lambda: self.show_happy_trend_week(True))
        self.happy_month_button.clicked.connect(
            lambda: self.show_happy_trend_month(True)
        )
        self.happy_year_button.clicked.connect(lambda: self.show_happy_trend_year(True))

        self.happy_button_layout.addWidget(self.happy_day_button)
        self.happy_button_layout.addWidget(self.happy_week_button)
        self.happy_button_layout.addWidget(self.happy_month_button)
        self.happy_button_layout.addWidget(self.happy_year_button)

        happy_layout.addLayout(self.happy_button_layout)
        happy_layout.addWidget(self.happy_canvas)
        happy_tab.setLayout(happy_layout)

        # Emotion Tabs and Buttons
        self.emotion_figure = plt.figure()
        self.emotion_canvas = FigureCanvas(self.emotion_figure)
        emotion_tab = QWidget()
        emotion_layout = QVBoxLayout()
        self.emotion_button_layout = QHBoxLayout()

        self.emotion_day_button = QPushButton("Day")
        self.emotion_week_button = QPushButton("Week")
        self.emotion_month_button = QPushButton("Month")
        self.emotion_year_button = QPushButton("Year")

        self.emotion_day_button.clicked.connect(
            lambda: self.show_emotion_trend_day(True)
        )
        self.emotion_week_button.clicked.connect(
            lambda: self.show_emotion_trend_week(True)
        )
        self.emotion_month_button.clicked.connect(
            lambda: self.show_emotion_trend_month(True)
        )
        self.emotion_year_button.clicked.connect(
            lambda: self.show_emotion_trend_year(True)
        )

        self.emotion_button_layout.addWidget(self.emotion_day_button)
        self.emotion_button_layout.addWidget(self.emotion_week_button)
        self.emotion_button_layout.addWidget(self.emotion_month_button)
        self.emotion_button_layout.addWidget(self.emotion_year_button)

        emotion_layout.addLayout(self.emotion_button_layout)
        emotion_layout.addWidget(
            self.emotion_canvas
        )  # Add the canvas to the emotion tab main_layout
        emotion_tab.setLayout(emotion_layout)

        self.tabs.addTab(happy_tab, "Happy Emotions Count")
        self.tabs.addTab(emotion_tab, "All Emotion Count")

        dialog_layout.addWidget(self.tabs)

        self.trends_window.setLayout(dialog_layout)

        # Show the default graph (e.g., Happy Emotions Over the Day)
        self.show_happy_trend_day(True)
        self.happy_tab_viewed = True
        self.current_happy_button = self.happy_day_button

        # Connect tab change to method
        self.tabs.currentChanged.connect(self.on_tab_changed)

        self.trends_window.exec()

    def on_tab_changed(self, index):
        if index == 0:
            if not self.happy_tab_viewed:
                self.show_happy_trend_day(True)
                self.happy_tab_viewed = True
                self.current_happy_button = self.happy_day_button
            else:
                selected_button = self.get_selected_button(self.happy_button_layout)
                self.current_happy_button = (
                    selected_button if selected_button else self.happy_day_button
                )
                self.update_tab_styles(
                    self.current_happy_button, self.happy_button_layout
                )
        elif index == 1:
            if not self.emotion_tab_viewed:
                self.show_emotion_trend_day(True)
                self.emotion_tab_viewed = True
                self.current_emotion_button = self.emotion_day_button
            else:
                selected_button = self.get_selected_button(self.emotion_button_layout)
                self.current_emotion_button = (
                    selected_button if selected_button else self.emotion_day_button
                )
                self.update_tab_styles(
                    self.current_emotion_button, self.emotion_button_layout
                )

    def get_selected_button(self, button_layout):
        for i in range(button_layout.count()):
            button = button_layout.itemAt(i).widget()
            if button.styleSheet() == "background-color: blue; color: white;":
                return button
        return None

    def update_tab_styles(self, selected_button, button_layout):
        for i in range(button_layout.count()):
            button = button_layout.itemAt(i).widget()
            if button == selected_button:
                button.setStyleSheet("background-color: blue; color: white;")
            else:
                button.setStyleSheet("")

    def show_emotion_trend_day(self, update_styles=False):
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
        if update_styles:
            self.update_tab_styles(self.emotion_day_button, self.emotion_button_layout)
            self.current_emotion_button = self.emotion_day_button

    def show_emotion_trend_week(self, update_styles=False):
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
        if update_styles:
            self.update_tab_styles(self.emotion_week_button, self.emotion_button_layout)
            self.current_emotion_button = self.emotion_week_button

    def show_emotion_trend_month(self, update_styles=False):
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

        # Prepare date labels for the x-axis
        dates = [
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
            dates,
        )
        if update_styles:
            self.update_tab_styles(
                self.emotion_month_button, self.emotion_button_layout
            )
            self.current_emotion_button = self.emotion_month_button

    def show_emotion_trend_year(self, update_styles=False):
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

        # Prepare date labels for the x-axis
        dates = [start_of_year.replace(month=i + 1) for i in range(months_in_year)]

        # Use the helper function to plot the data
        self.plot_year_trend(
            self.emotion_figure,
            "Emotions Over the Year",
            "Month",
            "Count of Emotions",
            emotion_data,
            dates,
        )
        if update_styles:
            self.update_tab_styles(self.emotion_year_button, self.emotion_button_layout)
            self.current_emotion_button = self.emotion_year_button

    def show_happy_trend_day(self, update_styles=False):
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
        if update_styles:
            self.update_tab_styles(self.happy_day_button, self.happy_button_layout)
            self.current_emotion_button = self.happy_day_button

    def show_happy_trend_week(self, update_styles=False):
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
        if update_styles:
            self.update_tab_styles(self.happy_week_button, self.happy_button_layout)
            self.current_emotion_button = self.happy_week_button

    def show_happy_trend_month(self, update_styles=False):
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
        if update_styles:
            self.update_tab_styles(self.happy_month_button, self.happy_button_layout)
            self.current_emotion_button = self.happy_month_button

    def show_happy_trend_year(self, update_styles=False):
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
        if update_styles:
            self.update_tab_styles(self.happy_year_button, self.happy_button_layout)
            self.current_emotion_button = self.happy_year_button

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
