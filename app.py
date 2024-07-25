# app.py
from datetime import datetime, timedelta
from flask import Flask, render_template, url_for, flash, redirect, request, session, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
from flask_migrate import Migrate

from config import Config
from models import db, User, TimeOff, BucketChange, Note, Period
from forms import LoginForm, AddUserForm, EditUserForm, TimeOffForm, AddTimeForm, EditBucketForm, NoteForm, AddPeriodForm, HiddenForm
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import func
from flask_wtf import FlaskForm
from weasyprint import HTML
import random
import string
import logging
import io

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
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

        user_data = []
        for user in users:
            current_period = Period.query.filter_by(user_id=user.id, is_current=True).first()
            if not current_period:
                user_data.append({
                    'user': user,
                    'pto_total': 0,
                    'emergency_total': 0,
                    'vacation_total': 0,
                    'has_current_period': False
                })
            else:
                initial_pto_total = db.session.query(func.sum(BucketChange.new_value)).filter_by(user_id=user.id, category='pto', period_id=current_period.id).scalar() or 0
                initial_emergency_total = db.session.query(func.sum(BucketChange.new_value)).filter_by(user_id=user.id, category='emergency', period_id=current_period.id).scalar() or 0
                initial_vacation_total = db.session.query(func.sum(BucketChange.new_value)).filter_by(user_id=user.id, category='vacation', period_id=current_period.id).scalar() or 0

                used_pto_hours = db.session.query(func.sum(TimeOff.hours)).filter_by(user_id=user.id, reason='pto', period_id=current_period.id).scalar() or 0
                used_emergency_hours = db.session.query(func.sum(TimeOff.hours)).filter_by(user_id=user.id, reason='emergency', period_id=current_period.id).scalar() or 0
                used_vacation_hours = db.session.query(func.sum(TimeOff.hours)).filter_by(user_id=user.id, reason='vacation', period_id=current_period.id).scalar() or 0

                pto_total = round(initial_pto_total - used_pto_hours, 2)
                emergency_total = round(initial_emergency_total - used_emergency_hours, 2)
                vacation_total = round(initial_vacation_total - used_vacation_hours, 2)

                user_data.append({
                    'user': user,
                    'pto_total': pto_total,
                    'emergency_total': emergency_total,
                    'vacation_total': vacation_total,
                    'has_current_period': True
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
    current_period = Period.query.filter_by(user_id=user_id, is_current=True).first()
    
    form = EditUserForm(obj=user)
    
    if request.method == 'GET':
        if current_period:
            form.period_start_date.data = current_period.start_date
            form.period_end_date.data = current_period.end_date
    
    if form.validate_on_submit():
        user.username = form.username.data
        user.birth_date = form.birth_date.data
        user.start_date = form.start_date.data
        user.status = form.status.data
        user.role = form.role.data
        if form.password.data:  # Update password if provided
            user.set_password(form.password.data)
        
        if current_period:
            current_period.start_date = form.period_start_date.data
            current_period.end_date = form.period_end_date.data
        else:
            new_period = Period(
                start_date=form.period_start_date.data,
                end_date=form.period_end_date.data,
                is_current=True,
                user_id=user.id
            )
            db.session.add(new_period)
        
        db.session.commit()
        flash('User updated successfully', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('edit_user.html', form=form, user=user)
    
@app.route('/view_user/<int:user_id>', methods=['GET'])
@login_required
def view_user(user_id):
    user = User.query.get_or_404(user_id)
    current_period = Period.query.filter_by(user_id=user.id, is_current=True).first()
    
    if not current_period:
        flash('No current period set for this user. Please set a current period first.', 'danger')
        return redirect(url_for('dashboard'))

    initial_pto_total = round(db.session.query(func.sum(BucketChange.new_value)).filter_by(user_id=user.id, category='pto', period_id=current_period.id).scalar() or 0, 2)
    initial_emergency_total = round(db.session.query(func.sum(BucketChange.new_value)).filter_by(user_id=user.id, category='emergency', period_id=current_period.id).scalar() or 0, 2)
    initial_vacation_total = round(db.session.query(func.sum(BucketChange.new_value)).filter_by(user_id=user.id, category='vacation', period_id=current_period.id).scalar() or 0, 2)

    used_pto_hours = round(db.session.query(func.sum(TimeOff.hours)).filter_by(user_id=user.id, reason='pto', period_id=current_period.id).scalar() or 0, 2)
    used_emergency_hours = round(db.session.query(func.sum(TimeOff.hours)).filter_by(user_id=user.id, reason='emergency', period_id=current_period.id).scalar() or 0, 2)
    used_vacation_hours = round(db.session.query(func.sum(TimeOff.hours)).filter_by(user_id=user.id, reason='vacation', period_id=current_period.id).scalar() or 0, 2)

    pto_total = initial_pto_total - used_pto_hours
    emergency_total = initial_emergency_total - used_emergency_hours
    vacation_total = initial_vacation_total - used_vacation_hours

    time_offs = TimeOff.query.filter_by(user_id=user.id, period_id=current_period.id).order_by(TimeOff.date.desc()).all()
    bucket_changes = BucketChange.query.filter_by(user_id=user.id, period_id=current_period.id).order_by(BucketChange.date.desc()).all()
    notes = Note.query.filter_by(user_id=user.id).order_by(Note.date.desc()).all()

    return render_template(
        'view_user.html', 
        user=user, 
        current_period=current_period, 
        time_offs=time_offs, 
        bucket_changes=bucket_changes, 
        notes=notes, 
        pto_total=pto_total, 
        emergency_total=emergency_total, 
        vacation_total=vacation_total
    )

@app.route('/add_note/<int:user_id>', methods=['POST'])
@login_required
def add_note(user_id):
    form = NoteForm()
    if form.validate_on_submit():
        note = Note(content=form.content.data, user_id=user_id)
        db.session.add(note)
        db.session.commit()
        flash('Note added successfully', 'success')
    else:
        flash('Failed to add note', 'danger')
    return redirect(url_for('view_user', user_id=user_id))

@app.route('/delete_note/<int:note_id>', methods=['POST'])
@login_required
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    user_id = note.user_id
    if current_user.role != 'admin' and current_user.id != user_id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard'))
    
    db.session.delete(note)
    db.session.commit()
    flash('Note deleted successfully', 'success')
    return redirect(url_for('view_user', user_id=user_id))


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
            delta = (form.end_date.data - form.start_date.data).days + 1
            hours_per_day = form.total_hours.data / delta
            for i in range(delta):
                date = form.start_date.data + timedelta(days=i)
                time_off = TimeOff(date=date, hours=hours_per_day, reason=form.reason.data, user_id=user.id, period_id=current_period.id)
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
        
        bucket_change = BucketChange(category=form.category.data, old_value=old_value, new_value=new_value, user_id=user.id, period_id=current_period.id)
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

@app.route('/view_user_period', methods=['GET'])
@login_required
def view_user_period():
    user_id = request.args.get('user_id')
    user = User.query.get_or_404(user_id)

    current_period = Period.query.filter_by(user_id=user_id, is_current=True).first()
    
    time_offs = TimeOff.query.filter(
        TimeOff.user_id == user.id,
        TimeOff.period_id == current_period.id
    ).all()

    bucket_changes = BucketChange.query.filter(
        BucketChange.user_id == user.id,
        BucketChange.period_id == current_period.id
    ).all()

    return render_template('view_user_period.html', user=user, time_offs=time_offs, bucket_changes=bucket_changes,
                           current_period=current_period)

@app.route('/add_period', methods=['GET', 'POST'])
@login_required
def add_period():
    if current_user.role != 'admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard'))
    
    form = AddPeriodForm()
    if form.validate_on_submit():
        period = Period(
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            user_id=form.user_id.data,
            is_current=form.is_current.data
        )
        db.session.add(period)
        db.session.commit()
        flash('Period added successfully', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('add_period.html', form=form)
    
@app.route('/set_current_period/<int:period_id>', methods=['POST'])
@login_required
def set_current_period(period_id):
    if current_user.role != 'admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard'))

    period = Period.query.get_or_404(period_id)

    Period.query.filter_by(user_id=period.user_id).update({"is_current": False})

    period.is_current = True
    db.session.commit()

    flash('Current period updated successfully', 'success')
    return redirect(url_for('view_user_period', user_id=period.user_id))

@app.route('/delete_period/<int:period_id>', methods=['POST'])
@login_required
def delete_period(period_id):
    period = Period.query.get_or_404(period_id)
    user_id = period.user_id
    if current_user.role != 'admin' and current_user.id != user_id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard'))

    db.session.delete(period)
    db.session.commit()
    flash('Period deleted successfully', 'success')
    return redirect(url_for('view_user_period', user_id=user_id))

@app.route('/set_period/<int:user_id>', methods=['GET', 'POST'])
@login_required
def set_period(user_id):
    if current_user.role != 'admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(user_id)
    start_date = user.start_date
    period_start_date = start_date.replace(day=1)
    period_end_date = (start_date.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    existing_period = Period.query.filter_by(user_id=user_id, is_current=True).first()
    if existing_period:
        existing_period.start_date = period_start_date
        existing_period.end_date = period_end_date
    else:
        new_period = Period(
            start_date=period_start_date,
            end_date=period_end_date,
            is_current=True,
            user_id=user.id
        )
        db.session.add(new_period)
    
    db.session.commit()
    flash('Current period set successfully', 'success')
    return redirect(url_for('view_user', user_id=user_id))

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
