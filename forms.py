from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, DateField, IntegerField, FloatField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from models import User
from datetime import datetime

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class AddUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    birth_date = DateField('Birth Date', validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()])
    status = SelectField('Status', choices=[('active', 'Active'), ('inactive', 'Inactive')], validators=[DataRequired()])
    role = SelectField('Role', choices=[('user', 'User'), ('admin', 'Admin')], validators=[DataRequired()])
    submit = SubmitField('Add User')

class EditUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    birth_date = DateField('Birth Date', validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()])
    status = SelectField('Status', choices=[('active', 'Active'), ('inactive', 'Inactive')], validators=[DataRequired()])
    role = SelectField('Role', choices=[('user', 'User'), ('admin', 'Admin')], validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=0, max=20)])  # Allow empty password for no change
    submit = SubmitField('Update User')

class TimeOffForm(FlaskForm):
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=[DataRequired()])
    end_date = DateField('End Date', format='%Y-%m-%d', validators=[DataRequired()])
    total_hours = IntegerField('Total Hours', validators=[DataRequired()])
    reason = SelectField('Reason', choices=[('pto', 'PTO'), ('emergency', 'Emergency'), ('vacation', 'Vacation')], validators=[DataRequired()])
    submit = SubmitField('Submit')

class AddTimeForm(FlaskForm):
    category = SelectField('Category', choices=[('pto', 'PTO'), ('emergency', 'Emergency'), ('vacation', 'Vacation')], validators=[DataRequired()])
    hours = FloatField('Hours', validators=[DataRequired()])
    submit = SubmitField('Add Time')

class EditBucketForm(FlaskForm):
    category = SelectField('Category', choices=[('pto', 'PTO'), ('emergency', 'Emergency'), ('vacation', 'Vacation')], validators=[DataRequired()])
    new_value = FloatField('New Value', validators=[DataRequired()])
    submit = SubmitField('Update Bucket')
