import cv2
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PySide6.QtCore import Qt, QTimer, QRect, QPropertyAnimation
from PySide6.QtGui import QKeyEvent, QPainter
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QMessageBox,
    QSlider
)

from src import DatabaseManager, EmotionTexts, FrameProcessor, Graph
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
        self.single_person_mode = True

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

        self.welcome_label = QLabel("Good morning amazing Human!", self)
        self.welcome_label.setStyleSheet("color: pink; font-size: 44px")
        firstpage_layout.addWidget(self.welcome_label, alignment=Qt.AlignCenter)
        description_label = QLabel(
            "Get a reading of your emotion, age and gender by \nme, Sam, an AI bot... While getting your coffee or tea. \nHave fun with it!"
        )
        description_label.setStyleSheet("color: black; font-size: 30px")
        firstpage_layout.addWidget(description_label, alignment=Qt.AlignCenter)

        self.continue_button = QPushButton("Start camera", self)
        self.continue_button.setFixedSize(130, 90)
        self.continue_button.setStyleSheet(
            "border-radius: 5%; background-color: pink; color: white; font-size: 18px"
        )
        firstpage_layout.addWidget(self.continue_button, alignment=Qt.AlignCenter)
        self.continue_button.clicked.connect(self.changeScreen)

        # Trend to be launched in next version
        # self.trend_button = QPushButton("View trend", self)
        # self.trend_button.setFixedSize(100, 60)
        # self.trend_button.setStyleSheet("border: 3px solid pink;border-radius: 2%; background-color: white; color: black; font-size: 18px")
        # firstpage_layout.addWidget(self.trend_button, alignment=Qt.AlignCenter)
        # self.trend_button.clicked.connect(self.show_trends_dialog)

        # TODO ADD GDPR Popup!
        self.gdpr_button = QPushButton(
            "Read how we handle the information according to GDPR.", self
        )
        self.gdpr_button.setStyleSheet(
            "color: black; font-size: 20; text-decoration: underline; border: 10px solid white;"
        )
        firstpage_layout.addWidget(self.gdpr_button, alignment=Qt.AlignCenter)
        self.gdpr_button.clicked.connect(self.show_gdpr_dialog)

    def show_gdpr_dialog(self):
        print("CLICKED")
        self.gdpr_window = QDialog(self)
        self.gdpr_window.setWindowTitle("Privacy policy")
        self.gdpr_title = QLabel("Privacy policy", self)
        self.gdpr_title.setStyleSheet("text-decoration: bold; font-size: 40")
        self.gdpr_text = QTextEdit("", self)

        html_content = """
        How we handle your personal data according to GDPR.\nConsent and Data Collection:\n
        <ul>
            <li>
                You have the choice to allow photo to be taken.
                Once the photo is taken and your mood, age and gender have been registered by AI, you can choose whether the mood should be saved or discarded.
            </li>
            <li>
                Regardless of your choice, the photo will be deleted immediately after the AI assessment.
            </li>
        </ul>
        Anonymity and Data Protection:
        <ul>
            <li>
                Your anonymity is protected; no personally identifiable information is collected during this process.
            </li>
            <li>
                Only your mood will be saved if you choose to do so.
            </li>
        </ul>
        For more information on how we handle your personal data, <a href="http://google.com" style="text-decoration: underline;">...'s full Privacy policy</a>
        """

        self.gdpr_text.setHtml(html_content)
        self.gdpr_text.setReadOnly(True)
        gdpr_layout = QVBoxLayout(self.gdpr_window)
        self.text = QLabel("GDPR", self)
        gdpr_layout.addWidget(self.gdpr_text, 0, Qt.AlignCenter)
        gdpr_layout.addWidget(self.text, 0, Qt.AlignCenter)

        self.gdpr_window.exec()

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
        # Capture Button
        self.capture_button = QPushButton("", self)
        self.capture_button.setFixedSize(70, 70)  # Adjust the size as needed
        self.capture_button.setStyleSheet("border: 5px solid purple; border-radius: 35px; background-color: pink;")

        # Toggle Blur Button 
     #   self.toggle_blur_button = QPushButton("Friends or Alone", self)
      #  self.toggle_blur_button.setFixedSize(100, 50)  # Adjust the size as needed
       # self.toggle_blur_button.setStyleSheet("background-color: grey;")

        # Create the background frame
        self.frame = QPushButton("Only me", self)
        self.frame.setFixedSize(100, 50)
        self.frame.setStyleSheet("background-color: lightgray; border: 2px solid black; border-radius: 25px;")
        self.frame.setEnabled(False)

        # Create the toggle button
        firstHorisontalLayour = QHBoxLayout()
        firstHorisontalLayour.addStretch()
        self.toggle_button = QPushButton("Me & My Friends", self)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setFixedSize(100, 50)
        self.toggle_button.setStyleSheet("background-color: white; border: 2px solid black; border-radius: 25px;")
        self.toggle_button.move(0, 0)
        self.toggle_button.clicked.connect(self.animate)
        firstHorisontalLayour.addWidget(self.frame, alignment=Qt.AlignCenter)
        firstHorisontalLayour.addStretch()
        firstHorisontalLayour.addWidget(self.toggle_button, alignment=Qt.AlignCenter)
        firstHorisontalLayour.addStretch()

        self.animation = QPropertyAnimation(self.toggle_button, b"geometry")
        
        # Vertical Layout
        vertical_layout = QVBoxLayout()
        vertical_layout.addStretch()
        vertical_layout.addWidget(self.image_label, alignment=Qt.AlignCenter)
        vertical_layout.addStretch()
        vertical_layout.addWidget(self.capture_button, alignment=Qt.AlignCenter)
        vertical_layout.addStretch()
        main_layout.addLayout(vertical_layout)


        # Buttons
        self.retake_button = QPushButton("Retake", self)
        self.retake_button.setFixedSize(70, 70)
        self.retake_button.setStyleSheet("border: 3px solid pink; border-radius: 5%;")
        self.accept_button = QPushButton("Accept", self)
        self.accept_button.setFixedSize(70, 70)
        self.accept_button.setStyleSheet("border: 3px solid pink; border-radius: 5%;")
        self.discard_button = QPushButton("Discard", self)
        self.discard_button.setFixedSize(70, 70)
        self.discard_button.setStyleSheet("border: 3px solid pink; border-radius: 5%;")
        # self.trend_button = QPushButton("Show Trends", self)
        self.capture_button.setVisible(True)
        self.accept_button.setVisible(False)
        self.discard_button.setVisible(False)
        self.retake_button.setVisible(False)
        # self.trend_button.setVisible(False)

        # Horisontal Layout - Handling the horisontal position!
        horisontal_layout = QHBoxLayout()
        horisontal_layout.addStretch()
        horisontal_layout.addWidget(self.accept_button, alignment=Qt.AlignCenter)
        horisontal_layout.addWidget(self.discard_button, alignment=Qt.AlignCenter)
        horisontal_layout.addWidget(self.retake_button, alignment=Qt.AlignCenter)
        horisontal_layout.addStretch()
        main_layout.addLayout(horisontal_layout)

        # #main_layout.addWidget(self.trend_button)
        # self.accept_button.setEnabled(False)
        # self.discard_button.setEnabled(False)

        self.capture_button.clicked.connect(self.capture_image)
        self.accept_button.clicked.connect(self.accept_image)
        self.discard_button.clicked.connect(self.discard_image)
        self.retake_button.clicked.connect(self.retake_image)
        #self.toggle_blur_button.clicked.connect(self.toggle_single_person_mode)
        # self.trend_button.clicked.connect(self.show_trends_dialog)
    
    def animate(self):
        if self.toggle_button.isChecked():
            self.animation.setEndValue(QRect(50, 0, 50, 50))
            self.frame.setStyleSheet("background-color: pink; border: 2px solid black; border-radius: 25px;")
        else:
            self.animation.setEndValue(QRect(0, 0, 50, 50))
            self.frame.setStyleSheet("background-color: white; border: 2px solid black; border-radius: 25px;")

        self.animation.setDuration(200)  # Animation duration in milliseconds
        self.animation.start()
    
    def show_pop_up_discarded(self):
        popup = QMessageBox(self)
        popup.setWindowTitle("")
        popup.setText("Picture Discarded!")
        popup.show()
        # Close the popup after 5 seconds
        QTimer.singleShot(5000, popup.close)
    
    def show_accept_image_popup(self):
        popup = QMessageBox(self)
        popup.setWindowTitle("")
        popup.setText("Thank you! \n Emotion was saved")
        popup.show()
        # Close the popup after 5 seconds
        QTimer.singleShot(5000, popup.close)


    def retake_image(self):
        self.update_button_states(
            accept_button=False, discard_button=False, capture_button=True
        )
        self.live_video = True
        self.accept_button.setVisible(False)
        self.discard_button.setVisible(False)
        # self.trend_button.setVisible(False)
        self.capture_button.setVisible(True)
        self.retake_button.setVisible(False)
        # ADD POPUP THAT SHOWS FOR 5 seconds
        self.stackedWidget.setCurrentWidget(self.mainPageWidget)
        print("Image was discarded!")

    def setup_image_display(self, main_layout):
        self.image_label = QLabel(self)
        main_layout.addWidget(self.image_label, 0, alignment=Qt.AlignCenter)

        # Get the size of the application window
        window_width, window_height = self.size().width(), self.size().height()

        # Calculate the size with 25% margins on each side
        label_width = int(window_width)  # 50% of window width
        label_height = int(window_height)  # 50% of window height
        self.image_label.setFixedSize(label_width, label_height)
        self.image_label.setStyleSheet("border: 5px solid pink; border-radius: 10%")

    def setup_toggle(self, main_layout):
        self.toggle_blur_button = QPushButton("Friends or Alone", self)
        self.toggle_blur_button.setFixedSize(100, 50)  # Adjust the size as needed
        self.toggle_blur_button.setStyleSheet("background-color: grey;")
        self.toggle_blur_button.clicked.connect(self.toggle_single_person_mode)
        main_layout.addWidget(self.toggle_blur_button)

    def toggle_single_person_mode(self):
        self.single_person_mode = not self.single_person_mode
        print(f"Single person mode set to: {self.single_person_mode}")

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
                if self.single_person_mode:
                    frame = self.frame_processor.blur_edges(frame)
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
            # self.trend_button.setVisible(True)
            self.capture_image()
            print("Picture is captured!")
        elif event.key() == Qt.Key_R:
            self.accept_button.setVisible(False)
            self.discard_button.setVisible(False)
            # self.trend_button.setVisible(False)
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
        self.retake_button.setVisible(True)
        # self.trend_button.setVisible(True)
        if frame is not None:
            if self.single_person_mode:
                blurred_frame = self.frame_processor.blur_edges(frame)
                mask = self.frame_processor.create_face_mask(frame)
                frame = cv2.bitwise_and(frame, frame, mask=mask)
            else:
                blurred_frame = frame

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
                    blurred_frame, self.current_results
                )
                self.display_image(annotated_frame)
                self.current_frame = annotated_frame
            else:
                self.display_image(blurred_frame)
                self.current_frame = blurred_frame

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
            accept_button=False, discard_button=False, capture_button=False
        )
        self.accept_button.setVisible(False)
        self.discard_button.setVisible(False)
        # self.trend_button.setVisible(False)
        self.capture_button.setVisible(False)
        self.live_video = False
        # ADD POPUP THAT SHOWS FOR 5 seconds
        self.show_accept_image_popup()
        self.stackedWidget.setCurrentWidget(self.firstPageWidget)

    def discard_image(self):
        self.update_button_states(
            accept_button=False, discard_button=False, capture_button=True
        )
        self.live_video = True
        self.accept_button.setVisible(False)
        self.discard_button.setVisible(False)
        # self.trend_button.setVisible(False)
        self.capture_button.setVisible(True)
        self.retake_button.setVisible(False)
        # ADD POPUP THAT SHOWS FOR 5 seconds
        self.show_pop_up_discarded()
        self.stackedWidget.setCurrentWidget(self.firstPageWidget)
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
        self.emotion_figure = plt.figure()
        self.emotion_canvas = FigureCanvas(self.emotion_figure)

        # Initialize the Graph class
        self.graph = Graph(
            self.db_manager, self.happy_figure, self.emotion_figure, self
        )

        # Flags to track if the tabs have been viewed
        self.graph.happy_tab_viewed = False
        self.graph.emotion_tab_viewed = False

        # Happy Tab and Buttons
        happy_tab = QWidget()
        happy_layout = QVBoxLayout()
        self.happy_button_layout = QHBoxLayout()

        self.happy_day_button = QPushButton("Day")
        self.happy_week_button = QPushButton("Week")
        self.happy_month_button = QPushButton("Month")
        self.happy_year_button = QPushButton("Year")

        self.happy_day_button.clicked.connect(
            lambda: self.graph.show_happy_trend_day(True)
        )
        self.happy_week_button.clicked.connect(
            lambda: self.graph.show_happy_trend_week(True)
        )
        self.happy_month_button.clicked.connect(
            lambda: self.graph.show_happy_trend_month(True)
        )
        self.happy_year_button.clicked.connect(
            lambda: self.graph.show_happy_trend_year(True)
        )

        self.happy_button_layout.addWidget(self.happy_day_button)
        self.happy_button_layout.addWidget(self.happy_week_button)
        self.happy_button_layout.addWidget(self.happy_month_button)
        self.happy_button_layout.addWidget(self.happy_year_button)

        happy_layout.addLayout(self.happy_button_layout)
        happy_layout.addWidget(self.happy_canvas)
        happy_tab.setLayout(happy_layout)

        # Emotion Tabs and Buttons
        emotion_tab = QWidget()
        emotion_layout = QVBoxLayout()
        self.emotion_button_layout = QHBoxLayout()

        self.emotion_day_button = QPushButton("Day")
        self.emotion_week_button = QPushButton("Week")
        self.emotion_month_button = QPushButton("Month")
        self.emotion_year_button = QPushButton("Year")

        self.emotion_day_button.clicked.connect(
            lambda: self.graph.show_emotion_trend_day(True)
        )
        self.emotion_week_button.clicked.connect(
            lambda: self.graph.show_emotion_trend_week(True)
        )
        self.emotion_month_button.clicked.connect(
            lambda: self.graph.show_emotion_trend_month(True)
        )
        self.emotion_year_button.clicked.connect(
            lambda: self.graph.show_emotion_trend_year(True)
        )

        self.emotion_button_layout.addWidget(self.emotion_day_button)
        self.emotion_button_layout.addWidget(self.emotion_week_button)
        self.emotion_button_layout.addWidget(self.emotion_month_button)
        self.emotion_button_layout.addWidget(self.emotion_year_button)

        emotion_layout.addLayout(self.emotion_button_layout)
        emotion_layout.addWidget(self.emotion_canvas)
        emotion_tab.setLayout(emotion_layout)

        self.tabs.addTab(happy_tab, "Happy Emotions Count")
        self.tabs.addTab(emotion_tab, "All Emotion Count")

        dialog_layout.addWidget(self.tabs)

        self.trends_window.setLayout(dialog_layout)

        # Show the default graph (e.g., Happy Emotions Over the Day)
        self.graph.show_happy_trend_day(True)
        self.graph.happy_tab_viewed = True
        self.graph.current_happy_button = self.happy_day_button

        # Connect tab change to method
        self.tabs.currentChanged.connect(self.graph.on_tab_changed)

        self.trends_window.exec()

    def update_button_states(self, *, accept_button, discard_button, capture_button):
        self.accept_button.setEnabled(accept_button)
        self.discard_button.setEnabled(discard_button)
        self.capture_button.setEnabled(capture_button)
