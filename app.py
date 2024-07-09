from flask import Flask, render_template, url_for, flash, redirect, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
from flask_migrate import Migrate
from config import Config
from models import db, login_manager, User, TimeOff, BucketChange
from forms import LoginForm, AddUserForm, TimeOffForm, AddTimeForm, EditBucketForm
from datetime import datetime, timedelta
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
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    users = User.query.all()
    return render_template('dashboard.html', users=users)

@app.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    form = AddUserForm()
    if form.validate_on_submit():
        hashed_password = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        user = User(username=form.username.data, birth_date=form.birth_date.data, start_date=form.start_date.data)
        user.set_password(hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'User {form.username.data} added with password {hashed_password}', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_user.html', form=form)

@app.route('/view_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def view_user(user_id):
    user = User.query.get_or_404(user_id)
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

    # Calculate the totals from time off entries and bucket changes
    pto_total = (db.session.query(db.func.sum(TimeOff.hours)).filter_by(user_id=user_id, reason='pto').scalar() or 0) + \
                (db.session.query(db.func.sum(BucketChange.new_value - BucketChange.old_value)).filter_by(user_id=user_id, category='pto').scalar() or 0)
    emergency_total = (db.session.query(db.func.sum(TimeOff.hours)).filter_by(user_id=user_id, reason='emergency').scalar() or 0) + \
                      (db.session.query(db.func.sum(BucketChange.new_value - BucketChange.old_value)).filter_by(user_id=user_id, category='emergency').scalar() or 0)
    vacation_total = (db.session.query(db.func.sum(TimeOff.hours)).filter_by(user_id=user_id, reason='vacation').scalar() or 0) + \
                     (db.session.query(db.func.sum(BucketChange.new_value - BucketChange.old_value)).filter_by(user_id=user_id, category='vacation').scalar() or 0)

    bucket_changes = BucketChange.query.filter_by(user_id=user_id).all()
    time_offs = TimeOff.query.filter_by(user_id=user_id).filter(db.extract('year', TimeOff.date) == year).all()

    return render_template('view_user.html', user=user, form=form, bucket_changes=bucket_changes, time_offs=time_offs, year=year, datetime=datetime, pto_total=pto_total, emergency_total=emergency_total, vacation_total=vacation_total)

@app.route('/add_time/<int:user_id>', methods=['GET', 'POST'])
@login_required
def add_time(user_id):
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


@app.route('/add_time_off/<int:user_id>', methods=['GET', 'POST'])
@login_required
def add_time_off(user_id):
    form = TimeOffForm()
    user = User.query.get_or_404(user_id)
    if form.validate_on_submit():
        time_off = TimeOff(date=form.date.data, hours=form.hours.data, reason=form.reason.data, user_id=user_id)
        db.session.add(time_off)

        if form.reason.data == 'pto':
            user.pto_hours += form.hours.data
        elif form.reason.data == 'emergency':
            user.emergency_hours += form.hours.data
        elif form.reason.data == 'vacation':
            user.vacation_hours += form.hours.data

        db.session.commit()
        flash('Time off added successfully', 'success')
        return redirect(url_for('view_user', user_id=user_id))
    return render_template('add_time_off.html', form=form, user=user)

@app.route('/delete_time_off/<int:time_off_id>', methods=['POST'])
@login_required
def delete_time_off(time_off_id):
    time_off = TimeOff.query.get_or_404(time_off_id)
    user_id = time_off.user_id
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


@app.route('/delete_time_off/<int:time_off_id>', methods=['POST'])
@login_required
def delete_time_off(time_off_id):
    time_off = TimeOff.query.get_or_404(time_off_id)
    user_id = time_off.user_id
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


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
