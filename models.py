from datetime import datetime
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

class PeriodArchive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    pto_total = db.Column(db.Float, nullable=False, default=0)
    emergency_total = db.Column(db.Float, nullable=False, default=0)
    vacation_total = db.Column(db.Float, nullable=False, default=0)
    period_start = db.Column(db.DateTime, nullable=False)
    period_end = db.Column(db.DateTime, nullable=False)

class PeriodArchive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    pto_total = db.Column(db.Float, nullable=False, default=0)
    emergency_total = db.Column(db.Float, nullable=False, default=0)
    vacation_total = db.Column(db.Float, nullable=False, default=0)
    period_start = db.Column(db.DateTime, nullable=False)
    period_end = db.Column(db.DateTime, nullable=False)

# PeriodArchive model
class PeriodArchive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    pto_total = db.Column(db.Float, nullable=False, default=0)
    emergency_total = db.Column(db.Float, nullable=False, default=0)
    vacation_total = db.Column(db.Float, nullable=False, default=0)
    period_start = db.Column(db.DateTime, nullable=False)
    period_end = db.Column(db.DateTime, nullable=False)
    user = db.relationship('User', backref=db.backref('archives', lazy=True))
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
