from flask import Flask, render_template, url_for, flash, redirect, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
from flask_migrate import Migrate
from config import Config
from models import db, login_manager, User, TimeOff, BucketChange
from forms import LoginForm, AddUserForm, EditUserForm, TimeOffForm, AddTimeForm, EditBucketForm
from datetime import datetime
import random
import string

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager.init_app(app)
migrate = Migrate(app, db)

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
            return redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check username, password, and account status', 'danger')
    return render_template('login.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    filter_status = request.args.get('status', 'all')
    if current_user.role == 'admin':
        if filter_status == 'all':
            users = User.query.all()
        else:
            users = User.query.filter_by(status=filter_status).all()
    else:
        users = [current_user]
    return render_template('dashboard.html', users=users, filter_status=filter_status)

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
    form = EditUserForm()
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
    elif request.method == 'GET':
        form.username.data = user.username
        form.birth_date.data = user.birth_date
        form.start_date.data = user.start_date
        form.status.data = user.status
        form.role.data = user.role
    return render_template('edit_user.html', form=form, user=user)

@app.route('/view_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def view_user(user_id):
    user = User.query.get_or_404(user_id)
    if current_user.role != 'admin' and current_user.id != user_id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard'))
    form = EditBucketForm()
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
        return redirect(url_for('view_user', user_id=user.id))
    
    # Calculate the totals from bucket changes
    pto_total = db.session.query(db.func.sum(BucketChange.new_value)).filter_by(user_id=user_id, category='pto').scalar() or 0
    emergency_total = db.session.query(db.func.sum(BucketChange.new_value)).filter_by(user_id=user_id, category='emergency').scalar() or 0
    vacation_total = db.session.query(db.func.sum(BucketChange.new_value)).filter_by(user_id=user_id, category='vacation').scalar() or 0

    bucket_changes = BucketChange.query.filter_by(user_id=user_id).all()
    time_offs = TimeOff.query.filter_by(user_id=user_id).filter(db.extract('year', TimeOff.date) == year).all()

    return render_template('view_user.html', user=user, form=form, bucket_changes=bucket_changes, time_offs=time_offs, year=year, datetime=datetime, pto_total=pto_total, emergency_total=emergency_total, vacation_total=vacation_total)

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

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
