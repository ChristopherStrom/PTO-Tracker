from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()
login_manager = LoginManager()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    start_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    birth_date = db.Column(db.Date, nullable=False)
    pto_hours = db.Column(db.Integer, nullable=False, default=0)
    emergency_hours = db.Column(db.Integer, nullable=False, default=0)
    vacation_hours = db.Column(db.Integer, nullable=False, default=0)

    time_off = db.relationship('TimeOff', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"User('{self.username}', '{self.start_date}', '{self.birth_date}')"

class TimeOff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    hours = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"TimeOff('{self.date}', '{self.hours}', '{self.reason}')"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
