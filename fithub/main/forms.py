
from datetime import datetime
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, TextField, PasswordField, SubmitField, DateTimeField, BooleanField, FloatField, IntegerField, RadioField, SelectField
from wtforms.validators import DataRequired, InputRequired, Length, Email, EqualTo, Regexp, ValidationError, NumberRange, AnyOf




# A WTForms instance for adding a workout to a user's weekly schedule.
class WorkoutForm(FlaskForm):
    workout = StringField("Workout (e.g. Chest Day, Cardio, Back and Biceps, Legs, etc.)", validators = [DataRequired()])

    day = SelectField(u'Day of the Week:', choices=[('Monday', 'Monday'), ('Tuesday', 'Tuesday'), ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'), ('Friday', 'Friday'), ('Saturday', 'Saturday'), ('Sunday', 'Sunday')],
        validators = [DataRequired()])

    reset = BooleanField("Delete all exercises associated with the previous workout.")

    submit = SubmitField("Set Workout")

# A WTForms instance for adding or editing macronutrient numbers to/in a user's nutritional profile.
class MacroForm(FlaskForm):
    day = SelectField(u"Day of Week:", choices = [("Monday", "Monday"), ("Tuesday", "Tuesday"), ("Wednesday", "Wednesday"),
        ("Thursday", "Thursday"), ("Friday", "Friday"), ("Saturday", "Saturday"), ("Sunday", "Sunday")],
        validators = [DataRequired()])

    protein = IntegerField("Daily Protein (g)", validators = [DataRequired(), NumberRange(min = 0)])
    carbs = IntegerField("Daily Carbohydrates (g)", validators = [DataRequired(), NumberRange(min = 0)])
    fat = IntegerField("Daily Fat (g)", validators = [DataRequired(), NumberRange(min = 0)])

    set_all = BooleanField("Set Macros for All Days of the Week")

    submit = SubmitField("Set Macros")


# A WTForms instance for adding or editing meal data to/in a user's nutritional profile.
class MealForm(FlaskForm):
    description = StringField('Description of your meal:')

    food_type = SelectField(u'Type of Meal:', choices=[('breakfast.jpg', 'Breakfast'), ('lunch.jpg', 'Lunch'), ('dinner.jpg', 'Dinner'),
        ('cheat_meal.jpg', 'Cheat Meal'), ('snack.jpg', 'Snack'), ('other.jpg', 'Other')],
        validators = [DataRequired()])

    time = DateTimeField("When did you approximately eat this meal? (example: 3/14/2018 3:14 PM)", format = '%m/%d/%Y %I:%M %p',
        default = datetime.now)

    protein = IntegerField("Amount of Protein (g)", validators = [InputRequired(), NumberRange(min = 0)])
    carbs = IntegerField("Amount of Carbohydrates (g)", validators = [InputRequired(), NumberRange(min = 0)])
    fat = IntegerField("Amount of Fat (g)", validators = [InputRequired(), NumberRange(min = 0)])

    submit = SubmitField("Add to My Log")
    update = SubmitField("Update My Meal")




