import os
import cv2
import face_recognition
import numpy as np
import pandas as pd
import bcrypt
from datetime import datetime
from threading import Thread, Lock
from flask import Flask, request, session, jsonify, render_template, Response, redirect, url_for , send_file
import requests
from flask_sqlalchemy import SQLAlchemy
from twilio.rest import Client



account_sid = 'AC9717e23a8b6a334f668fc0728dc6ed66' 
auth_token = 'cd7d11d79d0153dceca774b6fa759629'   
twilio_sms_number = '+13072125079'                 

client = Client(account_sid, auth_token)
app = Flask(__name__)
app.secret_key = "zaeem"  


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///teachers.db'
db = SQLAlchemy(app)


class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(50), nullable=False)


with app.app_context():
    db.create_all()


video_capture = cv2.VideoCapture(0)
frame = None
lock = Lock()
subject = "General"

photo_folder = r'C:\Users\zaeem\Downloads\TEst]\attendance-system\attendance-system\photo_folder'
attendance_folder = r'C:\Users\zaeem\Downloads\TEst]\attendance-system\attendance-system\Attendance'
os.makedirs(photo_folder, exist_ok=True)
os.makedirs(attendance_folder, exist_ok=True)
# Add near your video capture thread
def capture_frames():
    global frame, lock
    while True:
        ret, temp_frame = video_capture.read()
        if not ret:
            print("Camera error")
            break

        # Low-light detection (new)
        gray = cv2.cvtColor(temp_frame, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray)
        LOW_LIGHT_THRESHOLD = 50  # Adjust as needed (0-255)

        if brightness < LOW_LIGHT_THRESHOLD:
            with lock:
                cv2.putText(temp_frame, "LOW LIGHT! ADJUST LIGHTING", (50, 50),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

known_face_encodings = []
known_face_names = []
@app.route('/live')
@app.route('/live')
def live_page():
    subject = request.args.get('subject', 'Unknown')
    return render_template('live.html', subject=subject)


for file in os.listdir(photo_folder):
    if file.endswith(("jpg", "png", "jpeg")):
        img_path = os.path.join(photo_folder, file)
        img = face_recognition.load_image_file(img_path)
        encoding = face_recognition.face_encodings(img)

        if encoding:
            known_face_encodings.append(encoding[0])
            known_face_names.append(os.path.splitext(file)[0])
        else:
            print(f"⚠ No face detected in {file}. Skipping...")

if os.listdir(photo_folder):
    for file in os.listdir(photo_folder):
        if file.endswith(("jpg", "png", "jpeg")):
            img_path = os.path.join(photo_folder, file)
            img = face_recognition.load_image_file(img_path)
            encoding = face_recognition.face_encodings(img)

            if encoding:
                known_face_encodings.append(encoding[0])
                known_face_names.append(os.path.splitext(file)[0])
            else:
                print(f"⚠ No face detected in {file}. Skipping...")


if not video_capture.isOpened():
    print("❌ Error: Camera failed to initialize.")
    exit(1)

def capture_frames():
    global frame, lock, subject  
    while True:
        ret, temp_frame = video_capture.read()
        if not ret:
            print("❌ Camera issue: Failed to read frame.")
            break

        rgb_frame = cv2.cvtColor(temp_frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        print(f"Detected {len(face_locations)} faces.")  

        for face_encoding, face_location in zip(face_encodings, face_locations):
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.5)
            name = "Unknown"

            if True in matches:
                best_match_index = np.argmin(face_recognition.face_distance(known_face_encodings, face_encoding))
                name = known_face_names[best_match_index]
                print(f"Detected: {name}") 

                mark_attendance(name, subject)  
                print(f"✅ {name} marked as Present for {subject}") 

            top, right, bottom, left = face_location
            cv2.rectangle(temp_frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(temp_frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        with lock:
            frame = temp_frame

video_thread = Thread(target=capture_frames)
video_thread.daemon = True
video_thread.start()

def generate_frames():
    global frame, lock
    while True:
        with lock:
            if frame is None:
                continue

            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
def calculate_leaderboard():
    current_month = datetime.now().strftime("%m-%Y")
    students = [os.path.splitext(f)[0] for f in os.listdir(photo_folder) 
               if f.endswith(('jpg', 'png', 'jpeg'))]
    
    attendance_data = []
    
    for student in students:
        present_counts = {}
        total_possible = 0
        
        # Check all attendance files for this month
        for subject in ['DCN', 'JPR', 'EES', 'PWP', 'MIC']:
            subject_files = [f for f in os.listdir(attendance_folder) 
                           if f.startswith(f"{subject}_attendance") 
                           and current_month in f]
            
            present_count = 0
            for file in subject_files:
                df = pd.read_excel(os.path.join(attendance_folder, file))
                present_count += df[df["Student Name"] == student]["Attendance"].count()
            
            present_counts[subject] = present_count
            total_possible += len(subject_files)
        
        # Calculate overall percentage
        total_present = sum(present_counts.values())
        percentage = (total_present / total_possible * 100) if total_possible > 0 else 0
        
        attendance_data.append({
            "Name": student,
            **present_counts,
            "Total Present": total_present,
            "Percentage": round(percentage, 1)
        })
    
    # Sort by total present (descending)
    attendance_data.sort(key=lambda x: x["Total Present"], reverse=True)
    
    # Add rankings
    for i, student in enumerate(attendance_data, 1):
        student["Rank"] = i
    
    return attendance_data
def send_parent_email(student_name, subject_name):
    try:
        response = requests.post(
            'http://localhost:8000/mailer.php',
            json={
                'student': student_name,
                'subject': subject_name
            },
            headers={'Content-Type': 'application/json'}
        )
        return response.json().get('success', False)
    except Exception as e:
        print(f"Email system error: {str(e)}")
        return False
def mark_attendance(name, subject):
    subject = subject.upper()  
    time_now = datetime.now().strftime("%H:%M:%S")
    today_date = datetime.now().strftime("%d-%m-%Y")
    excel_path = os.path.join(attendance_folder, f"{subject}_attendance_{today_date}.xlsx")

    # Initialize DataFrame
    if os.path.exists(excel_path):
        df = pd.read_excel(excel_path)
    else:
        df = pd.DataFrame(columns=["Student Name", "Attendance", "Time"])

    # Check for duplicates
    if name in df["Student Name"].values:
        print(f"⚠ {name} already marked present for {subject}. Skipping...")
        return False

    # Add new entry
    new_entry = pd.DataFrame([[name, "Present", time_now]], 
                           columns=["Student Name", "Attendance", "Time"])
    df = pd.concat([df, new_entry], ignore_index=True)
    
    try:
        df.to_excel(excel_path, index=False)
        print(f"✅ {name} marked as Present for {subject} at {time_now}")
        
        # Send email notification
        try:
            response = requests.post(
                'http://localhost:8000/mailer.php',
                json={'student': name, 'subject': subject},
                headers={'Content-Type': 'application/json'}
            )
            if response.json().get('success'):
                print(f"📧 Email sent to {name}'s parent")
            else:
                print(f"⚠ Email failed for {name}")
        except Exception as e:
            print(f"🚨 Email system error: {str(e)}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error saving attendance: {str(e)}")
        return False

@app.route('/')
def index():
    global camera_active
    camera_active = False  
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    teacher = Teacher.query.filter_by(username=session['username']).first()
    if not teacher:
        return redirect(url_for('login'))

    subject = teacher.subject.upper()
    today_date = datetime.now().strftime("%d-%m-%Y")
    excel_path = os.path.join(attendance_folder, f"{subject}_attendance_{today_date}.xlsx")

    # Get students for dropdown
    students = [os.path.splitext(file)[0] for file in os.listdir(photo_folder) 
               if file.endswith(('jpg', 'png', 'jpeg'))]

    # Get attendance records
    if os.path.exists(excel_path):
        df = pd.read_excel(excel_path)
        records = df.to_dict(orient="records")
    else:
        records = []

    return render_template(
        'dashboard.html',
        username=teacher.username,
        subject=subject,
        records=records
        
    )
@app.route('/live')
def live():
    global subject  
    subject = request.args.get('subject', default='General', type=str).upper()  
    print(f"Subject selected: {subject}")  
    
    
    teacher = Teacher.query.filter_by(subject=subject).first()
    
    if not teacher:
        return "Invalid subject selected.", 400

    return render_template('live.html', subject=subject, teacher_name=teacher.username)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html') 

    data = request.json  
    username = data['username']
    password = data['password']

    
    if Teacher.query.filter_by(username=username).first():
        return jsonify({'status': 'error', 'message': 'Username already exists'})

    
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    if "subject" not in data or not data["subject"]:
        return jsonify({'status': 'error', 'message': 'Please select a subject.'})

    new_teacher = Teacher(username=username, password=hashed_password, subject=data["subject"])

    db.session.add(new_teacher)
    db.session.commit()

    return jsonify({'status': 'success', 'message': 'Signup successful', 'redirect': '/login'})
@app.route('/debug_db')
def debug_db():
    teachers = Teacher.query.all()
    if not teachers:
        return jsonify({'message': 'No users found in the database.'})
    return jsonify([{"id": t.id, "username": t.username, "subject": t.subject} for t in teachers])


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')  

    data = request.json
    username = data['username']
    password = data['password']

    teacher = Teacher.query.filter_by(username=username).first()

    if teacher and bcrypt.checkpw(password.encode('utf-8'), teacher.password.encode('utf-8')):
        session['username'] = username
        return jsonify({'status': 'success', 'message': 'Login successful', 'redirect': '/dashboard'})

    return jsonify({'status': 'error', 'message': 'Invalid credentials'})
@app.route('/get_records')
def get_records():
    print(f"Loading attendance records from: {attendance_folder}")
    today_date = datetime.now().strftime("%d-%m-%Y")
    records = []
    
    for file in os.listdir(attendance_folder):
        if today_date in file:  
            df = pd.read_excel(os.path.join(attendance_folder, file))
            records.extend(df.to_dict(orient="records"))

    return jsonify(records)
@app.route('/leaderboard')
def leaderboard():
    leaderboard_data = calculate_leaderboard()
    return render_template('leaderboard.html', leaderboard=leaderboard_data)

@app.route('/download_leaderboard')
def download_leaderboard():
    leaderboard_data = calculate_leaderboard()
    df = pd.DataFrame(leaderboard_data)
    
    # Save to Excel in memory (no temporary file)
    from io import BytesIO
    excel_buffer = BytesIO()
    df.to_excel(excel_buffer, index=False)
    excel_buffer.seek(0)  # Reset buffer position
    
    # Send as download
    return send_file(
        excel_buffer,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='leaderboard.xlsx'
    )
@app.route('/logout')
def logout():
    session.pop('username', None)   
    return redirect(url_for('index'))

@app.route('/get_status')
def get_status():
    return jsonify({'message': 'Waiting for face detection...'})
@app.route('/add_student', methods=['POST'])
def add_student():
    if 'photo' not in request.files or 'name' not in request.form:
        return jsonify({'success': False, 'message': 'No file or name provided'})

    photo = request.files['photo']
    student_name = request.form['name'].strip()

    if photo.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'})

    if not allowed_file(photo.filename):
        return jsonify({'success': False, 'message': 'Invalid file type (only JPG, PNG, JPEG allowed)'})

    # Save the photo with the student's name as filename
    filename = f"{student_name}.jpg"  # You can also keep original extension
    save_path = os.path.join(photo_folder, filename)
    photo.save(save_path)

    # Reload known faces (optional, can be done on next startup)
    global known_face_encodings, known_face_names
    img = face_recognition.load_image_file(save_path)
    encoding = face_recognition.face_encodings(img)
    
    if encoding:
        known_face_encodings.append(encoding[0])
        known_face_names.append(student_name)
    else:
        return jsonify({'success': False, 'message': 'No face detected in the image!'})

    return jsonify({'success': True, 'message': f'Student {student_name} added successfully!'})

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png'}


DEFAULT_PASSWORD = "student123"

PREMADE_TEACHERS = [
    {"username": "Sandeep Kholambe", "subject": "JPR"},
    {"username": "Priyanka Khairnar PWP", "subject": "PWP"},
    {"username": "Priyanka Khairnar MIC", "subject": "MIC"},
    {"username": "Ugale Deepak", "subject": "DCN"},
    {"username": "Mhaske Jyoti", "subject": "EES"},
]


def add_premade_teachers():
    with app.app_context():
        for teacher in PREMADE_TEACHERS:
            existing_teacher = Teacher.query.filter_by(username=teacher["username"]).first()
            if not existing_teacher:
                hashed_password = bcrypt.hashpw(DEFAULT_PASSWORD.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                new_teacher = Teacher(username=teacher["username"], password=hashed_password, subject=teacher["subject"])
                db.session.add(new_teacher)
        db.session.commit()


add_premade_teachers()
if __name__ == '__main__':
    app.run(debug=True)
    
@app.route('/get_light_level')
def get_light_level():
    global frame  # Make sure you have this global variable declared
    
    if frame is None:
        return jsonify({"error": "Camera not initialized"}), 500
    
    try:
        # Convert to grayscale and calculate brightness
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness = float(np.mean(gray))
        
        # Debug print (view in terminal)
        print(f"Current brightness: {brightness}")
        
        return jsonify({
            "brightness": brightness,
            "status": "success"
        })
    except Exception as e:
        print(f"Light detection error: {str(e)}")
        return jsonify({"error": str(e)}), 500