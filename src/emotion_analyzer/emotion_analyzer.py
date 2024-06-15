from src.emotion_analyzer.deepface_analyzer import DeepFaceAnalyzer


class EmotionAnalyzer:
    def __init__(self, analyzer_name="deepface"):
        if analyzer_name == "deepface":
            self.analyzer = DeepFaceAnalyzer()
        else:
            raise ValueError(f"Unknown analyzer name: {analyzer_name}")

    def analyze_emotions(self, face_roi):
        return self.analyzer.analyze_emotions(face_roi)
