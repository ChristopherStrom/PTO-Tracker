# utils/init.py

import sys
import os
from datetime import date
from werkzeug.security import generate_password_hash

# Ensure the app's path is in the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import User

def create_admin(username, password):
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()

        # Check if admin user already exists
        admin = User.query.filter_by(username=username).first()
        if admin:
            admin.set_password(password)
            print(f"Admin user '{username}' already exists. Password has been updated.")
        else:
            # Create new admin user
            admin = User(
                username=username,
                password_hash=generate_password_hash(password),
                birth_date=date(1970, 1, 1),
                start_date=date(2022, 1, 1),
                status='active',
                role='admin'
            )
            db.session.add(admin)
            print(f"Admin user '{username}' created successfully.")
        
        db.session.commit()
        print(f"Username: {username}")
        print(f"Password: {password}")

if __name__ == '__main__':
    admin_username = 'admin'  # Change this to your desired admin username
    admin_password = 'password'  # Change this to your desired admin password
    create_admin(admin_username, admin_password)
