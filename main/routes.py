########################################################
# Routes for Fithub, and backend functions/methods. #
#                                                      #                                #
########################################################

import os
import operator
import secrets

from datetime import datetime
from urllib.parse import urlparse
from PIL import Image

import flask
from flask import render_template, url_for, flash, redirect, request, abort
from main import app, db, bcrypt, mail
from main.forms import (RegistrationForm, LoginForm, ProfileForm, ChangeProfilePicForm, 
ChangeUserForm, ChangePasswordForm, MacroForm, MealForm, AddExerciseForm, WorkoutForm, PostForm, RequestResetForm,ResetPasswordForm)
from main.models import User, Profile, Schedule, Exercise, Macros, Meal, Post
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message

# Route to the homepage.
@app.route("/")
@app.route("/home")
def home():
    page = request.args.get('page',1,type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(per_page=5)
    return render_template('home.html', posts=posts)


### Routes and functions to do with the fitness page. ###

# Route to the user's main fitness page.
@app.route("/my-fitness-page", methods = ['GET', 'POST'])
def fitness_page():
    return render_template('fitness-page.html', title = 'My Fitness Page')

@app.route("/course", methods=['GET','POST'])
def course():
    return render_template('course.html', title = 'Fitness Course')


### Routes and functions to do with the workouts page. ###

# Route to the user's main workouts page.
@app.route("/workouts")
def workouts():

    if current_user.is_authenticated:
        day = datetime.strftime(datetime.now(), "%A")
        workout = Schedule.query.filter(Schedule.user_id == current_user.id, Schedule.day_of_week == day).first().workout
        exercises = Exercise.query.filter(Exercise.user_id == current_user.id, Exercise.day == day).all()

        return render_template('workouts.html', title = 'Workouts', today = day, workout = workout, exercises = exercises)

    else:
        return redirect(url_for('home'))


# Route to the user's workouts page for selected DAY of week.
@app.route("/workouts/<day>")
@login_required
def workouts_day(day):
    workout = Schedule.query.filter(Schedule.user_id == current_user.id, Schedule.day_of_week == day).first().workout
    exercises = Exercise.query.filter(Exercise.user_id == current_user.id, Exercise.day == day).all()

    return render_template("workouts-day.html", title = "Daily Workout", day = day, workout = workout, exercises = exercises)


# Route to a WTForms instance to edit a workout for TODAY (by datetime).
@app.route("/workouts/<today>/update-workout1", methods = ['GET', 'POST'])
@login_required
def update_workout1(today):
    form = WorkoutForm()

    if form.validate_on_submit():
        workout = Schedule.query.filter(Schedule.user_id == current_user.id, Schedule.day_of_week == today).first()
        label = workout.workout

        if form.reset.data == True:
            exercises = Exercise.query.filter(Exercise.user_id == current_user.id, Exercise.day == today).all()

            for exercise in exercises:
                db.session.delete(exercise)

        workout.workout = form.workout.data

        db.session.commit()

        return redirect(url_for('workouts'))    

    elif request.method == 'GET':
        form.day.data = today

    return render_template('change-workout.html', title = "Change Workout", form = form)


# Route to a WTForms instance to edit a workout for a selected DAY.
@app.route("/workouts/<day>/update-workout2", methods = ['GET', 'POST'])
@login_required
def update_workout2(day):
    form = WorkoutForm()

    if form.validate_on_submit():
        workout = Schedule.query.filter(Schedule.user_id == current_user.id, Schedule.day_of_week == day).first()
        label = workout.workout

        if form.reset.data == True:
            exercises = Exercise.query.filter(Exercise.user_id == current_user.id, Exercise.day == day).all()

            for exercise in exercises:
                db.session.delete(exercise)

        workout.workout = form.workout.data

        db.session.commit()

        return redirect(url_for('workouts_day', day = day))    

    elif request.method == 'GET':
        form.day.data = day

    return render_template('change-workout.html', title = "Change Workout", form = form)


# Route to view the workouts schedule for the entire week. Not unique to different weeks.
@app.route("/workouts/view-schedule")
def view_schedule():

    today = datetime.today().strftime("%A")

    schedules = Schedule.query.filter(Schedule.user_id == current_user.id).all()
    num_exercises = [len(Exercise.query.filter(Exercise.user_id == current_user.id, Exercise.day == "Monday").all()),
                     len(Exercise.query.filter(Exercise.user_id == current_user.id, Exercise.day == "Tuesday").all()),
                     len(Exercise.query.filter(Exercise.user_id == current_user.id, Exercise.day == "Wednesday").all()),
                     len(Exercise.query.filter(Exercise.user_id == current_user.id, Exercise.day == "Thursday").all()),
                     len(Exercise.query.filter(Exercise.user_id == current_user.id, Exercise.day == "Friday").all()),
                     len(Exercise.query.filter(Exercise.user_id == current_user.id, Exercise.day == "Saturday").all()),
                     len(Exercise.query.filter(Exercise.user_id == current_user.id, Exercise.day == "Sunday").all())]

    return render_template('view-schedule.html', title = 'Workout Schedules', schedules = schedules, num_exercises = num_exercises, today = today)


# Route to a WTForms instance to add an exercise to TODAY's workout (by datetime).
@app.route("/workouts/<today>/add-exercise1", methods = ['GET', 'POST'])
@login_required
def add_exercise1(today):
    form = AddExerciseForm()

    if form.validate_on_submit():
        user_id = current_user.id
        day = form.day.data
        workout = Schedule.query.filter(Schedule.user_id == user_id, Schedule.day_of_week == day).first().workout

        if workout == "None Set.":
            flash("Please set a workout for that day first.", "danger")
            return redirect(url_for('workouts'))

        if form.difficulty.data == None:
            difficulty = "None Given"

        else:
            difficulty = form.difficulty.data

        exercise = Exercise(name = form.name.data, day = form.day.data, workout = workout, num_sets = form.num_sets.data,
            num_reps = form.num_reps.data, difficulty = difficulty, user_id = user_id)

        db.session.add(exercise)
        db.session.commit()

        return redirect(url_for('workouts'))

    elif request.method == 'GET':
        form.day.data = today

    return render_template('new-exercise.html', title = "Add Exercise", form = form)


# Route to a WTForms instance to add an exercise to the selected DAY's workout.
@app.route("/workouts/<day>/add-exercise2", methods = ['GET', 'POST'])
@login_required
def add_exercise2(day):

    form = AddExerciseForm()

    if form.validate_on_submit():
        user_id = current_user.id
        day = form.day.data
        workout = Schedule.query.filter(Schedule.user_id == user_id, Schedule.day_of_week == day).first().workout

        if workout == "None Set.":
            flash("Please set a workout for that day first.", "danger")
            return redirect(url_for('workouts'))

        if form.difficulty.data == None:
            difficulty = "None Given"

        else:
            difficulty = form.difficulty.data

        exercise = Exercise(name = form.name.data, day = form.day.data, workout = workout, num_sets = form.num_sets.data,
            num_reps = form.num_reps.data, difficulty = difficulty, user_id = user_id)

        db.session.add(exercise)
        db.session.commit()

        return redirect(url_for('workouts_day', day = day))

    elif request.method == 'GET':
        form.day.data = day

    return render_template('new-exercise.html', title = "Add Exercise", form = form)


# Route to a WTForms instance to add an exercise to any day of the week.
@app.route("/workouts/<exercise_name>/<difficulty>/add-exercise3")
@login_required
def add_exercise3(exercise_name, difficulty):

    form = AddExerciseForm()

    if form.validate_on_submit():
        user_id = current_user.id
        day = form.day.data
        workout = Schedule.query.filter(Schedule.user_id == user_id, Schedule.day_of_week == day).first().workout

        if workout == "None Set.":
            flash("Please set a workout for that day first.", "danger")
            return redirect(url_for('workouts'))

        if form.difficulty.data == None:
            difficulty = "None Given"

        else:
            difficulty = form.difficulty.data

        exercise = Exercise(name = form.name.data, day = form.day.data, workout = workout, num_sets = form.num_sets.data,
            num_reps = form.num_reps.data, difficulty = difficulty, user_id = user_id)

        db.session.add(exercise)
        db.session.commit()

        return redirect(url_for('workouts_day', day = day))

    elif request.method == 'GET':
        form.day.data = "Monday"
        form.name.data = exercise_name
        form.difficulty.data = difficulty

    return render_template('new-exercise.html', title = "Add Exercise", form = form)


# Route to a WTForms instance to edit a selected exercise in a selected DAY's workout, where the previous page was .
@app.route("/workouts/<day>/<exercise_id>/edit-exercise1", methods = ['GET', 'POST'])
@login_required
def edit_exercise1(day, exercise_id):
    exercise = Exercise.query.filter(Exercise.user_id == current_user.id, Exercise.id == exercise_id).first()

    form = AddExerciseForm()

    if form.validate_on_submit():

        if form.difficulty.data == None:
            difficulty = "None Given"

        else:
            difficulty = form.difficulty.data

        exercise.name = form.name.data
        exercise.day = form.day.data
        exercise.num_sets = form.num_sets.data
        exercise.num_reps = form.num_reps.data
        exercise.difficulty = difficulty

        db.session.commit()

        return redirect(url_for('workouts'))

    elif request.method == 'GET':
        form.name.data = exercise.name
        form.day.data = day
        form.num_sets.data = exercise.num_sets
        form.num_reps.data = exercise.num_reps
        form.difficulty.data = exercise.difficulty

    return render_template('new-exercise.html', title = "Add Exercise", form = form)


# Route to a WTForms instance to edit a selected exercise in a selected DAY's workout, where the previous page was .
@app.route("/workouts/<day>/<exercise_id>/edit-exercise2", methods = ['GET', 'POST'])
@login_required
def edit_exercise2(day, exercise_id):
    exercise = Exercise.query.filter(Exercise.user_id == current_user.id, Exercise.id == exercise_id).first()

    form = AddExerciseForm()

    if form.validate_on_submit():

        if form.difficulty.data == None:
            difficulty = "None Given"

        else:
            difficulty = form.difficulty.data

        exercise.name = form.name.data
        exercise.day = form.day.data
        exercise.num_sets = form.num_sets.data
        exercise.num_reps = form.num_reps.data
        exercise.difficulty = difficulty

        db.session.commit()

        return redirect(url_for('workouts_day', day = day))

    elif request.method == 'GET':
        form.name.data = exercise.name
        form.day.data = day
        form.num_sets.data = exercise.num_sets
        form.num_reps.data = exercise.num_reps
        form.difficulty.data = exercise.difficulty

    return render_template('new-exercise.html', title = "Add Exercise", form = form)


# Route to the main Fithub exercises database.
@app.route("/workouts/database")
@login_required
def exercise_db():
    today = datetime.today().strftime("%A")


    return render_template('exercise-db.html', title = "Exercise Database", today = today)


# Route to the Fithub exercises database for leg workouts, page 1.
@app.route("/workouts/database/legs1")
@login_required
def exercise_db_legs1():
    today = datetime.today().strftime("%A")

    return render_template('exercise-db-legs1.html', title = "Exercise Database: Legs", today = today)


# Route to the Fithub exercises database for leg workouts, page 2.
@app.route("/workouts/database/legs2")
@login_required
def exercise_db_legs2():
    today = datetime.today().strftime("%A")

    return render_template('exercise-db-legs2.html', title = "Exercise Database: Legs", today = today)


### Routes and functions to do with the nutrition page. ###

"""Return an integer for the remaining macros for a selected day. The selected day has user-set MACROS numbers, 
   and TODAYS_MEALS contains the macros eaten so far today."""
def get_remaining_macros(macros, todays_meals):
    remaining_macros = [macros.protein - sum([x.protein for x in todays_meals]),
                        macros.carbs - sum([x.carbs for x in todays_meals]),
                        macros.fat - sum([x.fat for x in todays_meals]),
                        macros.calories - sum([x.calories for x in todays_meals])]

    return remaining_macros


# Route to the main nutrition page.
@app.route("/nutrition", methods = ['GET', 'POST'])
def nutrition():
    today = datetime.today()
    current_day = today.strftime("%A")

    if current_user.is_authenticated:
        macros = Macros.query.filter(Macros.user_id == current_user.id, Macros.day == current_day).first()
        meals = Meal.query.filter(Meal.user_id == current_user.id).all()
        todays_meals = [x for x in meals if x.time.strftime('%d-%m-%Y') == today.strftime('%d-%m-%Y')]

        remaining = get_remaining_macros(macros, todays_meals)

        return render_template('nutrition.html', title = 'Nutrition', macros = macros, remaining = remaining, meals = todays_meals,
            today = datetime.today())

    else:
        return render_template('nutrition.html', title = 'Nutrition', today = datetime.today())


# Route to a WTForms instance for setting or editing TODAY's macros (by datetime).
@app.route("/nutrition/set-macros/today", methods = ['GET', 'POST'])
@login_required
def set_macros():
    form = MacroForm()
    day = datetime.today().strftime("%A")

    if form.validate_on_submit():
        if form.set_all.data == True:
            macros = Macros.query.filter(Macros.user_id == current_user.id).all()

            calories = 4*form.protein.data + 4*form.carbs.data + 9*form.fat.data

            for m in macros:
                m.protein = form.protein.data
                m.carbs = form.carbs.data
                m.fat = form.fat.data
                m.calories = calories

            db.session.commit()

        else:
            macros = Macros.query.filter(Macros.user_id == current_user.id, Macros.day == form.day.data).first()

            calories = 4*form.protein.data + 4*form.carbs.data + 9*form.fat.data

            macros.protein = form.protein.data
            macros.carbs = form.carbs.data
            macros.fat = form.fat.data
            macros.calories = calories

            db.session.commit()

        flash("You have set your daily macros.", "success")

        return redirect(url_for('nutrition'))

    elif request.method == 'GET':
        form.day.data = day

    return render_template('set-macros.html', title = "Set Macros", form = form)


# Route to a WTForms instance for setting or editing any WEEKDAY's macros.
@app.route("/nutrition/set-macros/<weekday>", methods = ['GET', 'POST'])
@login_required
def set_macros2(weekday):
    form = MacroForm()
    day = datetime.today().strftime("%A")

    if form.validate_on_submit():
        if form.set_all.data == True:
            macros = Macros.query.filter(Macros.user_id == current_user.id).all()

            calories = 4*form.protein.data + 4*form.carbs.data + 9*form.fat.data

            for m in macros:
                m.protein = form.protein.data
                m.carbs = form.carbs.data
                m.fat = form.fat.data
                m.calories = calories

            db.session.commit()

        else:
            macros = Macros.query.filter(Macros.user_id == current_user.id, Macros.day == form.day.data).first()

            calories = 4*form.protein.data + 4*form.carbs.data + 9*form.fat.data

            macros.protein = form.protein.data
            macros.carbs = form.carbs.data
            macros.fat = form.fat.data
            macros.calories = calories

            db.session.commit()

        flash("You have set your daily macros.", "success")

        return redirect(url_for('view_macros'))

    elif request.method == 'GET':
        form.day.data = weekday

    return render_template('set-macros.html', title = "Set Macros", form = form)


# Route to a webpage that displays the macros for all 7 days of the week.
@app.route("/nutrition/view-macros")
@login_required
def view_macros():
    macros = Macros.query.filter(Macros.user_id == current_user.id).all()

    return render_template('view-macros.html', title = "View Macros", macros = macros)


# Route to a WTForms instance for adding a new meal, where the previous page was .
@app.route("/nutrition/new-meal", methods = ['GET', 'POST'])
@login_required
def new_meal1():
    form = MealForm()

    if form.validate_on_submit():
        calories = 4*form.protein.data + 4*form.carbs.data + 9*form.fat.data

        meal = Meal(description = form.description.data, food_type = form.food_type.data, time = form.time.data, protein = form.protein.data,
            carbs = form.carbs.data, fat = form.fat.data, calories = calories, user_id = current_user.id)

        db.session.add(meal)
        db.session.commit()

        flash("You have successfully logged your meal.", "success")
        return redirect(url_for('nutrition'))

    return render_template('new-meal.html', title = "New Meal", form = form)


# Route to a WTForms instance for adding a new meal, where the previous page was .
@app.route("/nutrition/meal-log/new-meal", methods = ['GET', 'POST'])
@login_required
def new_meal2():
    form = MealForm()

    if form.validate_on_submit():
        calories = 4*form.protein.data + 4*form.carbs.data + 9*form.fat.data

        meal = Meal(description = form.description.data, food_type = form.food_type.data, time = form.time.data, protein = form.protein.data,
            carbs = form.carbs.data, fat = form.fat.data, calories = calories, user_id = current_user.id)

        db.session.add(meal)
        db.session.commit()

        flash("You have successfully logged your meal.", "success")
        return redirect(url_for('meal_log'))

    return render_template('new-meal.html', title = "New Meal", form = form)


# Route to the user's meal log, a webpage that contains data about all meals eaten today (by datetime).
@app.route("/nutrition/meal-log")
@login_required
def meal_log():
    today = datetime.today()

    meals = Meal.query.filter(Meal.user_id == current_user.id).all()
    todays_meals = [x for x in meals if x.time.strftime('%d-%m-%Y') == today.strftime('%d-%m-%Y')]

    sorted_meals = sorted(todays_meals, key = operator.attrgetter('calories'))

    return render_template('meal-log.html', title = "Meal Log", meals = todays_meals, sorted_meals = sorted_meals,
        today = datetime.today())


# Route to a WTForms instance for editing the data for a meal with MEAL_ID.
@app.route("/nutrition/meal-log/<int:meal_id>/update-meal", methods = ['GET', 'POST'])
@login_required
def update_meal(meal_id):
    meal = Meal.query.filter(Meal.user_id == current_user.id, Meal.id == meal_id).first()

    if meal.user != current_user:
        abort(403)

    form = MealForm()

    if form.validate_on_submit():
        meal.description = form.description.data
        meal.food_type = form.food_type.data
        meal.time = form.time.data
        meal.protein = form.protein.data
        meal.carbs = form.carbs.data
        meal.fat = form.fat.data

        meal.calories = 4*form.protein.data + 4*form.carbs.data + 9*form.fat.data

        db.session.commit()

        return redirect(url_for('meal_log'))

    elif request.method == 'GET':
        form.description.data = meal.description
        form.food_type.data = meal.food_type
        form.time.data = meal.time
        form.protein.data = meal.protein
        form.carbs.data = meal.carbs
        form.fat.data = meal.fat

    return render_template('update-meal.html', title = "Edit Your Meal", form = form)


# Route for deleting all the data for a meal with MEAL_ID (and subsequently deleting the meal itself).
@app.route("/nutrition/meal-log/<int:meal_id>/delete-meal", methods = ['GET'])
@login_required
def delete_meal(meal_id):
    meal = Meal.query.filter(Meal.user_id == current_user.id, Meal.id == meal_id).first()

    if meal.user != current_user:
        abort(403)

    db.session.delete(meal)
    db.session.commit()

    flash("You have successfully deleted your meal.", "success")
    return redirect(url_for('meal_log'))


# Route to the Fithub nutritional resources page.
@app.route("/nutrition/nutrition-resources")
@login_required
def nutrition_resources():
    return render_template('nutr-res.html', title = "Nutrition Resources")


# Route to the Fithub nutritional resources page about macronutrients.
@app.route("/nutrition/nutrition-resources/macros101")
@login_required
def nutr_res_macros():
    return render_template('nutr-res-macros.html', title = "Macros 101")


### Routes and functions to do with the community page. ###


# Route to the user community page.
@app.route("/community")
def community():
    page = request.args.get('page',1,type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(per_page=5)
    return render_template('community.html', title = 'Community',posts=posts)


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


# Route for a new user profile creation. This route finalizes new user registration from REGISTER (next route).
@app.route("/profile-creation/<username>", methods = ['GET', 'POST'])
def profile_creation(username):
    form = ProfileForm()

    if form.validate_on_submit():

        username = flask.session['user']
        first_name = flask.session['first_name']
        last_name = flask.session['last_name']
        email = flask.session['email']
        password = flask.session['password']

        user = User(username = username, first_name = first_name, last_name = last_name, email = email,
            password = password)

        db.session.add(user)
        db.session.commit()

        user_id = user.id

        profile = Profile(weight = form.weight.data, height = form.height.data, goal = form.goal.data, age = form.age.data,
            gender = form.gender.data, location = form.location.data, quote = form.quote.data, user_id = user_id)

        db.session.add(profile)
        set_blank_macros(user_id)
        set_blank_schedule(user_id)

        db.session.commit()

        login_user(user)

        flash(f'You have successfully created your account!', 'success')

        return redirect(url_for('fitness_page'))

    return render_template('profile-creation.html', title = "Create Your Profile", form = form)


# Route for registering a new user. The data from this page gets saved to the current Flask session, and the new user is created
# only if the user successfully completes PROFILE_CREATION (previous route).
@app.route("/register", methods = ['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = RegistrationForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

        # user = User(username = form.username.data, first_name = form.first_name.data, last_name = form.last_name.data,
        #     email = form.email.data, password = hashed_password)

        flask.session['user'] = form.username.data
        flask.session['first_name'] = form.first_name.data
        flask.session['last_name'] = form.last_name.data
        flask.session['email'] = form.email.data
        flask.session['password'] = hashed_password

        username = form.username.data
        
        flash(f'Please set up your profile to create your account.', 'success')

        return redirect(url_for('profile_creation', username = username))

    return render_template('register.html', title = 'Register', form = form)


# Route for existing user login.
@app.route("/login", methods = ['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username = form.username.data).first()

        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember = form.remember.data)

            #next_page = request.args.get('next')

            flash("You have successfully logged in.", "success")

            #return redirect(next_page) if next_page else redirect(url_for('fitness_page'))
            return redirect(url_for('fitness_page'))

        else:
            flash('Login Unsuccessful. Please check your username and/or password.', 'danger')

    return render_template('login.html', title = 'Log In', form = form)


# Route for existing user logout.
@app.route("/logout")
def logout():
    logout_user()

    flash('You have successfully logged out.', 'success')

    return redirect(url_for('home'))

# Route for displaying the current user's account and profile.
@app.route("/account")
@login_required
def account():
    profile_image = url_for('static', filename = 'images/' + current_user.profile_image)

    return render_template('account.html', title = 'Your Account', image_file = profile_image)


"""Save the PICTURE filename to the User model, and copy the selected PICTURE to static/images. The user's profile picture will
   then be changed to display the selected PICTURE."""
def save_picture(picture):
    random_hex = secrets.token_hex(8)
    _, file_ext = os.path.splitext(picture.filename)

    picture_filename = random_hex + file_ext

    picture_path = os.path.join(app.root_path, 'static/images', picture_filename)

    output_size = (500, 500)
    i = Image.open(picture)
    i.thumbnail(output_size)

    i.save(picture_path)

    return picture_filename


# Route for updating the current user's profile picture.
@app.route("/account/update-profile-picture", methods = ['GET', 'POST'])
@login_required
def change_profile_image():
    form = ChangeProfilePicForm()

    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)

            current_user.profile_image = picture_file

        db.session.commit()

        flash(f'You have successfully changed your profile picture.', 'success')

        return redirect(url_for('account'))

    return render_template('update-profile-picture.html', title = 'Update Profile Picture', form = form)


# Route for updating the current user's email.
@app.route("/account/update-user-email", methods = ['GET', 'POST'])
@login_required
def change_user():
    form = ChangeUserForm()

    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data

        db.session.commit()

        flash(f'You have successfully updated your username and email', 'success')

        return redirect(url_for('account'))

    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email

    return render_template('update-user.html', title = 'Update Profile', form = form)


# Route for changing the current user's password.
@app.route("/account/change-password", methods = ['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        new_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

        current_user.password = new_pw

        db.session.commit()

        flash(f'You have successfully changed your password.', 'success')

        return redirect(url_for('account'))

    return render_template('change-password.html', title = 'Change Password', form = form)

@app.route('/course')
def course_video():
    return render_template('course.html')

@app.route("/post/new", methods=['GET','POST'])
@login_required
def new_post():
    form =PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)#create Post object
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post',
                            form=form, legend='New Post')

@app.route("/post/<int:post_id>") #flask let us put variable in the route using<>
def post(post_id):
    post = Post.query.get_or_404(post_id) #get the blog with this id or get 404 error
    return render_template('post.html', title=post.title, post=post) #past variables to post.html


@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post',
                           form=form, legend='Update Post',post=post)

@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('community'))

@app.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user)\
        .order_by(Post.date_posted.desc())\
        .paginate(page=page, per_page=5)
    return render_template('user_posts.html', posts=posts, user=user)

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request.', sender='marshallzyz@gmail.com',
                     recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}

If you did not make this request then  simply ignore this email and no change will be made.
    '''
    #_external=True means use absolute url
    mail.send(msg)


@app.route("/reset_password", methods=['GET','POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('You request to change your password.')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form = form)

@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token) 
    if user is None: #if not current user 
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)