import logging

import cv2
from deepface import DeepFace


class EmotionAnalyzer:
    CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    SCALE_FACTOR = 1.1
    MIN_NEIGHBORS = 8
    MIN_SIZE = (30, 30)

    def __init__(self):
        self.face_cascade = self.initialize_face_cascade()

    def initialize_face_cascade(self) -> cv2.CascadeClassifier:
        """Initializes the face cascade classifier."""
        face_cascade = cv2.CascadeClassifier(self.CASCADE_PATH)
        if face_cascade.empty():
            logging.error("Failed to load cascade classifier")
            exit()
        return face_cascade

    def analyze_frame(self, frame):
        """Analyzes the frame for faces and their emotions."""
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray_frame,
            scaleFactor=self.SCALE_FACTOR,
            minNeighbors=self.MIN_NEIGHBORS,
            minSize=self.MIN_SIZE,
        )

        results = []
        for x, y, w, h in faces:
            face_roi = frame[y : y + h, x : x + w]
            result = DeepFace.analyze(
                face_roi, actions=["emotion", "age", "gender"], enforce_detection=False
            )
            result[0]["region"] = {"x": x, "y": y, "w": w, "h": h}
            results.append(result)
        return results
