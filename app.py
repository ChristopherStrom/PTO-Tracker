from flask import Flask, render_template, url_for, flash, redirect, request, session, make_response, send_from_directory, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
from flask_migrate import Migrate
from config import Config
from models import db, login_manager, User, TimeOff, calculate_earned_pto, BucketChange, Note
from forms import LoginForm, AddUserForm, EditUserForm, TimeOffForm, AddTimeForm, EditBucketForm, NoteForm
from datetime import datetime, timedelta
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import func
from wtforms import HiddenField
from flask_wtf import FlaskForm
from weasyprint import HTML, CSS 
import random
import string
import logging
import io
import shutil
import sys
import os


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

            pto_total = round(initial_pto_total - used_pto_hours, 2)
            emergency_total = round(initial_emergency_total - used_emergency_hours, 2)
            vacation_total = round(initial_vacation_total - used_vacation_hours, 2)

            user_data.append({
                'user': user,
                'pto_total': pto_total,
                'emergency_total': emergency_total,
                'vacation_total': vacation_total
            })

        form = HiddenForm()
        current_date = datetime.today().date()  # Get the current date

        return render_template('dashboard.html', user_data=user_data, filter_role=filter_role, form=form, current_date=current_date)
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
        user.start_period = form.start_period.data
        user.end_period = form.end_period.data
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
    year = request.args.get('year', None, type=int)

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

    # Calculate earned PTO time using start and end periods
    earned_pto = calculate_earned_pto(user.start_period, user.end_period)
    
    # Determine all years present in the user's time off history
    years = db.session.query(func.extract('year', TimeOff.date)).filter_by(user_id=user_id).group_by(func.extract('year', TimeOff.date)).all()
    years = [int(y[0]) for y in years]
    
    if year is None and years:
        year = max(years)  # Default to the most recent year if no year is selected

    time_offs = TimeOff.query.filter_by(user_id=user_id).filter(db.extract('year', TimeOff.date) == year).order_by(TimeOff.date.desc()).all()
    bucket_changes = BucketChange.query.filter_by(user_id=user_id).order_by(BucketChange.date.desc()).all()
    notes = Note.query.filter_by(user_id=user_id).order_by(Note.date.desc()).all()

    # PDF export
    if 'export' in request.args and request.args.get('export') == 'pdf':
        rendered = render_template(
            'export_user.html', 
            user=user, 
            bucket_changes=bucket_changes, 
            time_offs=time_offs, 
            initial_pto_total=initial_pto_total, 
            used_pto_hours=used_pto_hours, 
            pto_total=pto_total, 
            initial_emergency_total=initial_emergency_total, 
            used_emergency_hours=used_emergency_hours, 
            emergency_total=emergency_total, 
            initial_vacation_total=initial_vacation_total, 
            used_vacation_hours=used_vacation_hours, 
            vacation_total=vacation_total
        )
        pdf = HTML(string=rendered).write_pdf()
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename=user_details.pdf'
        return response

    return render_template(
        'view_user.html', 
        user=user, 
        form=form, 
        note_form=note_form, 
        bucket_changes=bucket_changes, 
        time_offs=time_offs, 
        year=year, 
        years=years,
        datetime=datetime, 
        initial_pto_total=initial_pto_total, 
        used_pto_hours=used_pto_hours, 
        pto_total=pto_total, 
        initial_emergency_total=initial_emergency_total, 
        used_emergency_hours=used_emergency_hours, 
        emergency_total=emergency_total, 
        initial_vacation_total=initial_vacation_total, 
        used_vacation_hours=used_vacation_hours, 
        vacation_total=vacation_total,
        earned_pto=earned_pto,
        all_users=all_users, 
        notes=notes,
    )

@app.route('/dashboard_pdf')
@login_required
def dashboard_pdf():
    if current_user.role != 'admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard'))
    
    # Fetch user data similar to the dashboard route
    users = User.query.order_by(func.lower(User.username).asc()).all()
    user_data = []

    for user in users:
        initial_pto_total = db.session.query(func.sum(BucketChange.new_value)).filter_by(user_id=user.id, category='pto').scalar() or 0
        initial_emergency_total = db.session.query(func.sum(BucketChange.new_value)).filter_by(user_id=user.id, category='emergency').scalar() or 0
        initial_vacation_total = db.session.query(func.sum(BucketChange.new_value)).filter_by(user_id=user.id, category='vacation').scalar() or 0

        used_pto_hours = db.session.query(func.sum(TimeOff.hours)).filter_by(user_id=user.id, reason='pto').scalar() or 0
        used_emergency_hours = db.session.query(func.sum(TimeOff.hours)).filter_by(user_id=user.id, reason='emergency').scalar() or 0
        used_vacation_hours = db.session.query(func.sum(TimeOff.hours)).filter_by(user_id=user.id, reason='vacation').scalar() or 0

        pto_total = round(initial_pto_total - used_pto_hours, 2)
        emergency_total = round(initial_emergency_total - used_emergency_hours, 2)
        vacation_total = round(initial_vacation_total - used_vacation_hours, 2)

        user_data.append({
            'user': user,
            'pto_total': pto_total,
            'emergency_total': emergency_total,
            'vacation_total': vacation_total
        })

    # Get the current timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Render the PDF template without filter or actions, including the timestamp
    rendered = render_template('dashboard_pdf.html', user_data=user_data, timestamp=timestamp)

    # Define CSS for landscape orientation and timestamp positioning
    css = CSS(string='''
        @page { 
            size: A4 landscape; 
            margin: 1cm; 
        }
        .timestamp {
            position: fixed;
            bottom: 0;
            right: 0;
            font-size: 8px;
            color: grey;
        }
    ''')

    # Generate the PDF with landscape orientation and timestamp CSS
    pdf = HTML(string=rendered).write_pdf(stylesheets=[css])

    # Send the PDF as a downloadable file
    return send_file(
        io.BytesIO(pdf),
        mimetype='application/pdf',
        download_name='dashboard_report.pdf',
        as_attachment=True
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
    if current_user.role != 'admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    form = AddTimeForm()

    if form.validate_on_submit():
        # Ensure the hours fields are initialized to 0.0 if they are None
        if user.pto_hours is None:
            user.pto_hours = 0.0
        if user.emergency_hours is None:
            user.emergency_hours = 0.0
        if user.vacation_hours is None:
            user.vacation_hours = 0.0

        # Update the appropriate bucket
        if form.category.data == 'PTO':
            user.pto_hours += form.hours.data
        elif form.category.data == 'Emergency':
            user.emergency_hours += form.hours.data
        elif form.category.data == 'Vacation':
            user.vacation_hours += form.hours.data
        
        # Create a new bucket change record
        bucket_change = BucketChange(
            category=form.category.data,
            old_value=0,  # For add time, old value is considered as 0
            new_value=form.hours.data,
            user_id=user.id
        )
        db.session.add(bucket_change)

        db.session.commit()
        flash(f'Added {form.hours.data} hours to {form.category.data} for {user.username}', 'success')
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

@app.route('/reset_period/<int:user_id>')
@login_required
def reset_period(user_id):
    if current_user.role != 'admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(user_id)

    # Log user information
    logging.info(f"Resetting period for user: {user.username}")

    try:
        # Collect data before deletion
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
        time_offs = TimeOff.query.filter_by(user_id=user_id).order_by(TimeOff.date.desc()).all()

        # Update user object for current state
        user.pto_hours = pto_total
        user.emergency_hours = emergency_total
        user.vacation_hours = vacation_total

        # Generate PDF
        rendered = render_template('user_report.html', user=user, bucket_changes=bucket_changes, time_offs=time_offs, initial_pto_total=initial_pto_total, used_pto_hours=used_pto_hours, pto_total=pto_total, initial_emergency_total=initial_emergency_total, used_emergency_hours=used_emergency_hours, emergency_total=emergency_total, initial_vacation_total=initial_vacation_total, used_vacation_hours=used_vacation_hours, vacation_total=vacation_total)
        pdf = HTML(string=rendered).write_pdf()

        # Save PDF to a file in the archive
        archive_folder = os.path.join(app.static_folder, 'archive')
        os.makedirs(archive_folder, exist_ok=True)  # Ensure the archive folder exists
        logging.info(f"Archive folder exists or created: {archive_folder}")

        # Build the filename with username, start period, and end period
        pdf_filename = f'{user.username}_{user.start_period}_{user.end_period or "N_A"}.pdf'.replace(' ', '_').replace(':', '-')
        
        # Handle existing files by appending a counter
        original_pdf_filename = pdf_filename
        counter = 1
        while os.path.exists(os.path.join(archive_folder, pdf_filename)):
            pdf_filename = f'{original_pdf_filename.split(".pdf")[0]}-{counter}.pdf'
            counter += 1
        
        pdf_path = os.path.join(archive_folder, pdf_filename)
        with open(pdf_path, 'wb') as f:
            f.write(pdf)
        logging.info(f"PDF saved at {pdf_path}")

        # Provide a download link for the PDF
        download_link = url_for('download_pdf', filename=pdf_filename)

        return render_template('reset_period.html', download_link=download_link, user_id=user_id, username=user.username)
    except Exception as e:
        logging.error(f"Error resetting period for user: {user.username}, error: {str(e)}")
        flash('An error occurred while resetting the period. Please try again.', 'danger')
        return redirect(url_for('view_user', user_id=user_id))

@app.route('/complete_reset_period/<int:user_id>')
@login_required
def complete_reset_period(user_id):
    if current_user.role != 'admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(user_id)

    try:
        # Delete all time off and bucket entries for the user
        TimeOff.query.filter_by(user_id=user_id).delete()
        BucketChange.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        logging.info(f"Deleted all time off and bucket changes for user: {user.username}")

        # Flash message
        flash(f'Reset period for {user.username}. Please update the period dates.', 'success')
    except Exception as e:
        logging.error(f"Error completing reset period for user: {user.username}, error: {str(e)}")
        flash('An error occurred while completing the reset period. Please try again.', 'danger')
        return redirect(url_for('view_user', user_id=user_id))

    # Redirect to the edit user page
    return redirect(url_for('edit_user', user_id=user_id))

@app.route('/download_pdf/<path:filename>', methods=['GET'])
@login_required
def download_pdf(filename):
    if current_user.role != 'admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard'))

    archive_folder = os.path.join(app.static_folder, 'archive')
    logging.info(f"Serving PDF from archive folder: {archive_folder}")
    return send_from_directory(directory=archive_folder, path=filename, as_attachment=True)
    
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
