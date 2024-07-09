import random
import string
from datetime import datetime
from app import app, db
from models import User

def generate_random_password(length=16):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))

default_username = 'admin'
default_password = generate_random_password()
default_birth_date = datetime(1970, 1, 1)  # Example birth date

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username=default_username).first():
        admin = User(username=default_username, birth_date=default_birth_date, start_date=datetime.utcnow())
        admin.set_password(default_password)
        db.session.add(admin)
        db.session.commit()
        print(f'Created default admin user with username: {default_username} and password: {default_password}')
