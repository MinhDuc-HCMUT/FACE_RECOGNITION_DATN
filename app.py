from flask import Flask, render_template, jsonify
import sqlite3

app = Flask(__name__)

def get_monitor_data():
    conn = sqlite3.connect(r'D:\DATN\DATN_FINAL_main\FACE_RECOGNITION\data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT STT, Method, Identification, Status, Time, Day FROM monitor")
    data = cursor.fetchall()
    conn.close()
    return data

@app.route('/')
def index():
    data = get_monitor_data()
    return render_template('index.html', data=data)

@app.route('/data')
def data():
    data = get_monitor_data()
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
