from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from twilio.rest import Client
import random

app = Flask(__name__)
app.secret_key = 'abcdef'  # Change this to a secure secret key

# Twilio Credentials (Replace with your actual credentials)
TWILIO_ACCOUNT_SID = "AC4bfa5e56e807ea84ae5fe0344bcf4115"
TWILIO_AUTH_TOKEN = "35988329e4284fab3f4f44a2881c0acd"
TWILIO_PHONE_NUMBER = "+17609775493"

# Initialize Twilio client
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Store OTPs temporarily (this will reset if server restarts)
otp_storage = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send-otp', methods=['POST'])
def send_otp():
    phone_number = request.form.get('phone').strip()  # Remove spaces

    # Ensure phone number is in E.164 format (+91 for India, change as needed)
    if not phone_number.startswith("+"):
        phone_number = "+91" + phone_number  

    otp = str(random.randint(100000, 999999))
    otp_storage[phone_number] = otp  # Store OTP temporarily

    try:
        # Send OTP via Twilio
        message = client.messages.create(
            body=f'Your OTP for Medicine Reminder App is {otp}',
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        return render_template('index.html', otp_sent=True)

    except Exception as e:
        return render_template('index.html', error=f"Error sending OTP: {str(e)}")

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    phone_number = request.form.get('phone').strip()

    # Ensure number is in correct format
    if not phone_number.startswith("+"):
        phone_number = "+91" + phone_number  

    entered_otp = request.form.get('otp')

    if phone_number in otp_storage and otp_storage[phone_number] == entered_otp:
        session['authenticated'] = True
        del otp_storage[phone_number]  # Remove OTP after verification
        return redirect(url_for('patient'))
    else:
        return render_template('index.html', error="Invalid OTP. Please try again.")

@app.route('/patient', methods=['GET', 'POST'])
def patient():
    if not session.get('authenticated'):
        return redirect(url_for('index'))  # Redirect if not logged in

    if request.method == 'POST':
        patient_data = {
            'name': request.form.get('name'),
            'age': request.form.get('age'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone'),
            'location': request.form.get('location'),
            'password': request.form.get('password')
        }
        session['patient_data'] = patient_data
        return redirect(url_for('medicine'))

    return render_template('patient.html')

@app.route('/medicine', methods=['GET', 'POST'])
def medicine():
    if request.method == 'POST':
        medicine_data = {
            'name': request.form.get('medicine_name'),
            'dosage': request.form.get('dosage'),
            'time': request.form.get('time')
        }
        return jsonify(medicine_data)  # Simulate storing in DB

    return render_template('medicine.html')

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
