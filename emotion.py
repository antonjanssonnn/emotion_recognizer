import cv2
from deepface import DeepFace
import sqlite3
import os
from PIL import Image, ImageFont, ImageDraw
import numpy as np


class EmotionAnalyzer:
    def __init__(self):
        self.conn = sqlite3.connect('emotions.db')
        self.cursor = self.conn.cursor()
        self.setup_database()
        self.check_and_create_directory()
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.cap = self.initialize_camera()

    # Emotion to Emoji mapping
    emotion_emoji_map = {
        'angry': 'emojis/angry.png',
        'fear': 'emojis/fear.png',
        'happy': 'emojis/happy.png',
        'sad': 'emojis/sad.png',
        'surprise': 'emojis/surprise.png',
        'neutral': 'emojis/neutral_smile.png' 
    }

    def setup_database(self):
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

    def check_and_create_directory(self):
        if not os.path.exists('captured_images'):
            os.makedirs('captured_images')

    def initialize_camera(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Could not open video capture device.")
            exit()
        return cap
    
    def capture_frame(self):
        if not self.cap.isOpened():
            print("Camera not opened, attempting to reopen...")
            self.cap.open(0)  # Attempt to reopen the camera
        ret, frame = self.cap.read()
        if not ret:
            print("Failed to grab frame")
            return None
        return frame

    def analyze_frame(self, frame):
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
        emoji_img = Image.open(emoji_path).convert("RGBA")
        pil_frame = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).convert("RGBA")
        emoji_img = emoji_img.resize((50, 50), None)
        pil_frame.paste(emoji_img, position, emoji_img)
        return cv2.cvtColor(np.array(pil_frame), cv2.COLOR_RGBA2BGR)

    def close(self):
        self.conn.close()
        self.cap.release()
