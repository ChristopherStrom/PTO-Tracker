import sys
import os
from app import create_app
from models import db, User

def get_user_password(username):
    user = User.query.filter_by(username=username).first()
    if user:
        return user.password_hash  # Replace this with the actual method to get the password
    else:
        return None

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python get_user_pass.py <username>")
        sys.exit(1)

    username = sys.argv[1]
    
    # Set up the Flask application context
    app = create_app()
    with app.app_context():
        password = get_user_password(username)
    
    if password:
        print(f"The password for {username} is: {password}")
    else:
        print(f"No user found with username: {username}")
