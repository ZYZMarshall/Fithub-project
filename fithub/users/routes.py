from flask import render_template, url_for, flash, redirect, request, Blueprint
from flask_login import login_user, current_user, logout_user, login_required
from fithub import db, bcrypt
from fithub.models import User, Post, Schedule,Exercise,Profile,Macros, Meal
from fithub.users.forms import (RegistrationForm, LoginForm, AddExerciseForm,
                                   RequestResetForm, ResetPasswordForm,ProfileForm, ChangeProfilePicForm, 
                                   ChangeUserForm, ChangePasswordForm)
from fithub.main.forms import MealForm, WorkoutForm
from fithub.users.utils import save_picture, send_reset_email,set_blank_macros,set_blank_schedule
from datetime import datetime
import flask

users = Blueprint('users',__name__)


# Route for registering a new user. The data from this page gets saved to the current Flask session, and the new user is created
# only if the user successfully completes PROFILE_CREATION (previous route).
@users.route("/register", methods = ['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

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

        return redirect(url_for('users.profile_creation', username = username))

    return render_template('register.html', title = 'Register', form = form)


# Route for existing user login.
@users.route("/login", methods = ['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username = form.username.data).first()

        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember = form.remember.data)

            #next_page = request.args.get('next')

            flash("You have successfully logged in.", "success")

            #return redirect(next_page) if next_page else redirect(url_for('fitness_page'))
            return redirect(url_for('users.fitness_page'))

        else:
            flash('Login Unsuccessful. Please check your username and/or password.', 'danger')

    return render_template('login.html', title = 'Log In', form = form)


# Route for existing user logout.
@users.route("/logout")
def logout():
    logout_user()

    flash('You have successfully logged out.', 'success')

    return redirect(url_for('main.home'))


# Route for displaying the current user's account and profile.
@users.route("/account")
@login_required
def account():
    profile_image = url_for('static', filename = 'images/' + current_user.profile_image)

    return render_template('account.html', title = 'Your Account', image_file = profile_image)

@users.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user)\
        .order_by(Post.date_posted.desc())\
        .paginate(page=page, per_page=5)
    return render_template('user_posts.html', posts=posts, user=user)


@users.route("/reset_password", methods=['GET','POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('users.home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('users.login'))
    return render_template('reset_request.html', title='Reset Password', form = form)

@users.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('users.home'))
    user = User.verify_reset_token(token) 
    if user is None: #if not current user 
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('users.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('users.login'))
    return render_template('reset_token.html', title='Reset Password', form=form)

### Routes and functions to do with the fitness page. ###

# Route to the user's main fitness page.
@users.route("/my-fitness-page", methods = ['GET', 'POST'])
def fitness_page():
    return render_template('fitness-page.html', title = 'My Fitness Page')

@users.route("/course", methods=['GET','POST'])
def course():
    return render_template('course.html', title = 'Fitness Course')

### Routes and functions to do with the workouts page. ###

# Route to the user's main workouts page.
@users.route("/workouts")
def workouts():

    if current_user.is_authenticated:
        day = datetime.strftime(datetime.now(), "%A")
        workout = Schedule.query.filter(Schedule.user_id == current_user.id, Schedule.day_of_week == day).first().workout
        exercises = Exercise.query.filter(Exercise.user_id == current_user.id, Exercise.day == day).all()

        return render_template('workouts.html', title = 'Workouts', today = day, workout = workout, exercises = exercises)

    else:
        return redirect(url_for('users.home'))


# Route to the user's workouts page for selected DAY of week.
@users.route("/workouts/<day>")
@login_required
def workouts_day(day):
    workout = Schedule.query.filter(Schedule.user_id == current_user.id, Schedule.day_of_week == day).first().workout
    exercises = Exercise.query.filter(Exercise.user_id == current_user.id, Exercise.day == day).all()

    return render_template("workouts-day.html", title = "Daily Workout", day = day, workout = workout, exercises = exercises)


# Route to a WTForms instance to edit a workout for TODAY (by datetime).
@users.route("/workouts/<today>/update-workout1", methods = ['GET', 'POST'])
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

        return redirect(url_for('users.workouts'))    

    elif request.method == 'GET':
        form.day.data = today

    return render_template('change-workout.html', title = "Change Workout", form = form)


# Route to a WTForms instance to edit a workout for a selected DAY.
@users.route("/workouts/<day>/update-workout2", methods = ['GET', 'POST'])
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

        return redirect(url_for('users.workouts_day', day = day))    

    elif request.method == 'GET':
        form.day.data = day

    return render_template('change-workout.html', title = "Change Workout", form = form)


# Route to view the workouts schedule for the entire week. Not unique to different weeks.
@users.route("/workouts/view-schedule")
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
@users.route("/workouts/<today>/add-exercise1", methods = ['GET', 'POST'])
@login_required
def add_exercise1(today):
    form = AddExerciseForm()

    if form.validate_on_submit():
        user_id = current_user.id
        day = form.day.data
        workout = Schedule.query.filter(Schedule.user_id == user_id, Schedule.day_of_week == day).first().workout

        if workout == "None Set.":
            flash("Please set a workout for that day first.", "danger")
            return redirect(url_for('users.workouts'))

        if form.difficulty.data == None:
            difficulty = "None Given"

        else:
            difficulty = form.difficulty.data

        exercise = Exercise(name = form.name.data, day = form.day.data, workout = workout, num_sets = form.num_sets.data,
            num_reps = form.num_reps.data, difficulty = difficulty, user_id = user_id)

        db.session.add(exercise)
        db.session.commit()

        return redirect(url_for('users.workouts'))

    elif request.method == 'GET':
        form.day.data = today

    return render_template('new-exercise.html', title = "Add Exercise", form = form)


# Route to a WTForms instance to add an exercise to the selected DAY's workout.
@users.route("/workouts/<day>/add-exercise2", methods = ['GET', 'POST'])
@login_required
def add_exercise2(day):

    form = AddExerciseForm()

    if form.validate_on_submit():
        user_id = current_user.id
        day = form.day.data
        workout = Schedule.query.filter(Schedule.user_id == user_id, Schedule.day_of_week == day).first().workout

        if workout == "None Set.":
            flash("Please set a workout for that day first.", "danger")
            return redirect(url_for('users.workouts'))

        if form.difficulty.data == None:
            difficulty = "None Given"

        else:
            difficulty = form.difficulty.data

        exercise = Exercise(name = form.name.data, day = form.day.data, workout = workout, num_sets = form.num_sets.data,
            num_reps = form.num_reps.data, difficulty = difficulty, user_id = user_id)

        db.session.add(exercise)
        db.session.commit()

        return redirect(url_for('users.workouts_day', day = day))

    elif request.method == 'GET':
        form.day.data = day

    return render_template('new-exercise.html', title = "Add Exercise", form = form)


# Route to a WTForms instance to add an exercise to any day of the week.
@users.route("/workouts/<exercise_name>/<difficulty>/add-exercise3")
@login_required
def add_exercise3(exercise_name, difficulty):

    form = AddExerciseForm()

    if form.validate_on_submit():
        user_id = current_user.id
        day = form.day.data
        workout = Schedule.query.filter(Schedule.user_id == user_id, Schedule.day_of_week == day).first().workout

        if workout == "None Set.":
            flash("Please set a workout for that day first.", "danger")
            return redirect(url_for('users.workouts'))

        if form.difficulty.data == None:
            difficulty = "None Given"

        else:
            difficulty = form.difficulty.data

        exercise = Exercise(name = form.name.data, day = form.day.data, workout = workout, num_sets = form.num_sets.data,
            num_reps = form.num_reps.data, difficulty = difficulty, user_id = user_id)

        db.session.add(exercise)
        db.session.commit()

        return redirect(url_for('users.workouts_day', day = day))

    elif request.method == 'GET':
        form.day.data = "Monday"
        form.name.data = exercise_name
        form.difficulty.data = difficulty

    return render_template('new-exercise.html', title = "Add Exercise", form = form)


# Route to a WTForms instance to edit a selected exercise in a selected DAY's workout, where the previous page was .
@users.route("/workouts/<day>/<exercise_id>/edit-exercise1", methods = ['GET', 'POST'])
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

        return redirect(url_for('users.workouts'))

    elif request.method == 'GET':
        form.name.data = exercise.name
        form.day.data = day
        form.num_sets.data = exercise.num_sets
        form.num_reps.data = exercise.num_reps
        form.difficulty.data = exercise.difficulty

    return render_template('new-exercise.html', title = "Add Exercise", form = form)


# Route to a WTForms instance to edit a selected exercise in a selected DAY's workout, where the previous page was .
@users.route("/workouts/<day>/<exercise_id>/edit-exercise2", methods = ['GET', 'POST'])
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

        return redirect(url_for('users.workouts_day', day = day))

    elif request.method == 'GET':
        form.name.data = exercise.name
        form.day.data = day
        form.num_sets.data = exercise.num_sets
        form.num_reps.data = exercise.num_reps
        form.difficulty.data = exercise.difficulty

    return render_template('new-exercise.html', title = "Add Exercise", form = form)

# Route for a new user profile creation. This route finalizes new user registration from REGISTER (next route).
@users.route("/profile-creation/<username>", methods = ['GET', 'POST'])
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

        return redirect(url_for('users.fitness_page'))

    return render_template('profile-creation.html', title = "Create Your Profile", form = form)





# Route for updating the current user's profile picture.
@users.route("/account/update-profile-picture", methods = ['GET', 'POST'])
@login_required
def change_profile_image():
    form = ChangeProfilePicForm()

    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)

            current_user.profile_image = picture_file

        db.session.commit()

        flash(f'You have successfully changed your profile picture.', 'success')

        return redirect(url_for('users.account'))

    return render_template('update-profile-picture.html', title = 'Update Profile Picture', form = form)


# Route for updating the current user's email.
@users.route("/account/update-user-email", methods = ['GET', 'POST'])
@login_required
def change_user():
    form = ChangeUserForm()

    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data

        db.session.commit()

        flash(f'You have successfully updated your username and email', 'success')

        return redirect(url_for('users.account'))

    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email

    return render_template('update-user.html', title = 'Update Profile', form = form)


# Route for changing the current user's password.
@users.route("/account/change-password", methods = ['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        new_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

        current_user.password = new_pw

        db.session.commit()

        flash(f'You have successfully changed your password.', 'success')

        return redirect(url_for('users.account'))

    return render_template('change-password.html', title = 'Change Password', form = form)
  
@login_required
@users.route("/physicaltest")
def physical_test():
    return render_template('physical-test.html')
