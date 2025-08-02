from flask import Flask, render_template_string, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from twilio.rest import Client
import random
import os
import threading
import time
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'abcdef123456789'  # Change this to a secure key

# Configure SQLite Database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///simpill.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Twilio Credentials (Replace with actual credentials)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "AC4bfa5e56e807ea84ae5fe0344bcf4115")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "831987f481d9a14d2d4c23ca09dc0e00")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "+17609775493")

# Initialize Twilio client
try:
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
except Exception as e:
    print(f"Error initializing Twilio client: {e}")
    client = None

# Store OTPs temporarily (resets if the server restarts)
otp_storage = {}

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=True)
    location = db.Column(db.String(100), nullable=True)
    user_type = db.Column(db.String(20), nullable=False)  # 'patient' or 'caregiver'

class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    dosage = db.Column(db.String(50), nullable=False)
    time = db.Column(db.String(10), nullable=False)  # 24-hour format HH:MM
    phone = db.Column(db.String(20), nullable=False)  # Phone number for reminders
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Create tables
with app.app_context():
    db.create_all()

# Decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Shared CSS/Styling
style = """
<style>
    body { 
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
        text-align: center; 
        background-color: #f0f8ff; 
        padding: 20px; 
        margin: 0;
        background: linear-gradient(135deg, #e0f7fa 0%, #80deea 100%);
        min-height: 100vh;
    }
    .container {
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
    }
    .logo {
        font-size: 2.5em;
        font-weight: bold;
        color: #0288d1;
        margin-bottom: 20px;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    .logo span {
        color: #4caf50;
    }
    form, table { 
        background: white; 
        padding: 25px; 
        border-radius: 15px; 
        box-shadow: 0px 4px 15px rgba(0,0,0,0.1);
        margin: 20px auto;
        max-width: 500px;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 30px;
    }
    th {
        background-color: #e1f5fe;
        padding: 12px;
    }
    td {
        padding: 10px;
        border-bottom: 1px solid #e0e0e0;
    }
    input { 
        margin: 10px 0; 
        padding: 12px; 
        width: 90%;
        border: 1px solid #ddd;
        border-radius: 5px;
        font-size: 14px;
    }
    button { 
        padding: 12px 20px; 
        background-color: #0288d1; 
        color: white; 
        border: none; 
        border-radius: 5px;
        cursor: pointer; 
        font-size: 16px;
        margin-top: 10px;
        transition: background-color 0.3s;
    }
    button:hover {
        background-color: #0277bd;
    }
    .delete-btn { 
        background-color: #f44336; 
        padding: 8px 15px;
        font-size: 14px;
    }
    .delete-btn:hover {
        background-color: #e53935;
    }
    .green-btn {
        background-color: #4caf50;
    }
    .green-btn:hover {
        background-color: #43a047;
    }
    h2 { 
        color: #0288d1; 
        margin-bottom: 20px;
    }
    h3 {
        color: #0288d1;
        margin-top: 30px;
    }
    .message {
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .success {
        background-color: #e8f5e9;
        border: 1px solid #4caf50;
        color: #2e7d32;
    }
    .error {
        background-color: #ffebee;
        border: 1px solid #f44336;
        color: #c62828;
    }
    .nav {
        display: flex;
        justify-content: center;
        margin: 20px 0;
    }
    .nav a {
        margin: 0 10px;
        text-decoration : none;
    }
    .pill-icon {
        font-size: 24px;
        vertical-align: middle;
        margin-right: 5px;
    }
</style>
"""

# HTML Templates
index_template = style + """
<div class="container">
    <div class="logo">Sim<span>Pill</span> 💊</div>
    <h2>Welcome to SimPill Medication Reminder</h2>
    
    {% if error %}
        <div class="message error">{{ error }}</div>
    {% endif %}

    <form action="/send-otp" method="post">
        <h3>Enter Your Phone Number</h3>
        <input type="text" name="phone" placeholder="Enter phone number (with country code)" required>
        <button type="submit">Send OTP</button>
    </form>
</div>
"""

otp_verification_template = style + """
<div class="container">
    <div class="logo">Sim<span>Pill</span> 💊</div>
    <h2>Verify Your Phone Number</h2>
    
    {% if error %}
        <div class="message error">{{ error }}</div>
    {% endif %}

    <form action="/verify-otp" method="post">
        <h3>Enter 6-Digit OTP</h3>
        <input type="hidden" name="phone" value="{{ phone }}">
        <input type="text" maxlength="6" name="otp" placeholder="Enter 6-digit OTP" required>
        <br>
        <button type="submit">Verify OTP</button>
    </form>
</div>
"""

user_type_template = style + """
<div class="container">
    <div class="logo">Sim<span>Pill</span> 💊</div>
    <h2>Select Account Type</h2>
    
    <div style="display: flex; justify-content: center; gap: 20px; margin-top: 30px;">
        <a href="{{ url_for('patient_registration', phone=phone) }}">
            <button style="padding: 15px 30px; font-size: 18px;">I am a Patient</button>
        </a>
        <a href="{{ url_for('caregiver_registration', phone=phone) }}">
            <button style="padding: 15px 30px; font-size: 18px;">I am a Caregiver</button>
        </a>
    </div>
</div>
"""

patient_template = style + """
<div class="container">
    <div class="logo">Sim<span>Pill</span> 💊</div>
    <h2>Patient Registration</h2>
    
    {% if error %}
        <div class="message error">{{ error }}</div>
    {% endif %}

    <form action="/patient-registration" method="post">
        <input type="hidden" name="phone" value="{{ phone }}">
        <input type="text" name="name" placeholder="Full Name" required>
        <input type="number" name="age" placeholder="Age" required>
        <input type="email" name="email" placeholder="Email Address" required>
        <input type="text" name="location" placeholder="Location/Address" required>
        <input type="password" name="password" placeholder="Password" required>
        <input type="password" name="confirm_password" placeholder="Confirm Password" required>
        <button type="submit">Register</button>
    </form>
</div>
"""

caregiver_template = style + """
<div class="container">
    <div class="logo">Sim<span>Pill</span> 💊</div>
    <h2>Caregiver Registration</h2>
    
    {% if error %}
        <div class="message error">{{ error }}</div>
    {% endif %}

    <form action="/caregiver-registration" method="post">
        <input type="hidden" name="phone" value="{{ phone }}">
        <input type="text" name="name" placeholder="Full Name" required>
        <input type="email" name="email" placeholder="Email Address" required>
        <input type="password" name="password" placeholder="Password" required>
        <input type="password" name="confirm_password" placeholder="Confirm Password" required>
        <button type="submit">Register</button>
    </form>
</div>
"""

login_template = style + """
<div class="container">
    <div class="logo">Sim<span>Pill</span> 💊</div>
    <h2>Login to SimPill</h2>
    
    {% if error %}
        <div class="message error">{{ error }}</div>
    {% endif %}
    {% if success %}
        <div class="message success">{{ success }}</div>
    {% endif %}

    <form action="/login" method="post">
        <input type="text" name="phone" placeholder="Phone Number" required>
        <input type="password" name="password" placeholder="Password" required>
        <button type="submit">Login</button>
    </form>
    
    <p>Don't have an account? <a href="/">Register</a></p>
</div>
"""

dashboard_template = style + """
<div class="container">
    <div class="logo">Sim<span>Pill</span> 💊</div>
    <h2>Welcome, {{ user.name }}!</h2>
    
    <div class="nav">
        <a href="{{ url_for('dashboard') }}"><button>Dashboard</button></a>
        <a href="{{ url_for('manage_medicines') }}"><button>Manage Medicines</button></a>
        <a href="{{ url_for('logout') }}"><button style="background-color: #f44336;">Logout</button></a>
    </div>
    
    {% if message %}
        <div class="message success">{{ message }}</div>
    {% endif %}
    
    <div style="margin-top: 30px;">
        <h3>Account Information</h3>
        <table>
            <tr><td><strong>Name:</strong></td><td>{{ user.name }}</td></tr>
            <tr><td><strong>Email:</strong></td><td>{{ user.email }}</td></tr>
            <tr><td><strong>Phone:</strong></td><td>{{ user.phone }}</td></tr>
            {% if user.user_type == 'patient' %}
                <tr><td><strong>Age:</strong></td><td>{{ user.age }}</td></tr>
                <tr><td><strong>Location:</strong></td><td>{{ user.location }}</td></tr>
            {% endif %}
            <tr><td><strong>Account Type:</strong></td><td>{{ user.user_type|capitalize }}</td></tr>
        </table>
    </div>
    
    <div style="margin-top: 30px;">
        <h3>Upcoming Medication Reminders</h3>
        {% if medicines %}
            <table>
                <tr>
                    <th>Medicine</th>
                    <th>Dosage</th>
                    <th>Time</th>
                </tr>
                {% for med in medicines %}
                    <tr>
                        <td>{{ med.name }}</td>
                        <td>{{ med.dosage }}</td>
                        <td>{{ med.time }}</td>
                    </tr>
                {% endfor %}
            </table>
        {% else %}
            <p>No medicines scheduled. <a href="{{ url_for('manage_medicines') }}">Add some?</a></p>
        {% endif %}
    </div>
</div>
"""

medicine_template = style + """
<div class="container">
    <div class="logo">Sim<span>Pill</span> 💊</div>
    <h2>Manage Medicines & Reminders</h2>
    
    <div class="nav">
        <a href="{{ url_for('dashboard') }}"><button>Dashboard</button></a>
        <a href="{{ url_for('manage_medicines') }}"><button>Manage Medicines</button></a>
        <a href="{{ url_for('logout') }}"><button style="background-color: #f44336;">Logout</button></a>
    </div>

    {% if message %}
        <div class="message success">{{ message }}</div>
    {% endif %}
    {% if error %}
        <div class="message error">{{ error }}</div>
    {% endif %}

    <form action="/add-medicine" method="post">
        <h3>Add New Medicine</h3>
        <input type="text" name="name" placeholder="Medicine Name" required>
        <input type="text" name="dosage" placeholder="Dosage (e.g., 500mg)" required>
        <input type="text" name="time" placeholder="Time (HH:MM, 24-hour format)" required>
        <input type="hidden" name="phone" value="{{ user.phone }}">
        <button type="submit">Add Medicine</button>
    </form>

    <h3>Your Medicines</h3>
    {% if medicines %}
        <table>
            <tr>
                <th>Medicine</th>
                <th>Dosage</th>
                <th>Time</th>
                <th>Actions</th>
            </tr>
            {% for med in medicines %}
                <tr>
                    <td>{{ med.name }}</td>
                    <td>{{ med.dosage }}</td>
                    <td>{{ med.time }}</td>
                    <td>
                        <form action="{{ url_for('delete_medicine', med_id=med.id) }}" method="post" style="display:inline; padding: 0; margin: 0; box-shadow: none; background: none;">
                            <button type="submit" class="delete-btn">Delete</button>
                        </form>
                    </td>
                </tr>
            {% endfor %}
        </table>
        
        <div style="margin-top: 30px;">
            <a href="{{ url_for('check_reminders') }}">
                <button class="green-btn">Test Reminders Now</button>
            </a>
        </div>
    {% else %}
        <p>No medicines added yet. Use the form above to add your first medicine.</p>
    {% endif %}
</div>
"""

# Routes
@app.route('/')
def index():
    if session.get('user_id'):
        return redirect(url_for('dashboard'))
    return render_template_string(index_template)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')
        
        # Add country code if not provided
        if not phone.startswith("+"):
            phone = "+91" + phone
            
        user = User.query.filter_by(phone=phone).first()
        
        if user and user.password == password:
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        else:
            return render_template_string(login_template, error="Invalid phone number or password.")
    
    return render_template_string(login_template)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login', success="You have been logged out successfully."))

@app.route('/send-otp', methods=['POST'])
def send_otp():
    phone_number = request.form.get('phone').strip()
    
    # Add country code if not provided
    if not phone_number.startswith("+"):
        phone_number = "+91" + phone_number
    
    # Check if user already exists
    existing_user = User.query.filter_by(phone=phone_number).first()
    if existing_user:
        return render_template_string(index_template, error="This phone number is already registered. Please login.")
    
    # Generate OTP
    otp = str(random.randint(100000, 999999))
    otp_storage[phone_number] = otp
    
    try:
        if client:
            client.messages.create(
                body=f'Your OTP for SimPill is {otp}',
                from_=TWILIO_PHONE_NUMBER,
                to=phone_number
            )
        else:
            # For development/testing when Twilio is not configured
            print(f"DEVELOPMENT MODE: OTP for {phone_number} is {otp}")
            
        return redirect(url_for('enter_otp', phone=phone_number))
    except Exception as e:
        return render_template_string(index_template, error=f"Error sending OTP: {str(e)}")

@app.route('/enter-otp')
def enter_otp():
    phone = request.args.get('phone')
    return render_template_string(otp_verification_template, phone=phone)

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    phone_number = request.form.get('phone').strip()
    entered_otp = request.form.get('otp')
    
    # For development/testing
    if not client and entered_otp == "123456":
        session['verified_phone'] = phone_number
        return redirect(url_for('user_type_selection', phone=phone_number))
        
    if otp_storage.get(phone_number) == entered_otp:
        session['verified_phone'] = phone_number
        if phone_number in otp_storage:
            del otp_storage[phone_number]
        return redirect(url_for('user_type_selection', phone=phone_number))
    else:
        return render_template_string(otp_verification_template, phone=phone_number, error="Invalid OTP. Please try again.")

@app.route('/user-type-selection')
def user_type_selection():
    phone = request.args.get('phone')
    if not session.get('verified_phone'):
        return redirect(url_for('index'))
    return render_template_string(user_type_template, phone=phone)

@app.route('/patient-registration', methods=['GET', 'POST'])
def patient_registration():
    if not session.get('verified_phone'):
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        phone = request.form.get('phone')
        name = request.form.get('name')
        email = request.form.get('email')
        age = request.form.get('age')
        location = request.form.get('location')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            return render_template_string(patient_template, phone=phone, error="Passwords do not match.")
        
        # Create new user
        user = User(
            name=name,
            email=email,
            phone=phone,
            password=password,
            age=age,
            location=location,
            user_type='patient'
        )
        
        db.session.add(user)
        try:
            db.session.commit()
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            return render_template_string(patient_template, phone=phone, error=f"Registration failed: {str(e)}")
    
    phone = request.args.get('phone')
    return render_template_string(patient_template, phone=phone)

@app.route('/caregiver-registration', methods=['GET', 'POST'])
def caregiver_registration():
    if not session.get('verified_phone'):
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        phone = request.form.get('phone')
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            return render_template_string(caregiver_template, phone=phone, error="Passwords do not match.")
        
        # Create new user
        user = User(
            name=name,
            email=email,
            phone=phone,
            password=password,
            user_type='caregiver'
        )
        
        db.session.add(user)
        try:
            db.session.commit()
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            return render_template_string(caregiver_template, phone=phone, error=f"Registration failed: {str(e)}")
    
    phone = request.args.get('phone')
    return render_template_string(caregiver_template, phone=phone)

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    medicines = Medicine.query.filter_by(user_id=user_id).all()
    return render_template_string(dashboard_template, user=user, medicines=medicines)

@app.route('/manage-medicines')
@login_required
def manage_medicines():
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    medicines = Medicine.query.filter_by(user_id=user_id).all()
    return render_template_string(medicine_template, user=user, medicines=medicines)

@app.route('/add-medicine', methods=['POST'])
@login_required
def add_medicine():
    user_id = session.get('user_id')
    data = request.form
    
    # Validate time format
    time_str = data["time"]
    try:
        # Validate time format (HH:MM)
        hours, minutes = map(int, time_str.split(':'))
        if not (0 <= hours <= 23 and 0 <= minutes <= 59):
            raise ValueError("Invalid time format")
    except Exception:
        user = User.query.get(user_id)
        medicines = Medicine.query.filter_by(user_id=user_id).all()
        return render_template_string(medicine_template, 
                                     user=user, 
                                     medicines=medicines, 
                                     error="Invalid time format. Please use HH:MM (24-hour format).")
    
    medicine = Medicine(
        name=data["name"], 
        dosage=data["dosage"], 
        time=data["time"], 
        phone=data["phone"],
        user_id=user_id
    )
    
    db.session.add(medicine)
    db.session.commit()
    
    return redirect(url_for('manage_medicines', message="Medicine added successfully!"))

@app.route('/delete-medicine/<int:med_id>', methods=['POST'])
@login_required
def delete_medicine(med_id):
    user_id = session.get('user_id')
    medicine = Medicine.query.get(med_id)
    
    if medicine and medicine.user_id == user_id:
        db.session.delete(medicine)
        db.session.commit()
        return redirect(url_for('manage_medicines', message="Medicine deleted successfully!"))
    else:
        return redirect(url_for('manage_medicines', error="Cannot delete this medicine."))

@app.route('/check-reminders')
@login_required
def check_reminders():
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    medicines = Medicine.query.filter_by(user_id=user_id).all()
    
    if not medicines:
        return redirect(url_for('manage_medicines', error="No medicines found to send reminders."))
    
    # Send test reminder for the first medicine
    try:
        test_medicine = medicines[0]
        send_reminder(test_medicine)
        return redirect(url_for('manage_medicines', message=f"Test reminder sent for {test_medicine.name}!"))
    except Exception as e:
        return redirect(url_for('manage_medicines', error=f"Error sending reminder: {str(e)}"))

def send_reminder(med):
    """Sends a reminder SMS via Twilio."""
    try:
        if client:
            client.messages.create(
                body=f"SimPill Reminder: Time to take {med.name} ({med.dosage}).",
                from_=TWILIO_PHONE_NUMBER,
                to=med.phone
            )
        else:
            # For development/testing
            print(f"DEVELOPMENT MODE: Reminder sent to {med.phone} for {med.name} ({med.dosage})")
        
        print(f"Reminder sent to {med.phone} for {med.name} at {med.time}")
        return True
    except Exception as e:
        print(f"Error sending reminder: {e}")
        return False

def reminder_scheduler():
    """Runs a loop that checks for medicine reminders every minute."""
    with app.app_context():
        while True:
            now = datetime.now().strftime("%H:%M")
            medicines = Medicine.query.filter_by(time=now).all()
            for med in medicines:
                send_reminder(med)
            time.sleep(60)  # Wait 1 minute before checking again

# Start the reminder scheduler in a background thread
threading.Thread(target=reminder_scheduler, daemon=True).start()

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)