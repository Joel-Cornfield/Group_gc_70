from flask import render_template, redirect, url_for, flash, request, jsonify 
from flask_login import login_user, logout_user, login_required, current_user
from app.forms import LoginForm, RegistrationForm
from app.models import User, Stats, GameHistory, LocationGuess
from app import db, app

"""
This file contains the route definitions for the Flask application. Almost all of these endpoints are skeletolns and are not fully implemented yet.
"""
# Most of these pages will require user info to be passed to them(username, info for dropdown), but for now they are just placeholders.

# Home Page
@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html', user=current_user)

# Game Page
@app.route('/game')
def game():
    return render_template('game.html', user=current_user)

# How to Play Page
@app.route('/howtoplay')
def how_to_play():
    return render_template('howtoplay.html', user=current_user)

# Profile Page (Example)
@app.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    user = User.query.get_or_404(user_id)
    stats = Stats.query.filter_by(user_id=user_id).first()
    return render_template('profile.html', user=current_user, stats=stats)

# Leaderboard/Statistics Page (Example, would need more info)
@app.route('/analyticpage')
@login_required 
def analytic_page():
    stats = Stats.query.order_by(Stats.total_wins.desc()).all()
    return render_template('analyticpage.html', user=current_user, stats=stats)

# API Endpoint: Get User Data (Example)
@app.route('/api/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name
    })

# API Endpoint: Submit Game Data (Example)
@app.route('/api/submit_game', methods=['POST'])
def submit_game():
    data = request.json
    game = GameHistory(
        user_id=data['user_id'],
        total_score=data['total_score'],
        locations_guessed=data['locations_guessed'],
        correct_guesses=data['correct_guesses']
    )
    db.session.add(game)
    db.session.commit()
    return jsonify({'message': 'Game data submitted successfully!'})

# Auth Page 
@app.route('/auth')
def auth():
    login_form = LoginForm()
    registration_form = RegistrationForm()
    return render_template('auth.html', user=current_user, login_form=login_form, signup_form=registration_form)

# Login Form Submission 
@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('home'))
        flash('Invalid username or password', 'danger')
    return render_template('auth.html', form=form, tab='login')

# Registration Form Submission 
@app.route('/auth/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))
    return render_template('auth.html', form=form, tab='signup')

# Logout (Example)
@app.route('/auth/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth'))


# Error Handlers (Example)
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

