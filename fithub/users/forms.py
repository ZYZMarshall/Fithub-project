########################################################################################
# WTForms for user registration, login, profile creation, and user data entries/edits. #
#                                                                                      #                                                              #
########################################################################################

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField,SelectField,FloatField,RadioField,TextField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError,EqualTo, Regexp, ValidationError, NumberRange, AnyOf
from flask_login import current_user
from fithub.models import User

# A WTForms instance for user registration.
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators = [DataRequired(), Length(min = 1, max = 20)])

    first_name = StringField('First Name', validators = [DataRequired(), Length(min = 1)])
    last_name = StringField('Last Name', validators = [DataRequired(), Length(min = 1)])

    email = StringField('Email', validators = [DataRequired(), Email()])

    password = PasswordField('Password', validators = [DataRequired(), Length(min = 6)])
    confirm_password = PasswordField('Confirm Password', validators = [DataRequired(), Length(min = 6), EqualTo('password')])

    submit = SubmitField('Sign Up')


    """Check if the selected USERNAME already exists. If true, throw a validation error."""
    def validate_username(self, username):
        user = User.query.filter_by(username = username.data).first()

        if user:
            raise ValidationError('That username already exists. Please select another username.')

    """Check if the selected EMAIL is already associated with an account. If true, throw a validation error."""
    def validate_email(self, email):
        user = User.query.filter_by(email = email.data).first()

        if user:
            raise ValidationError('That email is already taken. Please select another email.')


# A WTForms instance for user login.
class LoginForm(FlaskForm):
    username = StringField('Username', validators = [DataRequired(), Length(min = 1, max = 20)])

    password = PasswordField('Password', validators = [DataRequired(), Length(min = 6)])

    remember = BooleanField('Remember Me')

    submit = SubmitField('Log In')


# A WTForms instance for user profile creation.
class ProfileForm(FlaskForm):
    weight = FloatField('What is your current weight (in lbs.)?', validators = [DataRequired(), NumberRange(min = 0)])

    height = TextField("What is your current height (ft.' in.)? ", validators = [DataRequired(), 
        Regexp('[3-7]\'\d{1,2}', message = "Wrong height format. If your height has no inches (e.g. 6 ft.), please place 0 in inches (e.g. 6'0). ")])

    goal = RadioField('What are your fitness goals?', choices = [('Weight Loss', 'Lose Weight'), ('Muscle Gain', 'Build Muscle')],
        validators = [DataRequired()])

    age = IntegerField('What is your age?', validators = [DataRequired(), NumberRange(min = 0)])

    gender = RadioField('What is your gender?', choices = [('Male', 'Male'), ('Female', 'Female')],  validators = [DataRequired()])

    location = StringField('Which city do you currently live in (e.g. Berkeley, CA)?')

    quote = StringField("Would you like to add a personal quote?")

    submit = SubmitField('Save Profile')


# A WTForms instance for changing an existing user's profile picture.
class ChangeProfilePicForm(FlaskForm):
    picture = FileField('Please select a picture (.jpg, .png, .gif).', validators = [FileAllowed(['jpg', 'png', 'jpeg', 'gif'])])

    submit = SubmitField('Update')


# A WTForms instance for changing a user's username and/or email.
class ChangeUserForm(FlaskForm):
    username = StringField('Username', validators = [DataRequired(), Length(min = 1, max = 20)])

    email = StringField('Email', validators = [DataRequired(), Email()])

    submit = SubmitField('Update')


    """Check if the selected USERNAME already exists. If true, throw a validation error."""
    def validate_username(self, username):
        if username.data != current_user.username:

            user = User.query.filter_by(username = username.data).first()

            if user:
                raise ValidationError('That username already exists. Please select another username.')

    """Check if the selected EMAIL is already associated with an account. If true, throw a validation error."""
    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email = email.data).first()

            if user:
                raise ValidationError('That email is already taken. Please select another email.')


# A WTForms instance for changing an existing user's password.
class ChangePasswordForm(FlaskForm):
    password = PasswordField('Password', validators = [DataRequired(), Length(min = 6)])
    confirm_password = PasswordField('Confirm Password', validators = [DataRequired(), Length(min = 6), EqualTo('password')])

    submit = SubmitField('Change Password')


class RequestResetForm(FlaskForm):
    email = StringField('Email', validators = [DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('There is no account with that email. You must register first.')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators = [DataRequired(), Length(min = 6)])
    confirm_password = PasswordField('Confirm Password', validators = [DataRequired(), Length(min = 6), EqualTo('password')])
    submit = SubmitField('Reset Password')

# A WTForms instance for adding or editing an exercise to/in a user's workout.
class AddExerciseForm(FlaskForm):
    name = StringField("Exercise Name:", validators = [DataRequired()])

    day = SelectField(u'Day of the Week:', choices=[('Monday', 'Monday'), ('Tuesday', 'Tuesday'), ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'), ('Friday', 'Friday'), ('Saturday', 'Saturday'), ('Sunday', 'Sunday')],
        validators = [DataRequired()])

    num_sets = IntegerField("Number of Sets:", validators = [DataRequired(), NumberRange(min = 0)])
    num_reps = IntegerField("Number of Reps:", validators = [DataRequired(), NumberRange(min = 0)])

    difficulty = SelectField(u'Exercise Difficulty (Optional):', choices=[('Novice', 'Novice'), ('Beginner', 'Beginner'), ('Intermediate', 'Intermediate'),
        ('Adanced', 'Advanced'), ('Expert', 'Expert')])

    submit = SubmitField("Submit")