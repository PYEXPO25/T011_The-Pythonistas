from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from twilio.rest import Client
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'
db = SQLAlchemy(app)

# Twilio Configuration
TWILIO_ACCOUNT_SID = "AC4bfa5e56e807ea84ae5fe0344bcf4115"
TWILIO_AUTH_TOKEN = "831987f481d9a14d2d4c23ca09dc0e00"
TWILIO_PHONE_NUMBER = "+17609775493"
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    otp = db.Column(db.String(6), nullable=True)
    verified = db.Column(db.Boolean, default=False)

@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('register'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        existing_user = User.query.filter_by(phone=phone).first()
        if existing_user:
            return "Phone number already registered! Please login."
        otp = str(random.randint(100000, 999999))
        user = User(name=name, phone=phone, otp=otp)
        db.session.add(user)
        db.session.commit()
        send_otp(phone, otp)
        session['phone'] = phone
        return redirect(url_for('verify'))
    return render_template('register.html')

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        phone = session.get('phone')
        otp_entered = request.form['otp']
        user = User.query.filter_by(phone=phone, otp=otp_entered).first()
        if user:
            user.verified = True
            user.otp = None
            db.session.commit()
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        return "Invalid OTP, try again!"
    return render_template('verify.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form['phone']
        user = User.query.filter_by(phone=phone).first()
        if user and user.verified:
            otp = str(random.randint(100000, 999999))
            user.otp = otp
            db.session.commit()
            send_otp(phone, otp)
            session['phone'] = phone
            return redirect(url_for('verify'))
        return "User not found or not verified. Please register."
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

def send_otp(phone, otp):
    message = client.messages.create(
        body=f'Your OTP is: {otp}',
        from_=TWILIO_PHONE_NUMBER,
        to=phone
    )
    print(f'OTP sent to {phone}: {otp}')

if __name__ == '__main__':
    app.run(debug=True)
