import random
import string
from datetime import datetime
from app import app, db
from models import User

def generate_random_password(length=16):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))

with app.app_context():
    db.create_all()
    default_users = [
        {'username': 'admin', 'password': generate_random_password(), 'birth_date': datetime(1970, 1, 1), 'role': 'admin', 'status': 'active'},
        {'username': 'user1', 'password': generate_random_password(), 'birth_date': datetime(1990, 1, 1), 'role': 'user', 'status': 'active'},
        {'username': 'user2', 'password': generate_random_password(), 'birth_date': datetime(1995, 1, 1), 'role': 'user', 'status': 'inactive'}
    ]
    for user_data in default_users:
        if not User.query.filter_by(username=user_data['username']).first():
            user = User(username=user_data['username'], birth_date=user_data['birth_date'], start_date=datetime.utcnow(), role=user_data['role'], status=user_data['status'])
            user.set_password(user_data['password'])
            db.session.add(user)
            print(f"Created user {user.username} with password: {user_data['password']}")
    db.session.commit()
