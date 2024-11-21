from flask import Flask, request, jsonify
from flask_cors import CORS
import face_recognition
import cv2
import numpy as np
import base64
import os
import mysql.connector
from datetime import datetime
from deepface import DeepFace
app = Flask(__name__)
CORS(app)

EMPLOYEE_DIR = "../employees/"
TEMP_DIR = "../temp_photos/"

# Tạo thư mục tạm nếu chưa tồn tại
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# Kết nối MySQL
def connect_to_db():
    return mysql.connector.connect(
        host="svr-freehost.vinahost.vn",
        user="oamtyxks_duong",
        password="Duong3001@",
        database="oamtyxks_membershiphp"
    )

# Tải dữ liệu khuôn mặt từ thư mục
def load_employee_faces():
    employee_faces = []
    employee_names = []

    for folder in os.listdir(EMPLOYEE_DIR):
        folder_path = os.path.join(EMPLOYEE_DIR, folder)
        if os.path.isdir(folder_path):
            for file in os.listdir(folder_path):
                if file.endswith((".jpg", ".jpeg")):
                    image_path = os.path.join(folder_path, file)
                    image = face_recognition.load_image_file(image_path)
                    encoding = face_recognition.face_encodings(image)
                    if encoding:
                        employee_faces.append(encoding[0])
                        employee_names.append(folder)
    return employee_faces, employee_names

employee_faces, employee_names = load_employee_faces()

# Ghi nhật ký chấm công
def log_attendance(employee_name, attendance_type):
    conn = connect_to_db()
    cursor = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(
        "INSERT INTO attendance_logs (employee_name, attendance_type, timestamp) VALUES (%s, %s, %s)",
        (employee_name, attendance_type, timestamp)
    )
    conn.commit()
    conn.close()

# Route API: Kiểm tra hoạt động
@app.route('/')
def home():
    return jsonify({"message": "API đang hoạt động!"}), 200

# Route API: Nhận diện khuôn mặt
# Thay thế logic nhận diện trong route /recognize
@app.route('/recognize', methods=['POST'])
def recognize():
    try:
        data = request.json
        img_data = base64.b64decode(data['image'])
        attendance_type = data['type']

        np_img = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

        # Nhận diện bằng DeepFace
        result = DeepFace.find(img_path=img, db_path=EMPLOYEE_DIR, enforce_detection=False)
        if len(result) > 0:
            employee_name = result[0]['identity']
            log_attendance(employee_name, attendance_type)
            return jsonify({"status": "success", "message": f"{employee_name} đã {'chấm công vào' if attendance_type == 'in' else 'chấm công ra'}!"}), 200

        return jsonify({"status": "fail", "message": "Không tìm thấy khuôn mặt trùng khớp."}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Route API: Thêm nhân viên
@app.route('/add-employee', methods=['POST'])
def add_employee():
    try:
        data = request.json
        name = data['name']
        employee_id = data['employeeId']
        photos = data['photos']

        # Tạo thư mục nhân viên nếu chưa tồn tại
        employee_folder = os.path.join(EMPLOYEE_DIR, name)
        if not os.path.exists(employee_folder):
            os.makedirs(employee_folder)

        # Lưu ảnh
        for i, photo in enumerate(photos):
            img_data = base64.b64decode(photo.split(",")[1])
            with open(os.path.join(employee_folder, f"{name}_{employee_id}_{i+1}.jpg"), "wb") as f:
                f.write(img_data)

        # Thêm vào cơ sở dữ liệu
        conn = connect_to_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO employees (name, employee_id) VALUES (%s, %s)", (name, employee_id))
        conn.commit()
        conn.close()

        return jsonify({"status": "success", "message": f"Nhân viên {name} đã được thêm thành công!"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
