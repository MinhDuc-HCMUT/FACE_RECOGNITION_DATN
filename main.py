import cv2
import numpy as np
import sqlite3
import os
import serial
import time  # Thư viện để quản lý thời gian
from datetime import datetime
from PIL import Image

# Initialize face recognizer
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read(r'D:\DATN\DATN_FINAL_main\FACE_RECOGNITION\recognizer\trainingData.yml')

def insertOrUpdate(id, name):
    conn = sqlite3.connect(r'D:\DATN\DATN_FINAL_main\FACE_RECOGNITION\data.db')
    query = "SELECT * FROM people WHERE ID=" + str(id)
    cursor = conn.execute(query)
    isRecordExist = 0

    for row in cursor:
        isRecordExist = 1
    if isRecordExist == 0:
        query = "INSERT INTO people(ID,Name) VALUES(" + str(id) + ",'" + str(name) + "')"
    else:
        query = "UPDATE people SET Name='" + str(name) + "' WHERE ID=" + str(id)
    conn.execute(query)
    conn.commit()
    conn.close()

# Hàm xử lý thêm gương mặt mới
def addFace(id, name, ser, cap, face_cascade):
    sampleNum = 0  # Đếm số lượng ảnh đã capture

    while True:
        # Đọc dữ liệu từ webcam
        ret, frame = cap.read()
        if not ret:
            print("Không thể truy cập webcam")
            break

        # Chuyển đổi sang ảnh xám
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Nhận diện khuôn mặt
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        # Vẽ hình chữ nhật xung quanh các khuôn mặt và lưu ảnh
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Tạo thư mục nếu chưa tồn tại
            if not os.path.exists('dataSet'):
                os.makedirs('dataSet')

            # Lưu ảnh vào thư mục
            sampleNum += 1
            cv2.imwrite(f'dataSet/User.{id}.{sampleNum}.jpg', gray[y: y + h, x: x + w])

        # Hiển thị khung hình
        cv2.putText(frame, "COLLECTING NEW FACES DATA", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.imshow('frame', frame)
        cv2.waitKey(1)

        # Kết thúc khi đủ 500 ảnh hoặc hết thời gian
        if sampleNum >= 500:  # Timeout sau 60 giây
            break

    # Kiểm tra nếu đã capture đủ ảnh
    if sampleNum >= 500:
        print(f"Đã capture {sampleNum} ảnh cho ID: {id}. Bắt đầu huấn luyện lại mô hình...")
        trainRecognizer()  # Huấn luyện lại mô hình
        ser.write(b"True")  # Gửi tín hiệu thành công qua serial
        print("Đã gửi: True")
    else:
        print("Capture không đủ ảnh hoặc hết thời gian!")
        ser.write(b"False")  # Gửi tín hiệu thất bại qua serial
        print("Đã gửi: False")

def checkInDatabase(id, name):
    conn = sqlite3.connect("D:/DATN/DATN_FINAL_main/FACE_RECOGNITION/data.db")
    query = "SELECT * FROM people WHERE ID=? AND Name=?"
    cursor = conn.execute(query, (id, name))
    result = cursor.fetchone()  # Lấy một kết quả
    conn.close()
    return result is not None  # Trả về True nếu có dữ liệu, False nếu không

def deleteData(id, name):
    try:
        # Xóa ảnh của user trong thư mục dataSet
        user_images_path = 'dataSet'  # Thư mục chứa tất cả ảnh của người dùng
        # Duyệt qua tất cả các tệp trong thư mục 'dataSet'
        deleted = False
        for filename in os.listdir(user_images_path):
            if filename.startswith(f"User.{id}."):
                file_path = os.path.join(user_images_path, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)  # Xóa tệp ảnh
                    deleted = True  # Đánh dấu nếu có tệp bị xóa
        if deleted:
            print(f"Đã xóa tất cả ảnh của User.{id}")
        else:
            print(f"Không tìm thấy ảnh của User.{id} để xóa.")

        # Xóa bản ghi trong database
        conn = sqlite3.connect("D:/DATN/DATN_FINAL_main/FACE_RECOGNITION/data.db")
        query = "DELETE FROM people WHERE ID=? AND Name=?"
        conn.execute(query, (id, name))
        conn.commit()
        conn.close()

        print(f"Đã xóa dữ liệu của User.{id} trong cơ sở dữ liệu.")
        return True  # Trả về True nếu xóa thành công
    except Exception as e:
        print(f"Lỗi khi xóa dữ liệu: {e}")
        return False  # Trả về False nếu có lỗi


# Hàm xóa tất cả dữ liệu người dùng và ảnh, tạo tệp mô hình rỗng (không thực tế)
def deleteAllData():
    try:
        # Xóa tất cả ảnh .jpg trong thư mục dataSet
        user_images_path = 'dataSet'  # Thư mục chứa tất cả ảnh của người dùng
        deleted = False
        for filename in os.listdir(user_images_path):
            if filename.endswith(".jpg"):  # Chỉ xóa các ảnh .jpg
                file_path = os.path.join(user_images_path, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)  # Xóa tệp ảnh
                    deleted = True  # Đánh dấu nếu có tệp bị xóa
        if deleted:
            print("Đã xóa tất cả ảnh trong thư mục dataSet.")
        else:
            print("Không tìm thấy ảnh để xóa.")

        # Xóa tất cả bản ghi trong bảng people
        conn = sqlite3.connect("D:/DATN/DATN_FINAL_main/FACE_RECOGNITION/data.db")
        query = "DELETE FROM people"
        conn.execute(query)
        conn.commit()
        conn.close()

        print("Đã xóa tất cả dữ liệu trong cơ sở dữ liệu.")

        # Tạo tệp trainingData.yml rỗng ( không thực tế)
        createFakeTrainingData()

        return True  # Trả về True nếu xóa thành công
    except Exception as e:
        print(f"Lỗi khi xóa dữ liệu: {e}")
        return False  # Trả về False nếu có lỗi


# Hàm tạo tệp trainingData.yml rỗng (dữ liệu không hợp lệ)
def createFakeTrainingData():
    # Tạo dữ liệu rỗng (ID = -1, không có ảnh thực tế)
    faces = [np.zeros((100, 100), dtype=np.uint8)]  # Ảnh trắng kích thước 100x100
    IDs = [-1]  # ID không tực tế

    # Huấn luyện mô hình với dữ liệu rỗng ( không thực tế)
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(faces, np.array(IDs))

    # Lưu mô hình giả vào tệp trainingData.yml
    if not os.path.exists('recognizer'):
        os.makedirs('recognizer')

    recognizer.save('recognizer/trainingData.yml')
    print("Đã tạo tệp trainingData.yml rỗng (không thực tế)!")


# Hàm lấy ảnh và ID từ thư mục dataSet
def getImageWithID(path):
    imagePaths = [os.path.join(path, f) for f in os.listdir(path)]
    faces = []
    IDs = []
    for imagePath in imagePaths:
        if not imagePath.endswith(".jpg"):  # Skip non-image files
            continue
        faceImg = Image.open(imagePath).convert('L')
        faceNp = np.array(faceImg, 'uint8')
        print(faceNp)
        Id = int(imagePath.split('\\')[1].split('.')[1])
        faces.append(faceNp)
        IDs.append(Id)
        cv2.imshow('training', faceNp)
        cv2.waitKey(10)
    return faces, IDs


# Hàm huấn luyện lại mô hình nhận diện gương mặt
def trainRecognizer():
    # Đọc dữ liệu từ thư mục 'dataSet'
    faces, IDs = getImageWithID('dataSet')

    # Huấn luyện lại mô hình nhận diện
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(faces, np.array(IDs))

    # Lưu lại mô hình nhận diện
    if not os.path.exists('recognizer'):
        os.makedirs('recognizer')

    recognizer.save('recognizer/trainingData.yml')
    print("Huấn luyện lại mô hình thành công và đã lưu!")

def getProfile(id):
    conn = sqlite3.connect("D:/DATN/DATN_FINAL_main/FACE_RECOGNITION/data.db")
    query = "SELECT * FROM people WHERE ID=" + str(id)
    cursor = conn.execute(query)
    profile = None
    for row in cursor:
        profile = row
    conn.close()
    return profile

def recognizeFace(ser, cap, face_cascade, recognizer):
    countdown = 5
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1
    color = (0, 0, 255)
    thickness = 2

    while True:
        start_time = time.time()
        recognized = False

        while True:
            if ser.in_waiting > 0:
                return  # Exit to handle serial data

            ret, frame = cap.read()
            if not ret:
                print("Không thể truy cập webcam")
                return

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)

            if len(faces) == 0:
                height, width = frame.shape[:2]
                text1 = "Please place your face"
                text2 = "in the center of the screen"

                text1_size = cv2.getTextSize(text1, font, font_scale, thickness)[0]
                text2_size = cv2.getTextSize(text2, font, font_scale, thickness)[0]

                text1_x = (width - text1_size[0]) // 2
                text1_y = (height // 2) - 20
                text2_x = (width - text2_size[0]) // 2
                text2_y = (height // 2) + 20

                cv2.putText(frame, text1, (text1_x, text1_y), font, font_scale, color, thickness)
                cv2.putText(frame, text2, (text2_x, text2_y), font, font_scale, color, thickness)
                start_time = time.time()  # Reset countdown if no face is detected

            else:
                for (x, y, w, h) in faces:
                    roi_gray = gray[y:y + h, x: x + w]
                    id, confidence = recognizer.predict(roi_gray)

                    if confidence < 50:
                        profile = getProfile(id)
                        confidence_text = "  {0}%".format(round(100 - confidence))
                        if profile is not None:
                            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                            cv2.putText(frame, str(profile[1]), (x + 10, y + h + 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                            cv2.putText(frame, confidence_text, (x - 30, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                            recognized = True
                            recognized_id = id  # Store the recognized ID
                            break  # Exit the loop if at least one face is recognized correctly
                    else:
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                        cv2.putText(frame, "Unknown", (x + 10, y + h + 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

                elapsed_time = time.time() - start_time
                remaining_time = countdown - int(elapsed_time)
                cv2.putText(frame, f"Time left: {remaining_time}s", (10, 30), font, font_scale, (255, 255, 255), thickness)

                if elapsed_time >= countdown:
                    break  # Exit the loop if countdown is complete

            cv2.imshow('frame', frame)
            if cv2.waitKey(1) == ord('q'):
                return

        if recognized:
            ser.write(f"Y.{recognized_id}".encode())
            print(f"Đã gửi: Y.{recognized_id}")
            cv2.putText(frame, "RECOGNIZE SUCCESSFULLY", (50, 100), font, font_scale, (0, 255, 0), thickness)  # Adjusted position
        else:
            ser.write(b"NO")
            print("Đã gửi: NO")
            cv2.putText(frame, "WRONG DATA - CANNOT RECOGNIZE", (50, 100), font, font_scale, (0, 0, 255), thickness)  # Adjusted position

        cv2.imshow('frame', frame)
        cv2.waitKey(2000)  # Display the result for 2 seconds

def reloadRecognizer():
    global recognizer
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(r'D:\DATN\DATN_FINAL_main\FACE_RECOGNITION\recognizer\trainingData.yml')

def insertIntoLog(method, identification, status):
    conn = sqlite3.connect(r'D:\DATN\DATN_FINAL_main\FACE_RECOGNITION\data.db')
    cursor = conn.execute("SELECT MAX(STT) FROM monitor")
    max_stt = cursor.fetchone()[0]
    if max_stt is None:
        max_stt = 0
    stt = max_stt + 1
    current_time = datetime.now().strftime("%H:%M:%S")
    current_date = datetime.now().strftime("%d:%m:%Y")
    query = "INSERT INTO monitor(STT, Method, Identification, Status, Time, Day) VALUES(?, ?, ?, ?, ?, ?)"
    conn.execute(query, (stt, method, identification, status, current_time, current_date))
    conn.commit()
    conn.close()

# Cấu hình serial
serial_port = "COM9"  # Thay bằng cổng serial của bạn
baud_rate = 115200
ser = serial.Serial(serial_port, baud_rate, timeout=1)

# Thư viện nhận diện gương mặt
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# Khởi động webcam với biến cap
cap = cv2.VideoCapture(0)

sampleNum = 0
id = None
name = None

while True:
    if ser.in_waiting > 0:
        serial_data = ser.readline().decode('utf-8').strip()
        print(f"Dữ liệu từ serial: {serial_data}")

        if serial_data.startswith("Add.") or serial_data.startswith("Che.") or serial_data.startswith("Rem.") or serial_data == "Del.ALL":
            if serial_data.startswith("Add."):
                try:
                    clean_data = serial_data.replace("\x00", "").strip()
                    id = int(clean_data.split(".")[1])
                    name = f"USER{id}"
                    print(f"Thêm/ cập nhật ID: {id}, Tên: {name}")
                    insertOrUpdate(id, name)
                    addFace(id, name, ser, cap, face_cascade)
                    reloadRecognizer()  # Reload recognizer after adding face
                except (ValueError, IndexError) as e:
                    print(f"Lỗi khi xử lý dữ liệu serial: {e}")

            elif serial_data.startswith("Che."):
                try:
                    clean_data = serial_data.replace("\x00", "").strip()
                    id = int(clean_data.split(".")[1])
                    name = f"USER{id}"
                    print(f"Kiểm tra ID: {id}, Tên: {name}")
                    if checkInDatabase(id, name):
                        ser.write(b"TRUE")
                        print("Dữ liệu tồn tại trong DB, đã gửi: TRUE")
                    else:
                        ser.write(b"FALSE")
                        print("Dữ liệu không tồn tại trong DB, đã gửi: FALSE")
                except (ValueError, IndexError) as e:
                    print(f"Lỗi khi xử lý dữ liệu serial: {e}")

            elif serial_data.startswith("Rem."):
                try:
                    clean_data = serial_data.replace("\x00", "").strip()
                    id = int(clean_data.split(".")[1])
                    name = f"USER{id}"
                    print(f"Yêu cầu xóa ID: {id}, Tên: {name}")
                    success = deleteData(id, name)
                    if success:
                        ser.write(b"True")
                        print("Đã gửi: True")
                    else:
                        ser.write(b"False")
                        print("Đã gửi: False")
                    if os.listdir('dataSet'):
                        trainRecognizer()
                    else:
                        createFakeTrainingData()
                    reloadRecognizer()  # Reload recognizer after removing face
                except (ValueError, IndexError) as e:
                    print(f"Lỗi khi xử lý dữ liệu serial: {e}")

            elif serial_data == "Del.ALL":
                print("Yêu cầu xóa tất cả dữ liệu...")
                success = deleteAllData()
                if success:
                    ser.write(b"True")
                    print("Đã gửi: True")
                else:
                    ser.write(b"False")
                    print("Đã gửi: False")
                reloadRecognizer()  # Reload recognizer after deleting all data
        elif serial_data.startswith("A.") or serial_data.startswith("U.") or serial_data.startswith("FA.") or serial_data.startswith("FIN.") or serial_data == "PW" or serial_data.startswith("RF.W") or serial_data.startswith("FA.W") or serial_data.startswith("FIN.W") or serial_data.startswith("PW.W"):
            try:
                clean_data = serial_data.replace("\x00", "").strip()
                method = ""
                name = ""
                status = "Successful"
                if serial_data.startswith("A.") or serial_data.startswith("U.") or serial_data.startswith("FA.") or serial_data.startswith("FIN."):
                    if serial_data.endswith(".W"):
                        method = serial_data.split(".")[0]
                        status = "WRONG"
                    else:
                        id = int(clean_data.split(".")[1])
                        if serial_data.startswith("A."):
                            method = "RFID"
                            name = f"Admin RFID {id}"
                        elif serial_data.startswith("U."):
                            method = "RFID"
                            name = f"User RFID {id}"
                        elif serial_data.startswith("FA."):
                            method = "FACEID"
                            name = f"FaceID {id}"
                        elif serial_data.startswith("FIN."):
                            method = "FINGERPRINT"
                            name = f"Fingerprint {id}"
                elif serial_data == "PW":
                    method = "PASSWORD"
                    name = ""
                elif serial_data.startswith("RF.W"):
                    method = "RFID"
                    name = ""
                    status = "WRONG"
                elif serial_data.startswith("FA.W"):
                    method = "FACEID"
                    name = ""
                    status = "WRONG"
                elif serial_data.startswith("FIN.W"):
                    method = "FINGERPRINT"
                    name = ""
                    status = "WRONG"
                elif serial_data.startswith("PW.W"):
                    method = "PASSWORD"
                    name = ""
                    status = "WRONG"
                insertIntoLog(method, name, status)
                print(f"Đã thêm vào log: Method={method}, Name={name}, Status={status}")
            except (ValueError, IndexError) as e:
                print(f"Lỗi khi xử lý dữ liệu serial: {e}")
    else:
        recognizeFace(ser, cap, face_cascade, recognizer)

cap.release()
cv2.destroyAllWindows()
ser.close()
