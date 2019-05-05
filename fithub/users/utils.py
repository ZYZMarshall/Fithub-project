import os
import secrets
from PIL import Image
from flask import url_for, current_app
from flask_mail import Message
from fithub import mail,db
from fithub.models import Macros, Schedule

"""Save the PICTURE filename to the User model, and copy the selected PICTURE to static/images. The user's profile picture will
   then be changed to display the selected PICTURE."""
def save_picture(picture):
    random_hex = secrets.token_hex(8)
    _, file_ext = os.path.splitext(picture.filename)

    picture_filename = random_hex + file_ext

    picture_path = os.path.join(current_app.root_path, 'static/images', picture_filename)

    output_size = (500, 500)
    i = Image.open(picture)
    i.thumbnail(output_size)

    i.save(picture_path)

    return picture_filename


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request.', sender='marshallzyz@gmail.com',
                     recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('users.reset_token', token=token, _external=True)}

If you did not make this request then  simply ignore this email and no change will be made.
    '''
    #_external=True means use absolute url
    mail.send(msg)

### Routes and functions to do with user creation, login, and management. ###


"""Initialize blank macros with temp. -1 values that triggers the webpage to prompt the newly-created user to
   set their macros. By WTForms restrictions, these values can never be negative again."""
def set_blank_macros(user_id):
    mon_macros = Macros(day = "Monday", protein = -1, carbs = -1, fat = -1, calories = -1, user_id = user_id)
    tu_macros = Macros(day = "Tuesday", protein = -1, carbs = -1, fat = -1, calories = -1, user_id = user_id)
    wed_macros = Macros(day = "Wednesday", protein = -1, carbs = -1, fat = -1, calories = -1, user_id = user_id)
    th_macros = Macros(day = "Thursday", protein = -1, carbs = -1, fat = -1, calories = -1, user_id = user_id)
    fr_macros = Macros(day = "Friday", protein = -1, carbs = -1, fat = -1, calories = -1, user_id = user_id)
    sat_macros = Macros(day = "Saturday", protein = -1, carbs = -1, fat = -1, calories = -1, user_id = user_id)
    sun_macros = Macros(day = "Sunday", protein = -1, carbs = -1, fat = -1, calories = -1, user_id = user_id)

    db.session.add(mon_macros)
    db.session.add(tu_macros)
    db.session.add(wed_macros)
    db.session.add(th_macros)
    db.session.add(fr_macros)
    db.session.add(sat_macros)
    db.session.add(sun_macros)


"""Initialize blank workout schedules with temp. string values that triggers the webpage to prompt the newly-created user to
   set their workouts for the week."""
def set_blank_schedule(user_id):
    schedule1 = Schedule(day_of_week = "Monday", workout = "None Set.", user_id = user_id)
    schedule2 = Schedule(day_of_week = "Tuesday", workout = "None Set.", user_id = user_id)
    schedule3 = Schedule(day_of_week = "Wednesday", workout = "None Set.", user_id = user_id)
    schedule4 = Schedule(day_of_week = "Thursday", workout = "None Set.", user_id = user_id)
    schedule5 = Schedule(day_of_week = "Friday", workout = "None Set.", user_id = user_id)
    schedule6 = Schedule(day_of_week = "Saturday", workout = "None Set.", user_id = user_id)
    schedule7 = Schedule(day_of_week = "Sunday", workout = "None Set.", user_id = user_id)

    db.session.add(schedule1)
    db.session.add(schedule2)
    db.session.add(schedule3)
    db.session.add(schedule4)
    db.session.add(schedule5)
    db.session.add(schedule6)
    db.session.add(schedule7)