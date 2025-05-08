import random
from flask import render_template, redirect, url_for, flash, request, jsonify 
from flask_login import login_user, logout_user, login_required, current_user
from app.forms import LoginForm, RegistrationForm
from app.models import User, Game, Stats, Location, Hint
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
        location_name=location.name,
        total_score=100
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

@app.route('/hint/<int:game_id>', methods=['POST'])
def get_hint(game_id):
    # Fetch the game
    game = Game.query.get(game_id)
    if not game:
        return jsonify({'error': 'Invalid game ID'}), 400

    # Fetch the location associated with the game
    location = Location.query.filter_by(name=game.location_name).first()
    if not location:
        return jsonify({'error': 'Location not found'}), 404

    # Get the list of already-received hint IDs from the client
    data = request.json
    received_hint_ids = data.get('received_hint_ids', [])
    
    # Fetch hints for the current location
    hints = Hint.query.filter(Hint.location_id == location.id, ~Hint.id.in_(received_hint_ids)).all()
    if not hints:
        return jsonify({'error': 'No hints available for this location'}), 404

    # Select a random hint
    hint = random.choice(hints).text
    game.total_score = max(0, game.total_score-10)  # Deduct score for hint usage
    return jsonify({'hint': hint,'score': game.total_score})

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
    game = Game(
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


# Error Handlers (Example)
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

