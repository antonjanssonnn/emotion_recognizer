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
        faces = self.face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=10, minSize=(30, 30))

        results = []
        for (x, y, w, h) in faces:
            rgb_frame = cv2.cvtColor(gray_frame, cv2.COLOR_GRAY2RGB)
            try:
                face_roi = rgb_frame[y:y + h, x:x + w]
                if face_roi.size > 0:
                    result = DeepFace.analyze(face_roi, actions=['emotion', 'age', 'gender'], enforce_detection=False)
                    results.append(result)
            except Exception as e:
                print(f"Failed to analyze face: {e}")
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


'''
# Load face cascade classifier
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
if face_cascade.empty():
    print("Failed to load cascade classifier")
    exit()

# Start capturing video
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():
    cap.open(0)  # Try to forcibly open the camera at index 1

# Check if camera opened successfully
if not cap.isOpened():
    print("Error: Could not open video capture device.")
    exit()
'''

'''
def add_emoji_to_frame(frame, emoji_path, position):
    emoji_img = Image.open(emoji_path).convert("RGBA")
    pil_frame = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).convert("RGBA")

    emoji_img = emoji_img.resize((50, 50), None)
    pil_frame.paste(emoji_img, position, emoji_img)

    return cv2.cvtColor(np.array(pil_frame), cv2.COLOR_RGBA2BGR)

def print_database_contents():
    # Connect to the database
    conn = sqlite3.connect('emotions.db')
    c = conn.cursor()

    # Query all data
    c.execute('SELECT * FROM emotions')
    rows = c.fetchall()

    # Print each row
    for row in rows:
        print(row)

    # Close the database connection
    conn.close()

while True:
    ret, frame = cap.read()

    if not ret or frame is None:
        print("Failed to grab frame")
        continue  # Skip this iteration of the loop if the frame wasn't grabbed correctly

    # Display the frame
    cv2.imshow('Press Space to Capture', frame)

    # Wait for space bar to capture image
    if cv2.waitKey(1) & 0xFF == ord(' '):
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rgb_frame = cv2.cvtColor(gray_frame, cv2.COLOR_GRAY2RGB)
        faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        for (x, y, w, h) in faces:
            face_roi = rgb_frame[y:y + h, x:x + w]
            result = DeepFace.analyze(face_roi, actions=['emotion', 'age', 'gender'], enforce_detection=False)

            emotion = result[0]['dominant_emotion']  # Correctly accessing dominant emotion
            age = result[0]['age']
            gender = result[0]['dominant_gender']

            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 0), 1)
            cv2.putText(frame, f'Age: {age}', (x, y + h + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (203, 192, 255), 1)
            cv2.putText(frame, f'Emotion: {emotion}', (x, y + h + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (203, 192, 255), 1)
            cv2.putText(frame, f'Gender: {gender}', (x, y + h + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (203, 192, 255), 1)

            # Insert data into the database
            c.execute('INSERT INTO emotions (emotion, age, gender) VALUES (?, ?, ?)', (emotion, str(age), gender))
            conn.commit()

            # Add emoji to frame
            if emotion in emotion_emoji_map:
                emoji_path = emotion_emoji_map[emotion]
                frame = add_emoji_to_frame(frame, emoji_path, (x, y - 40))

            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            cv2.imwrite(f'captured_images/{timestamp}.png', frame)

        cv2.imshow('Captured Image', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

# Calculate and print the most frequent emotion
c.execute("SELECT emotion, COUNT(emotion) FROM emotions GROUP BY emotion ORDER BY COUNT(emotion) DESC LIMIT 1")
most_frequent_emotion = c.fetchone()
if most_frequent_emotion:
    print(f"The dominant emotion detected is: {most_frequent_emotion[0]}")
else:
    print("No emotions were detected.")

print_database_contents()

conn.close()
'''