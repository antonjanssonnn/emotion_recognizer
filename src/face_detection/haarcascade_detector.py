import cv2


class HaarCascadeDetector:
    CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    SCALE_FACTOR = 1.1
    MIN_NEIGHBORS = 8
    MIN_SIZE = (30, 30)

    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(self.CASCADE_PATH)

    def detect_faces(self, frame):
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray_frame,
            scaleFactor=self.SCALE_FACTOR,
            minNeighbors=self.MIN_NEIGHBORS,
            minSize=self.MIN_SIZE,
        )
        return [{"x": x, "y": y, "w": w, "h": h} for (x, y, w, h) in faces]
