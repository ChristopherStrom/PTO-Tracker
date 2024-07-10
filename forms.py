from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, DateField, IntegerField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
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

class TimeOffForm(FlaskForm):
    date = DateField('Date', validators=[DataRequired()])
    hours = IntegerField('Hours', validators=[DataRequired()])
    reason = SelectField('Reason', choices=[('pto', 'PTO'), ('emergency', 'Emergency'), ('vacation', 'Vacation')], validators=[DataRequired()])
    submit = SubmitField('Add Time Off')

class AddTimeForm(FlaskForm):
    category = SelectField('Category', choices=[('pto', 'PTO'), ('emergency', 'Emergency'), ('vacation', 'Vacation')], validators=[DataRequired()])
    hours = IntegerField('Hours', validators=[DataRequired()])
    submit = SubmitField('Add Time')

class EditBucketForm(FlaskForm):
    category = SelectField('Category', choices=[('pto', 'PTO'), ('emergency', 'Emergency'), ('vacation', 'Vacation')], validators=[DataRequired()])
    new_value = IntegerField('New Value', validators=[DataRequired()])
    submit = SubmitField('Update Bucket')
