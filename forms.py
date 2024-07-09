from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, DateField, IntegerField, SelectField
from wtforms.validators import DataRequired, Length

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class AddUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    start_date = DateField('Start Date', validators=[DataRequired()])
    birth_date = DateField('Birth Date', validators=[DataRequired()])
    submit = SubmitField('Add User')

class TimeOffForm(FlaskForm):
    date = DateField('Date', validators=[DataRequired()])
    hours = IntegerField('Hours', validators=[DataRequired()])
    reason = SelectField('Reason', choices=[('pto', 'PTO'), ('emergency', 'Emergency'), ('vacation', 'Vacation')], validators=[DataRequired()])
    submit = SubmitField('Add Time Off')
