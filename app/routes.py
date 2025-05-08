import os
import json
from flask import render_template, redirect, url_for, flash, request, jsonify 
from flask_login import login_user, logout_user, login_required, current_user
from app.forms import LoginForm, RegistrationForm
from app.models import User, Game, Stats, Location, Hint, Friend
from app import db, app
from app.game_logic import process_guess

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

@app.route('/play', methods=['GET'])
def play():
    # Load locations from the JSON file
    location = Location.query.order_by(db.func.random()).first()

    # Create a new game entry
    game = Game(
        actual_latitude=location.latitude,
        actual_longitude=location.longitude,
        location_name=location.name
    )
    if current_user.is_authenticated:
        game.user_id = current_user.id

    db.session.add(game)
    db.session.commit()

    # Return game data as JSON
    return jsonify({
        'game_id': game.id,
        'guess_image': url_for('static', filename=f'images/{location.name.replace(" ", "_")}.jpg'),
    })

@app.route('/guess', methods=['POST'])
def guess():
    data = request.json
    if current_user.is_authenticated:
        return jsonify(process_guess(data['game_id'], current_user.id, data))
    else:
        return jsonify(process_guess(data['game_id'], None, data))

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
    return render_template('auth.html', user=current_user, login_form=login_form, signup_form=registration_form, tab='login')

# Login Form Submission 
@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    login_form = LoginForm()
    signup_form = RegistrationForm()
    if login_form.validate_on_submit():
        user = User.query.filter_by(username=login_form.username.data).first()
        if user and user.check_password(login_form.password.data):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('home'))
        flash('Invalid username or password', 'danger')  
    return render_template('auth.html', user=current_user, login_form=login_form, signup_form=signup_form, tab='login')

# Registration Form Submission 
@app.route('/auth/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    signup_form = RegistrationForm()
    if signup_form.validate_on_submit():
        # Check if email or username already exists
        existing_user = User.query.filter(
            (User.email == signup_form.email.data) | (User.username == signup_form.username.data)
        ).first()
        if existing_user:
            flash('Email or username already exists. Please choose a different one.', 'danger')
            return render_template(
                'auth.html',
                user=current_user,
                signup_form=signup_form,
                login_form=LoginForm(),
                tab='signup'  # Stay on the signup tab
            )

        # Create a new user
        user = User(
            username=signup_form.username.data,
            email=signup_form.email.data,
            first_name=signup_form.first_name.data,
            last_name=signup_form.last_name.data
        )
        user.set_password(signup_form.password.data)
        try:
            db.session.add(user)
            db.session.commit()
            flash('Account created successfully!', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating your account. Please try again.', 'danger')
            return render_template(
                'auth.html',
                user=current_user,
                signup_form=signup_form,
                login_form=LoginForm(),
                tab='signup' 
            )
    return render_template(
        'auth.html',
        user=current_user,
        signup_form=signup_form,
        login_form=LoginForm(),
        tab='signup'  # Stay on the signup tab
    )

# Logout 
@app.route('/auth/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth'))

# Fetch the current user's friends
@app.route('/api/friends', methods=['GET'])
@login_required
def get_friends():
    friends = Friend.query.filter(
        ((Friend.user_id == current_user.id) | (Friend.friend_id == current_user.id)) &
        (Friend.status == "accepted")
    ).all()
    friends_list = [
        {
            'id': friend.friend_id if friend.user_id == current_user.id else friend.user_id,
            'name': User.query.get(friend.friend_id).username,
            'profile_picture': url_for('static', filename='images/default_profile.png') # Placeholder 
        }
        for friend in friends
    ]
    return jsonify(friends_list)

# Add a new friend
@app.route('/api/friends/add', methods=['POST'])
@login_required
def add_friend():
    data = request.json
    friend_username = data.get('username')

    # Check if the user exists
    friend = User.query.filter_by(username=friend_username).first()
    if not friend:
        return jsonify({'error': 'User not found'}), 404

    # Check if the friend relationship already exists
    existing_friend = Friend.query.filter_by(user_id=current_user.id, friend_id=friend.id).first()
    if existing_friend:
        return jsonify({'error': 'Friend already added'}), 400

    # Create a new friend request with status "pending"
    new_friend_request = Friend(user_id=current_user.id, friend_id=friend.id, status="pending")
    db.session.add(new_friend_request)
    db.session.commit()

    return jsonify({'message': f'Friend request sent to {friend_username} !'})

# Fetch pending friend requests
@app.route('/api/friends/requests', methods=['GET'])
@login_required
def get_friend_requests():
    requests = Friend.query.filter_by(friend_id=current_user.id, status="pending").all()
    requests_list = [
        {
            'id': request.id,
            'name': User.query.get(request.user_id).username,
            'profile_picture': url_for('static', filename='images/default_profile.png')  # Placeholder
        }
        for request in requests
    ]
    return jsonify(requests_list)

# Accept a friend request 
@app.route('/api/friends/accept', methods=['POST'])
@login_required
def accept_friend_request():
    data = request.json
    request_id = data.get('request_id')

    # Find the friend request
    friend_request = Friend.query.filter_by(id=request_id, friend_id=current_user.id, status="pending").first()
    if not friend_request:
        return jsonify({'error': 'Friend request not found'}), 404

    # Update the status to accepted
    friend_request.status = "accepted"

    # Create reciprocal friend relationship 
    reciprocal_friend = Friend(user_id=current_user.id, friend_id=friend_request.user_id, status="accepted")
    db.session.add(reciprocal_friend)

    db.session.commit()

    return jsonify({'message': 'Friend request accepted!'})


# Error Handlers (Example)
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

