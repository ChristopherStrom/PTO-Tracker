import sys
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

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

# Function to update the user's password or add the user if they don't exist
def update_or_add_user(username, new_password):
    user = User.query.filter_by(username=username).first()
    if user:
        user.set_password(new_password)
    else:
        user = User(username=username)
        user.set_password(new_password)
        db.session.add(user)
    db.session.commit()
    return user

# Main function to run the script
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python update_user_pass.py <username> <new_password>")
        sys.exit(1)

    username = sys.argv[1]
    new_password = sys.argv[2]
    
    with app.app_context():
        user = update_or_add_user(username, new_password)
    
    if user:
        print(f"The password for {username} has been updated or user has been created.")
    else:
        print(f"Failed to update or create user: {username}")
