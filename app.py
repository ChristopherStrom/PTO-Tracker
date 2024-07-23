from flask import Flask, render_template, url_for, flash, redirect, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
from flask_migrate import Migrate
from config import Config
from models import db, login_manager, User, TimeOff, BucketChange, Note
from forms import LoginForm, AddUserForm, EditUserForm, TimeOffForm, AddTimeForm, EditBucketForm, NoteForm
from datetime import datetime, timedelta
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import func
from wtforms import HiddenField
from flask_wtf import FlaskForm
import random
import string
import logging


class HiddenForm(FlaskForm):
    csrf_token = HiddenField()

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager.init_app(app)
csrf = CSRFProtect(app)
migrate = Migrate(app, db)

logging.basicConfig(level=logging.INFO)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data) and user.status == 'active':
            login_user(user, remember=form.remember.data)
            session.permanent = True  # Make the session permanent
            return redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check username, password, and account status', 'danger')
    return render_template('login.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    filter_role = request.args.get('role', 'all')
    try:
        if current_user.role == 'admin':
            if filter_role == 'all':
                users = User.query.order_by(func.lower(User.username).asc()).all()
            elif filter_role == 'admin':
                users = User.query.filter_by(role='admin').order_by(func.lower(User.username).asc()).all()
            else:
                users = User.query.filter_by(status=filter_role).order_by(func.lower(User.username).asc()).all()
        else:
            users = [current_user]

        # Calculate PTO, Emergency, and Vacation hours for each user
        user_data = []
        for user in users:
            initial_pto_total = db.session.query(func.sum(BucketChange.new_value)).filter_by(user_id=user.id, category='pto').scalar() or 0
            initial_emergency_total = db.session.query(func.sum(BucketChange.new_value)).filter_by(user_id=user.id, category='emergency').scalar() or 0
            initial_vacation_total = db.session.query(func.sum(BucketChange.new_value)).filter_by(user_id=user.id, category='vacation').scalar() or 0

            used_pto_hours = db.session.query(func.sum(TimeOff.hours)).filter_by(user_id=user.id, reason='pto').scalar() or 0
            used_emergency_hours = db.session.query(func.sum(TimeOff.hours)).filter_by(user_id=user.id, reason='emergency').scalar() or 0
            used_vacation_hours = db.session.query(func.sum(TimeOff.hours)).filter_by(user_id=user.id, reason='vacation').scalar() or 0

            pto_total = initial_pto_total - used_pto_hours
            emergency_total = initial_emergency_total - used_emergency_hours
            vacation_total = initial_vacation_total - used_vacation_hours

            user_data.append({
                'user': user,
                'pto_total': pto_total,
                'emergency_total': emergency_total,
                'vacation_total': vacation_total
            })

        form = HiddenForm()

        return render_template('dashboard.html', user_data=user_data, filter_role=filter_role, form=form)
    except Exception as e:
        logging.error(f"Error in dashboard route: {e}")
        flash('An error occurred while loading the dashboard.', 'danger')
        return redirect(url_for('login'))

@app.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if current_user.role != 'admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard'))
    form = AddUserForm()
    if form.validate_on_submit():
        hashed_password = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        user = User(username=form.username.data, birth_date=form.birth_date.data, start_date=form.start_date.data, status=form.status.data, role=form.role.data)
        user.set_password(hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'User {form.username.data} added with password {hashed_password}', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_user.html', form=form)

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if current_user.role != 'admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    form = EditUserForm(obj=user)
    
    if form.validate_on_submit():
        user.username = form.username.data
        user.birth_date = form.birth_date.data
        user.start_date = form.start_date.data
        user.status = form.status.data
        user.role = form.role.data
        if form.password.data:  # Update password if provided
            user.set_password(form.password.data)
        db.session.commit()
        flash('User updated successfully', 'success')
        return redirect(url_for('dashboard'))
    return render_template('edit_user.html', form=form, user=user)

@app.route('/view_user', methods=['GET', 'POST'])
@login_required
def view_user():
    user_id = request.args.get('user_id', current_user.id, type=int)
    user = User.query.get_or_404(user_id)
    all_users = User.query.order_by(func.lower(User.username)).all() if current_user.role == 'admin' else [current_user]

    form = EditBucketForm()
    note_form = NoteForm()
    year = request.args.get('year', datetime.utcnow().year, type=int)
    
    if form.validate_on_submit():
        old_value = 0
        if form.category.data == 'pto':
            old_value = user.pto_hours
            user.pto_hours = form.new_value.data
        elif form.category.data == 'emergency':
            old_value = user.emergency_hours
            user.emergency_hours = form.new_value.data
        elif form.category.data == 'vacation':
            old_value = user.vacation_hours
            user.vacation_hours = form.new_value.data

        bucket_change = BucketChange(category=form.category.data, old_value=old_value, new_value=form.new_value.data, user_id=user.id)
        db.session.add(bucket_change)
        db.session.commit()
        flash(f'{form.category.data.capitalize()} hours updated to {form.new_value.data}', 'success')
        return redirect(url_for('view_user', user_id=user.id, year=year))
    
    if note_form.validate_on_submit():
        note = Note(content=note_form.content.data, user_id=user.id)
        db.session.add(note)
        db.session.commit()
        flash('Note added successfully', 'success')
        return redirect(url_for('view_user', user_id=user.id, year=year))
    
    # Calculate the totals from bucket changes and time off, rounding to 2 decimal places
    initial_pto_total = round(db.session.query(func.sum(BucketChange.new_value)).filter_by(user_id=user_id, category='pto').scalar() or 0, 2)
    initial_emergency_total = round(db.session.query(func.sum(BucketChange.new_value)).filter_by(user_id=user_id, category='emergency').scalar() or 0, 2)
    initial_vacation_total = round(db.session.query(func.sum(BucketChange.new_value)).filter_by(user_id=user_id, category='vacation').scalar() or 0, 2)

    used_pto_hours = round(db.session.query(func.sum(TimeOff.hours)).filter_by(user_id=user_id, reason='pto').scalar() or 0, 2)
    used_emergency_hours = round(db.session.query(func.sum(TimeOff.hours)).filter_by(user_id=user_id, reason='emergency').scalar() or 0, 2)
    used_vacation_hours = round(db.session.query(func.sum(TimeOff.hours)).filter_by(user_id=user_id, reason='vacation').scalar() or 0, 2)

    pto_total = initial_pto_total - used_pto_hours
    emergency_total = initial_emergency_total - used_emergency_hours
    vacation_total = initial_vacation_total - used_vacation_hours

    bucket_changes = BucketChange.query.filter_by(user_id=user_id).order_by(BucketChange.date.desc()).all()
    time_offs = TimeOff.query.filter_by(user_id=user_id).filter(db.extract('year', TimeOff.date) == year).order_by(TimeOff.date.desc()).all()
    notes = Note.query.filter_by(user_id=user_id).order_by(Note.date.desc()).all()

    return render_template('view_user.html', user=user, form=form, note_form=note_form, bucket_changes=bucket_changes, time_offs=time_offs, year=year, datetime=datetime, initial_pto_total=initial_pto_total, used_pto_hours=used_pto_hours, pto_total=pto_total, initial_emergency_total=initial_emergency_total, used_emergency_hours=used_emergency_hours, emergency_total=emergency_total, initial_vacation_total=initial_vacation_total, used_vacation_hours=used_vacation_hours, vacation_total=vacation_total, all_users=all_users, notes=notes)

@app.route('/add_time_off/<int:user_id>', methods=['GET', 'POST'])
@login_required
def add_time_off(user_id):
    if current_user.role != 'admin' and current_user.id != user_id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard'))
    form = TimeOffForm()
    user = User.query.get_or_404(user_id)
    if form.validate_on_submit():
        try:
            # Calculate the total number of days between start and end dates
            delta = (form.end_date.data - form.start_date.data).days + 1
            # Calculate the hours per day
            hours_per_day = form.total_hours.data / delta
            # Create a TimeOff entry for each day
            for i in range(delta):
                date = form.start_date.data + timedelta(days=i)
                time_off = TimeOff(date=date, hours=hours_per_day, reason=form.reason.data, user_id=user.id)
                db.session.add(time_off)
            db.session.commit()
            flash(f'Successfully added {form.total_hours.data} hours of {form.reason.data} for {user.username}', 'success')
            return redirect(url_for('view_user', user_id=user.id))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {e}', 'danger')
    return render_template('add_time_off.html', form=form, user=user)


@app.route('/add_time/<int:user_id>', methods=['GET', 'POST'])
@login_required
def add_time(user_id):
    if current_user.role != 'admin' and current_user.id != user_id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard'))
    form = AddTimeForm()
    user = User.query.get_or_404(user_id)
    if form.validate_on_submit():
        old_value = 0
        new_value = 0
        if form.category.data == 'pto':
            old_value = user.pto_hours
            user.pto_hours += form.hours.data
            new_value = user.pto_hours
        elif form.category.data == 'emergency':
            old_value = user.emergency_hours
            user.emergency_hours += form.hours.data
            new_value = user.emergency_hours
        elif form.category.data == 'vacation':
            old_value = user.vacation_hours
            user.vacation_hours += form.hours.data
            new_value = user.vacation_hours
        
        bucket_change = BucketChange(category=form.category.data, old_value=old_value, new_value=new_value, user_id=user.id)
        db.session.add(bucket_change)
        db.session.commit()
        flash(f'Successfully added {form.hours.data} hours to {form.category.data} for {user.username}', 'success')
        return redirect(url_for('view_user', user_id=user.id))
    return render_template('add_time.html', form=form, user=user)


@app.route('/delete_time_off/<int:time_off_id>', methods=['POST'])
@login_required
def delete_time_off(time_off_id):
    time_off = TimeOff.query.get_or_404(time_off_id)
    user_id = time_off.user_id
    if current_user.role != 'admin' and current_user.id != user_id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard'))
    user = User.query.get_or_404(user_id)
    
    if time_off.reason == 'pto':
        user.pto_hours -= time_off.hours
    elif time_off.reason == 'emergency':
        user.emergency_hours -= time_off.hours
    elif time_off.reason == 'vacation':
        user.vacation_hours -= time_off.hours

    db.session.delete(time_off)
    db.session.commit()
    flash('Time off entry deleted successfully', 'success')
    return redirect(url_for('view_user', user_id=user_id))

@app.route('/delete_bucket_change/<int:bucket_change_id>', methods=['POST'])
@login_required
def delete_bucket_change(bucket_change_id):
    bucket_change = BucketChange.query.get_or_404(bucket_change_id)
    user_id = bucket_change.user_id
    if current_user.role != 'admin' and current_user.id != user_id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard'))
    user = User.query.get_or_404(user_id)
    
    if bucket_change.category == 'pto':
        user.pto_hours -= (bucket_change.new_value - bucket_change.old_value)
    elif bucket_change.category == 'emergency':
        user.emergency_hours -= (bucket_change.new_value - bucket_change.old_value)
    elif bucket_change.category == 'vacation':
        user.vacation_hours -= (bucket_change.new_value - bucket_change.old_value)

    db.session.delete(bucket_change)
    db.session.commit()
    flash('Bucket change entry deleted successfully', 'success')
    return redirect(url_for('view_user', user_id=user_id))

@app.route('/update_status/<int:user_id>', methods=['POST'])
@login_required
def update_status(user_id):
    if current_user.role != 'admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    new_status = request.form.get('status')
    if new_status:
        user.status = new_status
        db.session.commit()
        flash(f'User status updated to {new_status}', 'success')
    else:
        flash('Invalid status update request', 'danger')
    
    return redirect(url_for('dashboard'))

@app.route('/set_session')
def set_session():
    session['test'] = 'It works!'
    return 'Session variable set.'

@app.route('/get_session')
def get_session():
    return session.get('test', 'Session variable not set.')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
