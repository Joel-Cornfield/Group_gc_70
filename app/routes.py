from flask import render_template, request, redirect, url_for, jsonify
from app import app, db
from app.models import User, GameHistory, Stats

"""
This file contains the route definitions for the Flask application. Almost all of these endpoints are skeletolns and are not fully implemented yet.
"""
# Most of these pages will require user info to be passed to them(username, info for dropdown), but for now they are just placeholders.

# Home Page
@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')

# Game Page
@app.route('/game')
def game():
    return render_template('game.html')

# How to Play Page
@app.route('/howtoplay')
def how_to_play():
    return render_template('howtoplay.html')

# Profile Page (Example)
@app.route('/profile/<int:user_id>')
def profile(user_id):
    user = User.query.get_or_404(user_id)
    stats = Stats.query.filter_by(user_id=user_id).first()
    return render_template('profile.html', user=user, stats=stats)

# Leaderboard/Statistics Page (Example, would need more info)
@app.route('/analyticpage')
def analytic_page():
    stats = Stats.query.order_by(Stats.total_wins.desc()).all()
    return render_template('analyticpage.html', stats=stats)

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

# Login Page (Example)
@app.route('/auth')
def login():
    return render_template('auth.html')

# Login Form Submission (Example)
@app.route('/auth/login', methods=['POST'])
def login_user():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        # Logic to log in the user (e.g., session management)
        return redirect(url_for('home'))
    return render_template('auth.html', error='Invalid credentials')

# Error Handlers (Example)
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

