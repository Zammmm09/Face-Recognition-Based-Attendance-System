import cv2
import face_recognition
import os
import numpy as np
import pandas as pd
from datetime import datetime


photo_folder = ('C:/Users/ashaz/Desktop/VS-code/Attendace Face Recognition/attendance-system/photo_folder')
attendance_folder = ('C:/Users/ashaz/Desktop/VS-code/Attendace Face Recognition/attendance-system/Attendance')


os.makedirs(attendance_folder, exist_ok=True)


today_date = datetime.now().strftime("%Y-%m-%d")
excel_path = os.path.join(attendance_folder, f"{today_date}.xlsx")


known_face_encodings = []
known_face_names = []

for file in os.listdir(photo_folder):
    if file.endswith(("jpg", "png", "jpeg")):
        img_path = os.path.join(photo_folder, file)
        img = face_recognition.load_image_file(img_path)
        encoding = face_recognition.face_encodings(img)
        
        if encoding:
            known_face_encodings.append(encoding[0])
            known_face_names.append(os.path.splitext(file)[0]) 
        else:
            print(f"Warning: No face detected in {file}. Skipping...")

def mark_attendance(name):
    time_now = datetime.now().strftime("%H:%M:%S")

 
    if os.path.exists(excel_path):
        df = pd.read_excel(excel_path)
    else:
        df = pd.DataFrame(columns=["Student Name", "Attendance", "Time"])
    if name not in df["Student Name"].values:
        new_entry = pd.DataFrame([[name, "Present", time_now]], columns=["Student Name", "Attendance", "Time"])
        df = pd.concat([df, new_entry], ignore_index=True)

        
        df.to_excel(excel_path, index=False)
        print(f"✅ {name} marked as Present at {time_now}")

video_capture = cv2.VideoCapture(0)

while True:
    ret, frame = video_capture.read()
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    attendance_message = "No student detected"

    for face_encoding, face_location in zip(face_encodings, face_locations):
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        name = "Unknown"

        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
        best_match_index = np.argmin(face_distances) if face_distances.size > 0 else None

        if best_match_index is not None and matches[best_match_index]:
            name = known_face_names[best_match_index]
            attendance_message = f"{name} Present"  
            mark_attendance(name)  

        top, right, bottom, left = face_location
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    overlay = frame.copy()
    cv2.rectangle(overlay, (0, frame.shape[0] - 50), (frame.shape[1], frame.shape[0]), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
    cv2.putText(frame, attendance_message, (50, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("Face Recognition Attendance", frame)

    # Press 'q' to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video_capture.release()
cv2.destroyAllWindows()
