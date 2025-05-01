from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired

### Login Form ###
class LoginForm(FlaskForm):

### Registration Form ###
class RegistrationForm(FlaskForm):

### Location Form ###
class LocationForm(FlaskForm):

### Change Password Form ###
class ChangePasswordForm(FlaskForm):