from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from twilio.rest import Client
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'abcdef'  # Change this to a secure key

# Configure SQLite Database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///reminder_app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Twilio Credentials (Replace with actual credentials)
TWILIO_ACCOUNT_SID = os.getenv("AC4bfa5e56e807ea84ae5fe0344bcf4115")
TWILIO_AUTH_TOKEN = os.getenv("35988329e4284fab3f4f44a2881c0acd")
TWILIO_PHONE_NUMBER = "+17609775493"

# Initialize Twilio client
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Database Model for Medicines
class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    dosage = db.Column(db.String(50), nullable=False)
    time = db.Column(db.String(10), nullable=False)  # 24-hour format HH:MM
    phone = db.Column(db.String(20), nullable=False)  # Phone number for reminders
    
with app.app_context():
    db.create_all()

# HTML Template (for medicine list & adding new medicines)
style = """
<style>
    body { font-family: Arial, sans-serif; text-align: center; background-color: #f0f0f0; padding: 20px; }
    form, table { background: white; padding: 20px; border-radius: 10px; box-shadow: 0px 0px 10px gray; display: inline-block; }
    input { margin: 10px; padding: 8px; width: 80%; }
    button { padding: 10px 15px; background-color: blue; color: white; border: none; cursor: pointer; }
    h2 { color: #333; }
</style>
"""

medicine_template = style + """
<h2>Medicine List & Reminders</h2>
<form action="/add-medicine" method="post">
    <input type="text" name="name" placeholder="Medicine Name" required><br>
    <input type="text" name="dosage" placeholder="Dosage (e.g., 500mg)" required><br>
    <input type="text" name="time" placeholder="Time (HH:MM, 24-hour format)" required><br>
    <input type="text" name="phone" placeholder="Phone Number (e.g., +911234567890)" required><br>
    <button type="submit">Add Medicine</button>
</form>

<h3>Current Medicines</h3>
<table border="1" cellpadding="10">
    <tr><th>Medicine</th><th>Dosage</th><th>Time</th><th>Phone</th></tr>
    {% for med in medicines %}
        <tr><td>{{ med.name }}</td><td>{{ med.dosage }}</td><td>{{ med.time }}</td><td>{{ med.phone }}</td></tr>
    {% endfor %}
</table>
"""

@app.route('/')
def show_medicines():
    medicines = Medicine.query.all()
    return render_template_string(medicine_template, medicines=medicines)

@app.route('/add-medicine', methods=['POST'])
def add_medicine():
    data = request.form
    medicine = Medicine(name=data["name"], dosage=data["dosage"], time=data["time"], phone=data["phone"])
    db.session.add(medicine)
    db.session.commit()
    return redirect(url_for('show_medicines'))

@app.route('/send-reminders')
def send_reminders():
    now = datetime.now().strftime("%H:%M")
    medicines = Medicine.query.filter_by(time=now).all()
    
    for med in medicines:
        client.messages.create(
            body=f"Reminder: Take {med.name} ({med.dosage})",
            from_=TWILIO_PHONE_NUMBER,
            to=med.phone
        )
    
    return "Reminders sent!"

if __name__ == '__main__':
    app.run(debug=True)
