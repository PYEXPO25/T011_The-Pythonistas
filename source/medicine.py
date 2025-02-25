from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from twilio.rest import Client
import random
import os

app = Flask(__name__)
app.secret_key = 'abcdef'  # Change this to a secure key

# Twilio Credentials (Replace with actual credentials)
TWILIO_ACCOUNT_SID = os.getenv("AC4bfa5e56e807ea84ae5fe0344bcf4115")
TWILIO_AUTH_TOKEN = os.getenv("831987f481d9a14d2d4c23ca09dc0e00")
TWILIO_PHONE_NUMBER = "+17609775493"

# Initialize Twilio client
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Store OTPs temporarily (resets if the server restarts)
otp_storage = {}

# HTML Templates (Embedded with CSS Styling)
style = """
<style>
    body { font-family: Arial, sans-serif; text-align: center; background-color: #f0f0f0; padding: 20px; }
    form { background: white; padding: 20px; border-radius: 10px; box-shadow: 0px 0px 10px gray; display: inline-block; }
    input { margin: 10px; padding: 8px; width: 80%; }
    button { padding: 10px 15px; background-color: blue; color: white; border: none; cursor: pointer; }
    h2 { color: #333; }
</style>
"""

index_template = style + """
<h2>Enter Your Phone Number</h2>
{% if error %}<p style="color: red;">{{ error }}</p>{% endif %}
<form action="/send-otp" method="post">
    <input type="text" name="phone" placeholder="Enter phone number" required>
    <button type="submit">Send OTP</button>
</form>
"""

otp_verification_template = style + """
<h2>Enter 6-Digit OTP</h2>
{% if error %}<p style="color: red;">{{ error }}</p>{% endif %}
<form action="/verify-otp" method="post">
    <input type="hidden" name="phone" value="{{ request.args.get('phone') }}">
    <input type="text" maxlength="6" name="otp" required>
    <br>
    <button type="submit">Verify OTP</button>
</form>
"""

patient_template = style + """
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
"""

caregiver_template = style + """
<h2>Caregiver Registration</h2>
<form action="/caregiver" method="post">
    <input type="text" name="name" placeholder="Name" required><br>
    <input type="email" name="email" placeholder="Email" required><br>
    <input type="text" name="phone" placeholder="Phone" required><br>
    <input type="password" name="password" placeholder="Password" required><br>
    <button type="submit">Submit</button>
</form>
"""

@app.route('/')
def index():
    return render_template_string(index_template)

@app.route('/send-otp', methods=['POST'])
def send_otp():
    phone_number = request.form.get('phone').strip()
    if not phone_number.startswith("+"):
        phone_number = "+91" + phone_number
    otp = str(random.randint(100000, 999999))
    otp_storage[phone_number] = otp
    try:
        client.messages.create(body=f'Your OTP for Medicine Reminder App is {otp}', from_=TWILIO_PHONE_NUMBER, to=phone_number)
        return redirect(url_for('enter_otp', phone=phone_number))
    except Exception as e:
        return render_template_string(index_template, error=f"Error sending OTP: {str(e)}")

@app.route('/enter-otp')
def enter_otp():
    return render_template_string(otp_verification_template)

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    phone_number = request.form.get('phone').strip()
    entered_otp = request.form.get('otp')
    if otp_storage.get(phone_number) == entered_otp:
        session['authenticated'] = True
        del otp_storage[phone_number]
        return redirect(url_for('patient'))
    else:
        return render_template_string(otp_verification_template, error="Invalid OTP. Please try again.")

@app.route('/patient', methods=['GET', 'POST'])
def patient():
    if not session.get('authenticated'):
        return redirect(url_for('index'))
    if request.method == 'POST':
        session['patient_data'] = request.form.to_dict()
        return redirect(url_for('caregiver'))
    return render_template_string(patient_template)

@app.route('/caregiver', methods=['GET', 'POST'])
def caregiver():
    if not session.get('authenticated'):
        return redirect(url_for('index'))
    if request.method == 'POST':
        session['caregiver_data'] = request.form.to_dict()
        return jsonify({"patient": session['patient_data'], "caregiver": session['caregiver_data']})
    return render_template_string(caregiver_template)

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)