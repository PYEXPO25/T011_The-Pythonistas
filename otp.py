from otp import Flask, request, jsonify, session
from twilio.rest import Client
import random
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Used for session management

# Twilio Credentials (Replace with your actual credentials)
TWILIO_ACCOUNT_SID = "AC4bfa5e56e807ea84ae5fe0344bcf4115"
TWILIO_AUTH_TOKEN = "35988329e4284fab3f4f44a2881c0acd"
TWILIO_PHONE_NUMBER = "+17609775493"

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def generate_otp():
    """Generate a random 6-digit OTP"""
    return str(random.randint(100000, 999999))

@app.route('/send-otp', methods=['POST'])
def send_otp():
    data = request.json
    phone_number = data.get('phone')

    if not phone_number:
        return jsonify({"error": "Phone number is required"}), 400

    otp = generate_otp()
    session['otp'] = otp  # Store OTP in session

    message = client.messages.create(
        body=f'Your OTP is: {otp}',
        from_=TWILIO_PHONE_NUMBER,
        to=+91+phone_number
    )

    return jsonify({"message": "OTP sent successfully!"})

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json
    user_otp = data.get('otp')

    if not user_otp:
        return jsonify({"error": "OTP is required"}), 400

    if 'otp' in session and session['otp'] == user_otp:
        return jsonify({"message": "OTP verified successfully!"})
    else:
        return jsonify({"error": "Invalid OTP"}), 400

if __name__ == '__main__':
    app.run(debug=True)
