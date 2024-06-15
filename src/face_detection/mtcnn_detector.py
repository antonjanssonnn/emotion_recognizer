import torch
from facenet_pytorch import MTCNN


class MTCNNDetector:
    def __init__(self):
        self.mtcnn = MTCNN(
            keep_all=True, device="cuda" if torch.cuda.is_available() else "cpu"
        )

    def detect_faces(self, frame):
        boxes, _ = self.mtcnn.detect(frame)
        if boxes is None:
            return []
        return [
            {
                "x": int(b[0]),
                "y": int(b[1]),
                "w": int(b[2] - b[0]),
                "h": int(b[3] - b[1]),
            }
            for b in boxes
        ]
