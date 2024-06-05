import cv2
from deepface import DeepFace
import sqlite3
import datetime
import os
from PIL import Image, ImageFont, ImageDraw
import numpy as np
import emoji

# Setup database connection
conn = sqlite3.connect('emotions.db')
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS emotions (
        id INTEGER PRIMARY KEY,
        emotion TEXT,
        age TEXT,
        gender TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()

# Check and create directory for captured images
if not os.path.exists('captured_images'):
    os.makedirs('captured_images')

# Load face cascade classifier
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Start capturing video
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

# Emotion to Emoji mapping
emotion_emoji_map = {
    'angry': 'emojis/angry.png',
    'fear': 'emojis/fear.png',
    'happy': 'emojis/happy.png',
    'sad': 'emojis/sad.png',
    'surprise': 'emojis/surprise.png',
    'neutral': 'emojis/neutral_smile.png' 
}

def add_emoji_to_frame(frame, emoji_path, position):
    emoji_img = Image.open(emoji_path).convert("RGBA")
    pil_frame = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).convert("RGBA")

    emoji_img = emoji_img.resize((50, 50), None)
    pil_frame.paste(emoji_img, position, emoji_img)

    return cv2.cvtColor(np.array(pil_frame), cv2.COLOR_RGBA2BGR)

while True:
    ret, frame = cap.read()

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

conn.close()
