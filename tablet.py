import cv2
import numpy as np
import tensorflow as tf
from otp import Flask, request, jsonify, render_template
import sqlite3

def detect_tablets(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (9, 9), 2)
    
    # HoughCircles to detect circular tablets
    circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=1.2, minDist=50,
                               param1=50, param2=30, minRadius=10, maxRadius=100)
    
    if circles is not None:
        circles = np.uint16(np.around(circles))
        for i in circles[0, :]:
            cv2.circle(frame, (i[0], i[1]), i[2], (0, 255, 0), 3)
            cv2.putText(frame, "Tablet", (i[0] - 20, i[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    return frame

def classify_tablet(image):
    model = tf.keras.models.load_model('tablet_model.h5')
    image = cv2.resize(image, (64, 64)) / 255.0
    image = np.expand_dims(image, axis=0)
    prediction = model.predict(image)
    return np.argmax(prediction)

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('medications.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS medications
                 (id INTEGER PRIMARY KEY, name TEXT, dosage TEXT)''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/detect', methods=['POST'])
def detect():
    file = request.files['image']
    np_img = np.frombuffer(file.read(), np.uint8)
    frame = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
    processed_frame = detect_tablets(frame)
    tablet_class = classify_tablet(processed_frame)
    return jsonify({'tablet_id': int(tablet_class)})

def main():
    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = detect_tablets(frame)
        cv2.imshow("Tablet Detection", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
