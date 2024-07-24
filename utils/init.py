# init.py
from app import app, db
from models import User
from werkzeug.security import generate_password_hash

def create_admin(username, password):
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()

        # Check if admin user already exists
        if not User.query.filter_by(username=username).first():
            # Create admin user
            admin = User(
                username=username,
                password_hash=generate_password_hash(password),
                birth_date="1970-01-01",
                start_date="2022-01-01",
                status='active',
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print(f"Admin user '{username}' created successfully.")
        else:
            print(f"Admin user '{username}' already exists.")

if __name__ == '__main__':
    admin_username = 'admin'  # Change this to your desired admin username
    admin_password = 'password'  # Change this to your desired admin password
    create_admin(admin_username, admin_password)
