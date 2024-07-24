# utils/init.py
import os
import sys
from datetime import datetime, date
from app import app, db
from models import User, Period

def create_admin(username, password):
    admin = User.query.filter_by(username=username).first()
    if admin:
        admin.set_password(password)
        print(f'Admin user {username} already exists. Password has been updated.')
    else:
        admin = User(username=username, role='admin', status='active', birth_date=date(1970, 1, 1), start_date=date(2022, 1, 1))
        admin.set_password(password)
        db.session.add(admin)
        print(f'Admin user {username} has been created with password: {password}')
    db.session.commit()
    generate_periods(admin)

def generate_periods(user):
    current_date = datetime.utcnow().date()
    hire_date = user.start_date
    periods = []
    period_start = date(hire_date.year, hire_date.month, 1)
    period_end = (period_start.replace(month=period_start.month % 12 + 1) - timedelta(days=1)).replace(day=1) - timedelta(days=1)

    while period_end < current_date:
        periods.append(Period(start_date=period_start, end_date=period_end, user_id=user.id))
        period_start = period_end + timedelta(days=1)
        period_end = (period_start.replace(month=period_start.month % 12 + 1) - timedelta(days=1)).replace(day=1) - timedelta(days=1)

    periods.append(Period(start_date=period_start, end_date=current_date, user_id=user.id, is_current=True))
    db.session.bulk_save_objects(periods)
    db.session.commit()

with app.app_context():
    db.create_all()

    admin_username = os.getenv('ADMIN_USERNAME', 'admin')
    admin_password = os.getenv('ADMIN_PASSWORD', 'password')

    create_admin(admin_username, admin_password)

    users = User.query.all()
    for user in users:
        generate_periods(user)
