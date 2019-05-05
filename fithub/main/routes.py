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

from flask import render_template, url_for, flash, redirect, request, abort,Blueprint, current_app
from fithub import db, bcrypt, mail
from fithub.main.forms import MacroForm, MealForm
from fithub.models import User, Profile, Schedule, Exercise, Macros, Meal, Post
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message

main = Blueprint('main',__name__)

# Route to the homepage.
@main.route("/")
@main.route("/home")
def home():
    page = request.args.get('page',1,type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(per_page=5)
    return render_template('home.html', posts=posts)


# Route to the main Fithub exercises database.
@main.route("/workouts/database")
@login_required
def exercise_db():
    today = datetime.today().strftime("%A")


    return render_template('exercise-db.html', title = "Exercise Database", today = today)


# Route to the Fithub exercises database for leg workouts, page 1.
@main.route("/workouts/database/legs1")
@login_required
def exercise_db_legs1():
    today = datetime.today().strftime("%A")

    return render_template('exercise-db-legs1.html', title = "Exercise Database: Legs", today = today)


# Route to the Fithub exercises database for leg workouts, page 2.
@main.route("/workouts/database/legs2")
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
@main.route("/nutrition", methods = ['GET', 'POST'])
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
@main.route("/nutrition/set-macros/today", methods = ['GET', 'POST'])
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

        return redirect(url_for('main.nutrition'))

    elif request.method == 'GET':
        form.day.data = day

    return render_template('set-macros.html', title = "Set Macros", form = form)


# Route to a WTForms instance for setting or editing any WEEKDAY's macros.
@main.route("/nutrition/set-macros/<weekday>", methods = ['GET', 'POST'])
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

        return redirect(url_for('main.view_macros'))

    elif request.method == 'GET':
        form.day.data = weekday

    return render_template('set-macros.html', title = "Set Macros", form = form)


# Route to a webpage that displays the macros for all 7 days of the week.
@main.route("/nutrition/view-macros")
@login_required
def view_macros():
    macros = Macros.query.filter(Macros.user_id == current_user.id).all()

    return render_template('view-macros.html', title = "View Macros", macros = macros)


# Route to a WTForms instance for adding a new meal, where the previous page was .
@main.route("/nutrition/new-meal", methods = ['GET', 'POST'])
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
        return redirect(url_for('main.nutrition'))

    return render_template('new-meal.html', title = "New Meal", form = form)


# Route to a WTForms instance for adding a new meal, where the previous page was .
@main.route("/nutrition/meal-log/new-meal", methods = ['GET', 'POST'])
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
        return redirect(url_for('main.meal_log'))

    return render_template('new-meal.html', title = "New Meal", form = form)


# Route to the user's meal log, a webpage that contains data about all meals eaten today (by datetime).
@main.route("/nutrition/meal-log")
@login_required
def meal_log():
    today = datetime.today()

    meals = Meal.query.filter(Meal.user_id == current_user.id).all()
    todays_meals = [x for x in meals if x.time.strftime('%d-%m-%Y') == today.strftime('%d-%m-%Y')]

    sorted_meals = sorted(todays_meals, key = operator.attrgetter('calories'))

    return render_template('meal-log.html', title = "Meal Log", meals = todays_meals, sorted_meals = sorted_meals,
        today = datetime.today())


# Route to a WTForms instance for editing the data for a meal with MEAL_ID.
@main.route("/nutrition/meal-log/<int:meal_id>/update-meal", methods = ['GET', 'POST'])
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

        return redirect(url_for('main.meal_log'))

    elif request.method == 'GET':
        form.description.data = meal.description
        form.food_type.data = meal.food_type
        form.time.data = meal.time
        form.protein.data = meal.protein
        form.carbs.data = meal.carbs
        form.fat.data = meal.fat

    return render_template('update-meal.html', title = "Edit Your Meal", form = form)


# Route for deleting all the data for a meal with MEAL_ID (and subsequently deleting the meal itself).
@main.route("/nutrition/meal-log/<int:meal_id>/delete-meal", methods = ['GET'])
@login_required
def delete_meal(meal_id):
    meal = Meal.query.filter(Meal.user_id == current_user.id, Meal.id == meal_id).first()

    if meal.user != current_user:
        abort(403)

    db.session.delete(meal)
    db.session.commit()

    flash("You have successfully deleted your meal.", "success")
    return redirect(url_for('main.meal_log'))


# Route to the Fithub nutritional resources page.
@main.route("/nutrition/nutrition-resources")
@login_required
def nutrition_resources():
    return render_template('nutr-res.html', title = "Nutrition Resources")


# Route to the Fithub nutritional resources page about macronutrients.
@main.route("/nutrition/nutrition-resources/macros101")
@login_required
def nutr_res_macros():
    return render_template('nutr-res-macros.html', title = "Macros 101")


### Routes and functions to do with the community page. ###


# Route to the user community page.
@main.route("/community")
def community():
    page = request.args.get('page',1,type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page,per_page=5)
    return render_template('community.html', title = 'Community',posts=posts)


@main.route('/course')
def course_video():
    return render_template('course.html')




