from datetime import datetime, timedelta, date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()
login_manager = LoginManager()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    birth_date = db.Column(db.Date, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    password_hash = db.Column(db.String(128))
    pto_hours = db.Column(db.Float, default=0.0)
    emergency_hours = db.Column(db.Float, default=0.0)
    vacation_hours = db.Column(db.Float, default=0.0)
    start_period = db.Column(db.Date, default=datetime.utcnow)
    end_period = db.Column(db.Date, nullable=True)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class TimeOff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    hours = db.Column(db.Float, nullable=False)
    reason = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('time_offs', lazy=True))

class BucketChange(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    category = db.Column(db.String(50), nullable=False)
    old_value = db.Column(db.Float, nullable=False)
    new_value = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('bucket_changes', lazy=True))

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('notes', lazy=True))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def workdays(start_date, end_date):
    """Returns the number of workdays (Monday-Friday) between two dates."""
    day_count = 0
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() < 5:  # Monday to Friday are 0 to 4
            day_count += 1
        current_date += timedelta(days=1)
    return day_count

def calculate_earned_pto(start_period, end_period, total_annual_pto=64):
    """Calculates earned PTO based on the start period and end period."""
    current_date = datetime.today().date()

    # If the end period is set and it's before the current date, use end period as current date
    if end_period and end_period < current_date:
        current_date = end_period

    # Total workdays in the entire period (start_period to end_period)
    total_workdays_in_period = workdays(start_period, end_period)

    # Total workdays passed from start_period to current_date
    workdays_passed = workdays(start_period, current_date)

    # Calculate earned PTO based on proportion of workdays passed
    earned_pto = (workdays_passed / total_workdays_in_period) * total_annual_pto
    return round(earned_pto, 2)



