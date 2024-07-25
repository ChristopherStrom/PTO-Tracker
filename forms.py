# forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class AddUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    birth_date = StringField('Birth Date', validators=[DataRequired()])
    start_date = StringField('Start Date', validators=[DataRequired()])
    status = SelectField('Status', choices=[('active', 'Active'), ('inactive', 'Inactive')])
    role = SelectField('Role', choices=[('admin', 'Admin'), ('user', 'User')])
    submit = SubmitField('Add User')

class EditUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    birth_date = StringField('Birth Date', validators=[DataRequired()])
    start_date = StringField('Start Date', validators=[DataRequired()])
    status = SelectField('Status', choices=[('active', 'Active'), ('inactive', 'Inactive')])
    role = SelectField('Role', choices=[('admin', 'Admin'), ('user', 'User')])
    password = PasswordField('Password', validators=[Length(min=6, max=20)])
    submit = SubmitField('Update User')

class TimeOffForm(FlaskForm):
    start_date = StringField('Start Date', validators=[DataRequired()])
    end_date = StringField('End Date', validators=[DataRequired()])
    total_hours = IntegerField('Total Hours', validators=[DataRequired()])
    reason = SelectField('Reason', choices=[('pto', 'PTO'), ('emergency', 'Emergency'), ('vacation', 'Vacation')])
    submit = SubmitField('Add Time Off')

class AddTimeForm(FlaskForm):
    category = SelectField('Category', choices=[('pto', 'PTO'), ('emergency', 'Emergency'), ('vacation', 'Vacation')])
    hours = IntegerField('Hours', validators=[DataRequired()])
    submit = SubmitField('Add Time')

class EditBucketForm(FlaskForm):
    category = SelectField('Category', choices=[('pto', 'PTO'), ('emergency', 'Emergency'), ('vacation', 'Vacation')])
    new_value = IntegerField('New Value', validators=[DataRequired()])
    submit = SubmitField('Update Bucket')

class NoteForm(FlaskForm):
    content = StringField('Content', validators=[DataRequired(), Length(min=1, max=500)])
    submit = SubmitField('Add Note')

class AddPeriodForm(FlaskForm):
    start_date = StringField('Start Date', validators=[DataRequired()])
    end_date = StringField('End Date', validators=[DataRequired()])
    user_id = IntegerField('User ID', validators=[DataRequired()])
    is_current = BooleanField('Is Current')
    submit = SubmitField('Add Period')

class HiddenForm(FlaskForm):
    submit = SubmitField('Hidden')

class BucketForm(FlaskForm):
    category = SelectField('Category', choices=[('pto', 'PTO'), ('emergency', 'Emergency'), ('vacation', 'Vacation')])
    new_value = IntegerField('New Value', validators=[DataRequired()])
    submit = SubmitField('Update Bucket')
