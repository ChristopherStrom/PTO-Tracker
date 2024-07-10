import sys
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

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

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Function to get the user's password
def get_user_password(username):
    user = User.query.filter_by(username=username).first()
    if user:
        return user.password_hash
    else:
        return None

# Main function to run the script
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python get_user_pass.py <username>")
        sys.exit(1)

    username = sys.argv[1]
    
    with app.app_context():
        password = get_user_password(username)
    
    if password:
        print(f"The password hash for {username} is: {password}")
    else:
        print(f"No user found with username: {username}")
