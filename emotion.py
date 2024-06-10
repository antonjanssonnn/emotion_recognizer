import cv2
from deepface import DeepFace
import sqlite3
import os
from PIL import Image
import numpy as np


class EmotionAnalyzer:
    # Emotion to Emoji mapping
    EMOTION_EMOJI_MAP = {
        'angry': 'emojis/angry.png',
        'fear': 'emojis/fear.png',
        'happy': 'emojis/happy.png',
        'sad': 'emojis/sad.png',
        'surprise': 'emojis/surprise.png',
        'neutral': 'emojis/neutral_smile.png' 
    }

    DATABASE_PATH = 'emotions.db'
    IMAGE_DIRECTORY = 'captured_images'
    CASCADE_PATH = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    EMOJI_SIZE = (50, 50)

    def __init__(self):
        self.conn = self.initialize_database()
        self.cursor = self.conn.cursor()
        self.setup_database()
        self.ensure_directory_exists(self.IMAGE_DIRECTORY)
        self.face_cascade = self.initialize_face_cascade()
        self.cap = self.initialize_camera()

    def initialize_database(self) -> sqlite3.Connection:
        """Initializes the SQLite database connection."""
        try:
            conn = sqlite3.connect(self.DATABASE_PATH)
            return conn
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
            exit()

    def setup_database(self):
        """Sets up the emotions table in the database."""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS emotions (
                    id INTEGER PRIMARY KEY,
                    emotion TEXT,
                    age TEXT,
                    gender TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Database setup error: {e}")
            exit()

    def ensure_directory_exists(self, directory):
        """Ensures the specified directory exists."""
        if not os.path.exists(directory):
            os.makedirs(directory)

    def initialize_face_cascade(self) -> cv2.CascadeClassifier:
        """Initializes the face cascade classifier."""
        face_cascade = cv2.CascadeClassifier(self.CASCADE_PATH)
        if face_cascade.empty():
            print("Failed to load cascade classifier")
            exit()
        return face_cascade

    def initialize_camera(self):
        """Initializes the camera."""
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Could not open video capture device.")
            exit()
        return cap

    def capture_frame(self):
        """Captures a frame from the camera."""
        if not self.cap.isOpened():
            print("Camera not opened, attempting to reopen...")
            self.cap.open(0)  # Attempt to reopen the camera
        ret, frame = self.cap.read()
        if not ret:
            print("Failed to grab frame")
            return None
        return frame

    def analyze_frame(self, frame):
        """Analyzes the frame for faces and their emotions."""
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=8, minSize=(30, 30))

        results = []
        for (x, y, w, h) in faces:
            face_roi = frame[y:y+h, x:x+w]
            result = DeepFace.analyze(face_roi, actions=['emotion', 'age', 'gender'], enforce_detection=False)
            result[0]['region'] = {'x': x, 'y': y, 'w': w, 'h': h}
            results.append(result)
        return results

    def add_emoji_to_frame(self, frame, emoji_path, position):
        """Adds an emoji to the frame at the specified position."""
        emoji_img = Image.open(emoji_path).convert("RGBA")
        pil_frame = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).convert("RGBA")
        emoji_img = emoji_img.resize(self.EMOJI_SIZE, None)
        pil_frame.paste(emoji_img, position, emoji_img)
        return cv2.cvtColor(np.array(pil_frame), cv2.COLOR_RGBA2BGR)

    def close(self):
        """Closes the database connection and releases the camera."""
        self.conn.close()
        self.cap.release()
