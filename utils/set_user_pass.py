import sys
import random
import string
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

# Configuration for the Flask app
class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'your_secret_key'

# Create the Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize the database
db = SQLAlchemy(app)

# Define the User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password_hash = db.Column(db.String(128))
    birth_date = db.Column(db.Date, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(50), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

# Function to update the user's password or add the user if they don't exist
def update_or_add_user(username, new_password, birth_date, start_date, status, role):
    user = User.query.filter_by(username=username).first()
    if user:
        user.set_password(new_password)
    else:
        user = User(
            username=username,
            birth_date=birth_date,
            start_date=start_date,
            status=status,
            role=role
        )
        user.set_password(new_password)
        db.session.add(user)
    db.session.commit()
    return user

# Main function to run the script
if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("Usage: python update_user_pass.py <username> <birth_date> <start_date> <status> <role>")
        sys.exit(1)

    username = sys.argv[1]
    birth_date = datetime.strptime(sys.argv[2], '%Y-%m-%d').date()
    start_date = datetime.strptime(sys.argv[3], '%Y-%m-%d').date()
    status = sys.argv[4]
    role = sys.argv[5]
    
    # Generate a random password
    new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=16))

    with app.app_context():
        user = update_or_add_user(username, new_password, birth_date, start_date, status, role)
    
    if user:
        print(f"User {username} has been added or updated with password: {new_password}")
    else:
        print(f"Failed to update or create user: {username}")
