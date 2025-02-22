from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from twilio.rest import Client
import random

app = Flask(__name__)
app.secret_key = 'abcdef'  # Change this to a secure key

# Twilio Credentials (Replace with actual credentials)
import os

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

TWILIO_PHONE_NUMBER = "+17609775493"

# Initialize Twilio client
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Store OTPs temporarily (resets if the server restarts)
otp_storage = {}

# HTML Templates (Embedded)
index_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enter Phone Number</title>
</head>
<body>
    <h2>Enter Your Phone Number</h2>
    {% if error %}
        <p style="color: red;">{{ error }}</p>
    {% endif %}
    <form action="/send-otp" method="post">
        <input type="text" name="phone" placeholder="Enter phone number" required>
        <button type="submit">Send OTP</button>
    </form>
</body>
</html>
"""

otp_verification_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OTP Verification</title>
</head>
<body>
    <h2>Enter 6-Digit OTP</h2>
    {% if error %}
        <p style="color: red;">{{ error }}</p>
    {% endif %}
    <form action="/verify-otp" method="post">
        <input type="hidden" name="phone" value="{{ request.args.get('phone') }}">
        <input type="text" maxlength="1" name="otp1" required>
        <input type="text" maxlength="1" name="otp2" required>
        <input type="text" maxlength="1" name="otp3" required>
        <input type="text" maxlength="1" name="otp4" required>
        <input type="text" maxlength="1" name="otp5" required>
        <input type="text" maxlength="1" name="otp6" required>
        <br>
        <button type="submit">Verify OTP</button>
    </form>
</body>
</html>
"""

patient_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Patient Registration</title>
</head>
<body>
    <h2>Patient Registration</h2>
    <form action="/patient" method="post">
        <input type="text" name="name" placeholder="Name" required><br>
        <input type="number" name="age" placeholder="Age" required><br>
        <input type="email" name="email" placeholder="Email" required><br>
        <input type="text" name="phone" placeholder="Phone" required><br>
        <input type="text" name="location" placeholder="Location" required><br>
        <input type="password" name="password" placeholder="Password" required><br>
        <button type="submit">Submit</button>
    </form>
</body>
</html>
"""

medicine_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Medicine Reminder</title>
</head>
<body>
    <h2>Enter Medicine Details</h2>
    <form action="/medicine" method="post">
        <input type="text" name="medicine_name" placeholder="Medicine Name" required><br>
        <input type="text" name="dosage" placeholder="Dosage" required><br>
        <input type="text" name="time" placeholder="Time" required><br>
        <button type="submit">Add Medicine</button>
    </form>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(index_template)

@app.route('/send-otp', methods=['POST'])
def send_otp():
    phone_number = request.form.get('phone').strip()

    # Ensure phone number starts with country code
    if not phone_number.startswith("+"):
        phone_number = "+91" + phone_number  # Modify as needed

    otp = str(random.randint(100000, 999999))
    otp_storage[phone_number] = otp  # Store OTP temporarily

    try:
        message = client.messages.create(
            body=f'Your OTP for Medicine Reminder App is {otp}',
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        return redirect(url_for('enter_otp', phone=phone_number))
    except Exception as e:
        return render_template_string(index_template, error=f"Error sending OTP: {str(e)}")

@app.route('/enter-otp')
def enter_otp():
    return render_template_string(otp_verification_template)

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    phone_number = request.form.get('phone').strip()

    if not phone_number.startswith("+"):
        phone_number = "+91" + phone_number  

    entered_otp = "".join([
        request.form.get('otp1'),
        request.form.get('otp2'),
        request.form.get('otp3'),
        request.form.get('otp4'),
        request.form.get('otp5'),
        request.form.get('otp6')
    ])

    if phone_number in otp_storage and otp_storage[phone_number] == entered_otp:
        session['authenticated'] = True
        del otp_storage[phone_number]  # Remove OTP after verification
        return redirect(url_for('patient'))
    else:
        return render_template_string(otp_verification_template, error="Invalid OTP. Please try again.")

@app.route('/patient', methods=['GET', 'POST'])
def patient():
    if not session.get('authenticated'):
        return redirect(url_for('index'))  

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

    return render_template_string(patient_template)

@app.route('/medicine', methods=['GET', 'POST'])
def medicine():
    if request.method == 'POST':
        medicine_data = {
            'name': request.form.get('medicine_name'),
            'dosage': request.form.get('dosage'),
            'time': request.form.get('time')
        }
        return jsonify(medicine_data)  # Simulate storing in DB

    return render_template_string(medicine_template)

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
