from otp import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///doctors.db'
db = SQLAlchemy(app)

# Database Models
class Hospital(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    specialty = db.Column(db.String(100), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id'), nullable=False)
    hospital = db.relationship('Hospital', backref=db.backref('doctors', lazy=True))
    treatment = db.Column(db.String(200), nullable=False)

# Routes
@app.route('/')
def index():
    doctors = Doctor.query.all()
    return render_template('index.html', doctors=doctors)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables
    app.run(debug=True)