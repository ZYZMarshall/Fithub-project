######################################################################################################
# Database models for Fithub users using SQLAlchemy.                                              #
# Models for user data, user fitness profile data, user workout schedule data, user exercises data,  #
# and user nutritional data (macros and meals).                                                      #
#                                                                                                    #                                                                             #
######################################################################################################

from datetime import datetime
from fithub import db, login_manager
from flask import current_app
from flask_login import UserMixin
from itsdangerous import JSONWebSignatureSerializer as Serializer

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# A SQLAlchemy Model instance for user data.
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)

    username = db.Column(db.String(20), unique = True, nullable = False)

    first_name = db.Column(db.String(50), unique = False, nullable = False)
    last_name = db.Column(db.String(50), unique = False, nullable = False)

    email = db.Column(db.String(120), unique = True, nullable = False)

    profile_image = db.Column(db.String(20), unique = False, nullable = False, default = 'default_image.jpg')

    password = db.Column(db.String(60), nullable = False)

    date_joined = db.Column(db.String, nullable = False, default = datetime.strftime(datetime.today(), "%b %d %Y"))

    profile = db.relationship('Profile', backref = 'user', lazy = True)

    meal = db.relationship('Meal', backref = 'user', lazy = True)

    posts = db.relationship('Post', backref='author', lazy=True)#lazy=True means db will load the data as neccessary in one go. 
    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.profile_image}', '{self.date_joined}')"

    def get_reset_token(self, expires_sec=1800): #create a secret key when reset user info
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod  #no self parameter
    def verify_reset_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)



# A SQLAlchemy Model instance for user fitness profile data.
class Profile(db.Model):
    id = db.Column(db.Integer, unique = True, nullable = False, primary_key = True)

    weight = db.Column(db.Float, unique = False, nullable = False, default = 0)
    height = db.Column(db.Text, unique = False, nullable = False, default = "0'0")

    goal = db.Column(db.String, unique = False, nullable = False, default = "None")

    age = db.Column(db.Integer, unique = False, nullable = False, default = 0)
    gender = db.Column(db.String, unique = False, nullable = False, default = "None")

    location = db.Column(db.String, unique = False, nullable = True, default = "None")

    quote = db.Column(db.String, unique = False, nullable = True, default = "")

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)

    def __repr__(self):
        return f"Profile('{self.user_id}', '{self.weight}', '{self.height}', '{self.goal}', '{self.age}', '{self.gender}')"


# A SQLAlchemy Model instance for user workout schedule data.
class Schedule(db.Model):
    id = db.Column(db.Integer, unique = True, nullable = False, primary_key = True)

    day_of_week = db.Column(db.String, unique = False, nullable = False)
    workout = db.Column(db.String, unique = False, nullable = False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)

    def __repr__(self):
        return f"Schedule('{self.user_id}', '{self.day_of_week}', '{self.workout}')"

# A SQLAlchemy Model instance for user exercise data.
class Exercise(db.Model):
    id = db.Column(db.Integer, unique = True, nullable = False, primary_key = True)

    name = db.Column(db.String, unique = False, nullable = False)

    day = db.Column(db.String, unique = False, nullable = False)
    workout = db.Column(db.String, unique = False, nullable = False)

    num_sets = db.Column(db.Integer, unique = False, nullable = False)
    num_reps = db.Column(db.Integer, unique = False, nullable = False)

    difficulty = db.Column(db.String, unique = False, nullable = False, default = "None Given")

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)

    def __repr__(self):
        return f"Exercise('{self.user_id}', '{self.name}', '{self.day}', '{self.workout}', '{self.num_sets}', '{self.num_reps}', '{self.difficulty}')"


# A SQLAlchemy Model instance for user nutritional macros data.
class Macros(db.Model):
    id = db.Column(db.Integer, unique = True, nullable = False, primary_key = True)

    day = db.Column(db.String, nullable = False)

    # Daily macronutrient numbers the user sets.
    protein = db.Column(db.Integer, nullable = False, default = -1)
    carbs = db.Column(db.Integer, nullable = False, default = -1)
    fat = db.Column(db.Integer, nullable = False, default = -1)

    calories = db.Column(db.Integer, nullable = False, default = -1)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)

    def __repr__(self):
        return f"Nutrition({self.user_id}', '{self.protein}', '{self.carbs}', '{self.fat}', '{self.calories}')"


# A SQLAlchemy Model instance for user nutritional meal data.
class Meal(db.Model):
    id = db.Column(db.Integer, unique = True, nullable = False, primary_key = True)

    description = db.Column(db.String(500), nullable = True, default = "No Description Given")

    food_type = db.Column(db.String, nullable = False, default = "other.jpg")

    time = db.Column(db.DateTime, nullable = False, default = datetime.now)

    protein = db.Column(db.Integer, nullable = False, default = 0)
    carbs = db.Column(db.Integer, nullable = False, default = 0)
    fat = db.Column(db.Integer, nullable = False, default = 0)

    calories = db.Column(db.Integer, nullable = True, default = 0)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)

    def __repr__(self):
        return f"Meal('{self.user_id}', '{self.description}', '{self.time}', '{self.protein}', '{self.carbs}', '{self.fat}', '{self.calories}')"

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Post('{sef.title}, '{self.data_posted}')"