from deepface import DeepFace


class DeepFaceAnalyzer:
    def analyze_emotions(self, face_roi):
        return DeepFace.analyze(
            face_roi, actions=["emotion", "age", "gender"], enforce_detection=False
        )
