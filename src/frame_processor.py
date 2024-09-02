import logging
import time

import cv2
import numpy as np
from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap


class FrameProcessor:
    EMOTION_EMOJI_MAP = {
        "angry": "emojis/angry.png",
        "fear": "emojis/fear.png",
        "happy": "emojis/happy.png",
        "sad": "emojis/sad.png",
        "surprise": "emojis/surprise.png",
        "neutral": "emojis/neutral_smile.png",
    }
    EMOJI_SIZE = (50, 50)

    def __init__(self):
        self.cap = self.initialize_camera()

    def initialize_camera(self):
        """Initializes the camera."""
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            logging.error("Error: Could not open video capture device.")
            exit()
        time.sleep(1)  # One-time delay to allow the camera to initialize
        return cap

    def capture_frame(self):
        """Captures a frame from the camera."""
        if not self.cap.isOpened():
            logging.warning("Camera not opened, attempting to reopen...")
            self.cap.open(0)  # Attempt to reopen the camera
        ret, frame = self.cap.read()
        if not ret:
            logging.error("Failed to grab frame")
            return None
        return frame

    def blur_edges(self, frame, blur_color=(255, 233, 236)):
        """Blurs the edges of the frame, keeping the central face-shaped region clear with a specific color blur."""
        h, w = frame.shape[:2]
        center_x, center_y = w // 2, h // 2
        region_w, region_h = int(w * 0.4), int(h * 0.85)

        # Create an elliptical mask for the face shape
        mask = np.zeros((h, w), dtype=np.uint8)
        cv2.ellipse(
            mask,
            (center_x, center_y),
            (region_w // 2, region_h // 2),
            0,
            0,
            360,
            255,
            -1,
        )

        # Blur the frame
        blurred_frame = cv2.GaussianBlur(frame, (99, 99), 0)

        # Change the color of the blurred area
        colored_blur = np.full_like(blurred_frame, blur_color)
        colored_blur = cv2.bitwise_and(colored_blur, colored_blur, mask=255 - mask)
        blurred_frame = cv2.bitwise_and(blurred_frame, blurred_frame, mask=255 - mask)
        blurred_color_frame = cv2.addWeighted(colored_blur, 0.5, blurred_frame, 0.5, 0)

        # Combine the original frame with the blurred, colored frame
        clear_region = cv2.bitwise_and(frame, frame, mask=mask)
        return cv2.add(clear_region, blurred_color_frame)

    def create_face_mask(self, frame):
        """Creates a mask for the face-shaped region to exclude blurred areas from detection."""
        h, w = frame.shape[:2]
        center_x, center_y = w // 2, h // 2
        region_w, region_h = int(w * 0.4), int(h * 0.7)  # Should match the blur area
        mask = np.zeros((h, w), dtype=np.uint8)
        cv2.ellipse(
            mask,
            (center_x, center_y),
            (region_w // 2, region_h // 2),
            0,
            0,
            360,
            255,
            -1,
        )
        return mask

    def get_central_region(self, frame):
        """Returns the central region of the frame."""
        h, w = frame.shape[:2]
        center_x, center_y = w // 2, h // 2
        region_w, region_h = int(w * 0.3), int(h * 0.6)
        left = center_x - region_w // 2
        top = center_y - region_h // 2
        return frame[top : top + region_h, left : left + region_w], left, top

    def add_emoji_to_frame(self, frame, emoji_path, position):
        """Adds an emoji to the frame at the specified position."""
        emoji_img = Image.open(emoji_path).convert("RGBA")
        pil_frame = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).convert(
            "RGBA"
        )
        emoji_img = emoji_img.resize(self.EMOJI_SIZE, None)
        pil_frame.paste(emoji_img, position, emoji_img)
        return cv2.cvtColor(np.array(pil_frame), cv2.COLOR_RGBA2BGR)

    def display_image(self, image_label, frame):
        """Displays an image on the label."""
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        q_img = QImage(image.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        scaled_pixmap = pixmap.scaled(
            image_label.width(),
            image_label.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        image_label.setPixmap(scaled_pixmap)

    def annotate_frame(self, frame, results):
        """Annotates the frame with bounding boxes and labels."""
        for result in results:
            region = result[0]["region"]
            x, y, w, h = region["x"], region["y"], region["w"], region["h"]

            # Draw the bounding box
            cv2.rectangle(frame, (x, y), (x + w, y + h), (110,188,62), 3)
            emotion = result[0]["dominant_emotion"]
            age = result[0]["age"]
            gender = result[0]["dominant_gender"]

            self.draw_speech_bubble(frame, x, y, w, h, age, emotion, gender)
            
            # Add emoji
            if emotion in self.EMOTION_EMOJI_MAP:
                emoji_path = self.EMOTION_EMOJI_MAP[emotion]
                frame = self.add_emoji_to_frame(frame, emoji_path, (x, y + 120))

        return frame

    def draw_speech_bubble(self, frame, x, y, w, h, age, emotion, gender):
        # Define bubble dimensions
        bubble_width = 150
        bubble_height = 70
        bubble_padding = 10
        bubble_color = (234, 20, 140)  # Light pink
        text_color = (255, 255, 255)    # White

        # Calculate bubble position
        bubble_x = x
        bubble_y = y - bubble_height - bubble_padding
        if bubble_y < 0:  # Ensure the bubble is within frame bounds
            bubble_y = y + h + bubble_padding

        # Draw the rectangle for the bubble
        cv2.rectangle(
            frame,
            (bubble_x, bubble_y),
            (bubble_x + bubble_width, bubble_y + bubble_height),
            bubble_color,
            cv2.FILLED
        )

        # Draw the triangular part of the speech bubble (tail)
        triangle_points = [
            (x + w // 2, y),                       # Top middle of the detected face
            (bubble_x + bubble_width // 2 - 10, bubble_y + bubble_height),  # Bottom left of the bubble
            (bubble_x + bubble_width // 2 + 10, bubble_y + bubble_height)   # Bottom right of the bubble
        ]
        cv2.drawContours(frame, [np.array(triangle_points, np.int32)], 0, bubble_color, cv2.FILLED)

        # Draw text inside the bubble
        cv2.putText(
            frame,
            f"Age: {age}",
            (bubble_x + bubble_padding, bubble_y + 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            text_color,
            2
        )
        cv2.putText(
            frame,
            f"Emotion: {emotion}",
            (bubble_x + bubble_padding, bubble_y + 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            text_color,
            2
        )
        cv2.putText(
            frame,
            f"Gender: {gender}",
            (bubble_x + bubble_padding, bubble_y + 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            text_color,
            2
        )

    def release_resources(self):
        """Releases the camera."""
        self.cap.release()
