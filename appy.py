from otp import Flask, render_template, request, redirect, url_for, session
from twilio.rest import Client
import random

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Twilio Credentials (Replace with your own)
TWILIO_ACCOUNT_SID = "AC4bfa5e56e807ea84ae5fe0344bcf4115"
TWILIO_AUTH_TOKEN = "35988329e4284fab3f4f44a2881c0acd"
TWILIO_PHONE_NUMBER = "+17609775493"

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Store OTP temporarily
otp_store = {}

# Home Route (Registration Page)
@app.route("/")
def index():
    return render_template("index.html", otp_sent=False)

# Route to send OTP
@app.route("/send-otp", methods=["POST"])
def send_otp():
    phone = request.form.get("phone")

    if not phone or len(phone) != 10:
        return render_template("index.html", message="Invalid phone number", otp_sent=False)

    otp = str(random.randint(100000, 999999))  # Generate a 6-digit OTP
    otp_store[phone] = otp  # Store OTP temporarily

    # Send OTP via Twilio
    client.messages.create(
        body=f"Your OTP for registration is {otp}. It is valid for 5 minutes.",
        from_=TWILIO_PHONE_NUMBER,
        to="+91" + phone  # Change for country-specific prefixes
    )

    return render_template("index.html", message="OTP sent successfully!", otp_sent=True, phone=phone)

# Route to verify OTP
@app.route("/verify-otp", methods=["POST"])
def verify_otp():
    phone = request.form.get("phone")
    otp = request.form.get("otp")

    if phone in otp_store and otp_store[phone] == otp:
        del otp_store[phone]  # Remove OTP after verification
        return render_template("index.html", message="OTP Verified! Registration Successful.", otp_sent=False)
    
    return render_template("index.html", message="Invalid OTP. Try again.", otp_sent=True, phone=phone)

if __name__ == "__main__":
    app.run(debug=True)
