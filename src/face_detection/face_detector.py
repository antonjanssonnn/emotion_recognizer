from src.face_detection.haarcascade_detector import HaarCascadeDetector
from src.face_detection.mtcnn_detector import MTCNNDetector
from src.face_detection.retinaface_detector import RetinaFaceDetector


class FaceDetector:
    def __init__(self, model_name="mtcnn"):
        if model_name == "mtcnn":
            self.detector = MTCNNDetector()
        elif model_name == "haarcascade":
            self.detector = HaarCascadeDetector()
        elif model_name == "retinaface":
            self.detector = RetinaFaceDetector()
        else:
            raise ValueError(f"Unknown model name: {model_name}")

    def detect_faces(self, frame):
        return self.detector.detect_faces(frame)
