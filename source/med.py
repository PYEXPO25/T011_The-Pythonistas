from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from twilio.rest import Client
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

# Twilio Configuration
twilio_sid = "your_twilio_sid"
twilio_auth_token = "your_twilio_auth_token"
twilio_phone_number = "your_twilio_phone"
client = Client(twilio_sid, twilio_auth_token)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    otp = db.Column(db.String(6), nullable=True)

class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    dosage = db.Column(db.String(50), nullable=False)
    time = db.Column(db.String(20), nullable=False)
    frequency = db.Column(db.String(20), nullable=False)

# Routes
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('Regform.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']

        # ✅ Check if phone or email already exists
        existing_user = User.query.filter((User.phone == phone) | (User.email == email)).first()
        if existing_user:
            flash('Email or phone number already registered. Please log in.', 'danger')
            return redirect(url_for('home'))  # Redirect back to login page

        # Generate OTP and register user
        otp = str(random.randint(100000, 999999))
        new_user = User(username=username, email=email, phone=phone, password=password, otp=otp)
        db.session.add(new_user)
        db.session.commit()

        # Send OTP via Twilio
        client.messages.create(
            body=f"Your SimPill OTP is {otp}",
            from_=twilio_phone_number,
            to=phone
        )

        return redirect(url_for('otp', phone=phone))

    return render_template('sign_up.html')


@app.route('/otp/<phone>', methods=['GET', 'POST'])
def otp(phone):
    user = User.query.filter_by(phone=phone).first()
    if request.method == 'POST':
        entered_otp = request.form['otp']
        if user.otp == entered_otp:
            session['user_id'] = user.id
            return redirect(url_for('success'))
        else:
            flash('Invalid OTP. Try again.', 'danger')
    return render_template('otp.html', phone=phone)

@app.route('/success')
def success():
    return render_template('reg_success.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    user_id = session['user_id']
    medicines = Medicine.query.filter_by(user_id=user_id).all()
    if request.method == 'POST':
        name = request.form['medicine-name']
        dosage = request.form['dosage']
        time = request.form['time']
        frequency = request.form['frequency']
        new_medicine = Medicine(user_id=user_id, name=name, dosage=dosage, time=time, frequency=frequency)
        db.session.add(new_medicine)
        db.session.commit()
        flash('Medicine added successfully!', 'success')
    return render_template('medlist.html', medicines=medicines)

@app.route('/send_reminder', methods=['POST'])
def send_reminder():
    phone = request.form['patient_phone']
    message = f"Reminder: It's time to take your medicine."
    client.messages.create(body=message, from_=twilio_phone_number, to=phone)
    flash('Reminder sent successfully!', 'success')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
