from datetime import datetime
import random
import json 
from flask import render_template, redirect, url_for, flash, request, jsonify , current_app, Response
from flask_login import login_user, logout_user, login_required, current_user
from app.forms import LoginForm, RegistrationForm, ProfilePictureForm, ChangePasswordForm, UpdateProfileForm
from app.models import User, Game, Stats, Location, Hint, Friend, Notification
from app import db
from app.game_logic import process_guess
from app.socket_events import send_notification_to_user
from app.blueprints import main 
from sqlalchemy import and_


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'} 

# Helper function to check file extensions
def allowed_file(filename): 
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'} 

# Helper function to check file extensions
def allowed_file(filename): 
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

"""
This file contains the route definitions for the Flask application. Almost all of these endpoints are skeletolns and are not fully implemented yet.
"""

# Home Page
@main.route('/')
@main.route('/home')
def home():
    return render_template('home.html', user=current_user)

# Game Page
@main.route('/game')
def game():
    return render_template('game.html', user=current_user)

@main.route('/play', methods=['GET'])
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
        'guess_image': url_for('main.location_image', location_id=location.id),
    })

@main.route('/guess', methods=['POST'])
def guess():
    data = request.json
    if current_user.is_authenticated:
        return jsonify(process_guess(data['game_id'], current_user.id, data))
    else:
        return jsonify(process_guess(data['game_id'], None, data))

@main.route('/hint/<int:game_id>', methods=['POST'])
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
    db.session.commit()
    return jsonify({'hint': hint,'score': game.total_score})


@main.route('/unblur/<int:game_id>', methods=['POST'])
def unblur(game_id):
    # Fetch the game
    game = Game.query.get(game_id)
    if not game:
        return jsonify({'error': 'Invalid game ID'}), 400
    
    game.total_score = max(0, game.total_score-20)  # Deduct score for unblur usage
    db.session.commit()
    return jsonify({'score': game.total_score})
    

# How to Play Page
@main.route('/howtoplay')
def how_to_play():
    return render_template('howtoplay.html', user=current_user)

# Profile Page (Example)
@main.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    user = User.query.get_or_404(user_id)
    stats = Stats.query.filter_by(user_id=user_id).first()

    profile_picture_form = ProfilePictureForm() 
    change_password_form = ChangePasswordForm() 
    update_profile_form = UpdateProfileForm()
    return render_template('profile.html', user=current_user, stats=stats, profile_picture_form=profile_picture_form, change_password_form=change_password_form, update_profile_form=update_profile_form)

# Update Profile Route
@main.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    form = UpdateProfileForm()
    if form.validate_on_submit():
        if form.username.data:
            current_user.username = form.username.data
        if form.first_name.data:
            current_user.first_name = form.first_name.data
        if form.last_name.data:
            current_user.last_name = form.last_name.data
        db.session.commit()
        flash("Profile updated successfully", "success")
    return redirect(url_for('main.profile', user_id=current_user.id))

# Change Password Route
@main.route('/change_password', methods=['POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect.', 'danger')
        else:
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Password updated successfully!', 'success')
    else:
        flash('Please fix the errors in the form.', 'danger')
    
    return redirect(url_for('main.profile', user_id=current_user.id))


@main.route('/upload_profile_picture', methods=['POST'])
@login_required
def upload_profile_picture():
    file = request.files.get('profile_picture')

    if not file or file.filename == '':
        flash('No file selected', 'danger')
        return redirect(url_for('main.profile', user_id=current_user.id))

    if not allowed_file(file.filename):
        flash('Invalid file type. Please upload an image file.', 'danger')
        return redirect(url_for('main.profile', user_id=current_user.id))

    # Save the file's binary data and mimetype to the database
    current_user.profile_picture_data = file.read()
    current_user.profile_picture_mimetype = file.mimetype
    db.session.commit()

    flash('Profile picture updated!', 'success')
    return redirect(url_for('main.profile', user_id=current_user.id))

@main.route('/profile_picture/<int:user_id>')
def profile_picture(user_id):
    user = User.query.get_or_404(user_id)
    if not user.profile_picture_data:
        # Return a default profile picture if none is set
        return redirect(url_for('static', filename='images/defaultprofile.png'))
    return Response(user.profile_picture_data, mimetype=user.profile_picture_mimetype)


# Leaderboard/Statistics Page (Example, would need more info)
@main.route('/analyticpage/<int:user_id>')
@login_required
def analytic_page(user_id):
    user = User.query.get_or_404(user_id)
    stats = Stats.query.filter_by(user_id=user_id).first()
    if not stats:
            stats = Stats(user_id=user_id, total_games=0, total_wins=0, win_streak=0, time_spent=0, start_date=db.func.now())
            db.session.add(stats)
    db.session.commit()

    # Check if the current user is the owner or a friend
    is_friend = Friend.query.filter(
        ((Friend.user_id == current_user.id) & (Friend.friend_id == user_id) & (Friend.status == "accepted")) |
        ((Friend.user_id == user_id) & (Friend.friend_id == current_user.id) & (Friend.status == "accepted"))
    ).first()

    if user_id != current_user.id and not is_friend:
        flash("You are not authorized to view this analytics page.", "danger")
        return redirect(url_for('main.home'))

    # Leaderboards
    win_streak_leaderboard = Stats.query.join(User).with_entities(
        User.username.label("player"),
        Stats.win_streak.label("value")
    ).order_by(Stats.win_streak.desc()).limit(10).all()

    total_wins_leaderboard = Stats.query.join(User).with_entities(
        User.username.label("player"),
        Stats.total_wins.label("value")
    ).order_by(Stats.total_wins.desc()).limit(10).all()

    win_percentage_leaderboard = Stats.query.join(User).with_entities(
        User.username.label("player"),
        Stats.win_percentage.label("value")
    ).order_by(Stats.win_percentage.desc()).limit(10).all()

    # Helper to get user's rank in a leaderboard
    def get_rank(leaderboard, username):
        for index, entry in enumerate(leaderboard):
            if entry.player == username:
                return f"#{index + 1}"
        return "N/A"

    stats_data = {
        "total_games": stats.total_games,
        "time_spent": f"{stats.time_spent // 60} mins" if stats.time_spent else "0 mins",
        "win_streak": stats.win_streak,
        "win_streak_rank": get_rank(win_streak_leaderboard, user.username),
        "total_wins": stats.total_wins,
        "total_wins_rank": get_rank(total_wins_leaderboard, user.username),
        "win_percentage": f"{stats.win_percentage:.2f}%" if stats.win_percentage is not None else "N/A",
        "win_percentage_rank": get_rank(win_percentage_leaderboard, user.username),
        "start_date": stats.start_date.strftime('%B %d, %Y') if stats.start_date else "Unknown"
    }

    # Fetch finished games
    games = Game.query.filter(
        and_(
            Game.user_id == user_id,
            Game.start_time.isnot(None),
            Game.finish_time.isnot(None)
        )
    ).order_by(Game.start_time.asc()).all()

    # Prepare data for graph 
    game_data = []
    for game in games:
        duration = (game.finish_time - game.start_time).total_seconds()
        is_correct = game.total_score > 0 
        game_data.append({
            'game_id': game.id,
            'duration': round(duration, 2),
            'correct': is_correct 
        })

    return render_template(
        'analyticpage.html',
        user=user,
        win_streak_leaderboard=win_streak_leaderboard,
        total_wins_leaderboard=total_wins_leaderboard,
        win_percentage_leaderboard=win_percentage_leaderboard,
        stats=stats_data,
        game_data=game_data
    )


# API Endpoint: Get User Data (Example)
@main.route('/api/user/<int:user_id>', methods=['GET'])
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
@main.route('/api/submit_game', methods=['POST'])
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

    user_stats = Stats.query.filter_by(user_id=data['user_id']).first()
    if user_stats:
        user_stats.total_games += 1
        if data['correct_guesses'] == len(data['locations_guessed']):
            user_stats.total_wins += 1
            user_stats.win_streak += 1
        else:
            user_stats.win_streak = 0  # Reset win streak on loss

        # Calculate win percentage
        user_stats.win_percentage = round((user_stats.total_wins / user_stats.total_games) * 100, 2)


        db.session.commit()

    return jsonify({'message': 'Game data submitted successfully!'})

# Auth Page 
@main.route('/auth')
def auth():
    login_form = LoginForm()
    registration_form = RegistrationForm()
    return render_template('auth.html', user=current_user, login_form=login_form, signup_form=registration_form, tab='login')

# Login Form Submission 
@main.route('/auth/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    login_form = LoginForm()
    signup_form = RegistrationForm()
    if login_form.validate_on_submit():
        user = User.query.filter_by(username=login_form.username.data).first()
        if user and user.check_password(login_form.password.data):
            login_user(user)
            return redirect(url_for('main.home')) 
    return render_template('auth.html', user=current_user, login_form=login_form, signup_form=signup_form, tab='login')

# Registration Form Submission 
@main.route('/auth/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    signup_form = RegistrationForm()
    if signup_form.validate_on_submit():
        # Check if email or username already exists
        existing_user = User.query.filter(
            (User.email == signup_form.email.data) | (User.username == signup_form.username.data)
        ).first()
        if existing_user:
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
            # Add user to the database
            db.session.add(user)
            db.session.commit()  # Commit user to generate user.id

            # Create a stats entry for this user
            stats = Stats(
                user_id=user.id,
                total_games=0,
                total_wins=0,
                win_streak=0,
                time_spent=0,
                win_percentage=0.0,
                start_date=datetime.utcnow()
            )
            db.session.add(stats)
            db.session.commit()  # Commit stats to the database

            flash("Account created successfully!", "success")
            return redirect(url_for('main.login'))
        except Exception as e:
            db.session.rollback()
            print(f"Error: {e}")
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
@main.route('/auth/logout')
@login_required
def logout():
    # Delete all read notifications for current user before logout
    try:
        Notification.query.filter_by(user_id=current_user.id, is_read=True).delete()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while clearing notifications on logout. Please try again.', 'danger')
    logout_user()
    flash('You have been logged out', 'success')
    return redirect(url_for('main.auth'))

# Fetch the current user's friends
@main.route('/api/friends', methods=['GET'])
@login_required
def get_friends():
    # Fetch all friends where the current user is either the sender or the recipient
    friends = Friend.query.filter(
        ((Friend.user_id == current_user.id) | (Friend.friend_id == current_user.id)) &
        (Friend.status == "accepted")
    ).all()

    # Use a dictionary to store friend details (to avoid duplicates)
    friends_dict = {}

    for friend in friends:
        # Determine the friend's ID (exclude the current user)
        friend_id = friend.friend_id if friend.user_id == current_user.id else friend.user_id

        # Avoid duplicates by using a dictionary
        if friend_id not in friends_dict:
            friend_user = User.query.get(friend_id)
            friends_dict[friend_id] = {
                'id': friend_user.id,
                'name': friend_user.username,
                'profile_picture': url_for('main.profile_picture', user_id=friend_user.id)
            }

    # Convert the dictionary values to a list
    friends_list = list(friends_dict.values())

    return jsonify(friends_list)

# Add a new friend
@main.route('/api/friends/add', methods=['POST'])
@login_required
def add_friend():
    data = request.json
    friend_username = data.get('username')

    # Check if the user exists
    friend = User.query.filter_by(username=friend_username).first()
    if not friend:
        return jsonify({'error': 'User not found'}), 404
        
    # Check if trying to add self
    if friend.id == current_user.id:
        return jsonify({'error': 'You cannot add yourself as a friend'}), 400

    # Check if the friend relationship already exists
    existing_friend = Friend.query.filter(
        (Friend.user_id == current_user.id) & (Friend.friend_id == friend.id)
    ).first()
    if existing_friend:
        return jsonify({'error': 'Friend request already sent or relationship exists'}), 400

    # Check if there's already a pending request from this user
    incoming_request = Friend.query.filter(
        (Friend.user_id == friend.id) & (Friend.friend_id == current_user.id) & (Friend.status == "pending")
    ).first()
    
    if incoming_request:
        # Accept the existing request instead of creating a new one
        incoming_request.status = "accepted"
        # Create reciprocal relationship
        new_friend = Friend(user_id=current_user.id, friend_id=friend.id, status="accepted")
        db.session.add(new_friend)
        db.session.commit()
        
        # Send WebSocket notification to both users
        send_notification_to_user(current_user.id, 'friend_accepted', {
            'friend_id': friend.id,
            'friend_name': friend.username,
            'profile_picture': url_for('static', filename='images/default_profile.png')
        })
        
        send_notification_to_user(friend.id, 'friend_accepted', {
            'friend_id': current_user.id,
            'friend_name': current_user.username,
            'profile_picture': url_for('static', filename='images/default_profile.png')
        })
        
        return jsonify({'message': f'You are now friends with {friend_username}!'})
    
    # Create a new friend request with status "pending"
    new_friend_request = Friend(user_id=current_user.id, friend_id=friend.id, status="pending")
    db.session.add(new_friend_request)
    db.session.commit()
    
    # Send WebSocket notification to the recipient
    send_notification_to_user(friend.id, 'friend_request', {
        'request_id': new_friend_request.id,
        'sender_id': current_user.id,
        'sender_name': current_user.username,
        'profile_picture': url_for('static', filename='images/default_profile.png')
    })

    return jsonify({'message': f'Friend request sent to {friend_username}!'})

# Fetch pending friend requests
@main.route('/api/friends/requests', methods=['GET'])
@login_required
def get_friend_requests():
    requests = Friend.query.filter_by(friend_id=current_user.id, status="pending").all()
    requests_list = [
        {
            'id': request.id,
            'user_id': request.user_id,
            'name': User.query.get(request.user_id).username,
            'profile_picture':  url_for('main.profile_picture', user_id=request.user_id)
        }
        for request in requests
    ]
    return jsonify(requests_list)

# Accept a friend request 
@main.route('/api/friends/accept', methods=['POST'])
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
    sender_id = friend_request.user_id
    reciprocal_friend = Friend(user_id=current_user.id, friend_id=sender_id, status="accepted")
    db.session.add(reciprocal_friend)
    db.session.commit()
    
    # Get sender user object for notification
    sender = User.query.get(sender_id)
    
    # Send WebSocket notifications to both users
    send_notification_to_user(current_user.id, 'friend_accepted', {
        'friend_id': sender_id,
        'friend_name': sender.username,
        'profile_picture': url_for('static', filename='images/default_profile.png')
    })
    
    send_notification_to_user(sender_id, 'friend_accepted', {
        'friend_id': current_user.id,
        'friend_name': current_user.username,
        'profile_picture': url_for('static', filename='images/default_profile.png')
    })

    return jsonify({
        'message': 'Friend request accepted!',
        'friend': {
            'id': sender_id,
            'name': sender.username,
            'profile_picture': url_for('static', filename='images/default_profile.png')
        }
    })

# Rejecting friend requests
@main.route('/api/friends/reject', methods=['POST'])
@login_required
def reject_friend_request():
    data = request.json
    request_id = data.get('request_id')

    # Find the friend request
    friend_request = Friend.query.filter_by(id=request_id, friend_id=current_user.id, status="pending").first()
    if not friend_request:
        return jsonify({'error': 'Friend request not found'}), 404
        
    # Store the sender ID before deleting
    sender_id = friend_request.user_id

    # Delete the request
    db.session.delete(friend_request)
    db.session.commit()
    
    # Send WebSocket notification to the sender that their request was rejected
    send_notification_to_user(sender_id, 'friend_rejected', {
        'user_id': current_user.id,
        'username': current_user.username
    })

    return jsonify({'message': 'Friend request rejected!'})

# Removing friends
@main.route('/api/friends/remove', methods=['POST'])
@login_required
def remove_friend():
    data = request.json
    friend_id = data.get('friend_id')

    if not friend_id:
        return jsonify({'error': 'Friend ID is required'}), 400

    # Find both friendship records (bidirectional)
    friendship1 = Friend.query.filter_by(user_id=current_user.id, friend_id=friend_id, status="accepted").first()
    friendship2 = Friend.query.filter_by(user_id=friend_id, friend_id=current_user.id, status="accepted").first()

    if not friendship1 and not friendship2:
        return jsonify({'error': 'Friendship not found'}), 404

    # Remove both friendship records
    if friendship1:
        db.session.delete(friendship1)
    if friendship2:
        db.session.delete(friendship2)
    db.session.commit()
    
    # Send WebSocket notification to the removed friend
    send_notification_to_user(friend_id, 'friend_removed', {
        'user_id': current_user.id,
        'username': current_user.username
    })

    return jsonify({'message': 'Friend removed successfully!'})

# Fetch user's notifications
@main.route('/api/notifications', methods=['GET'])
@login_required
def get_notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(50).all()
    
    result = []
    for notification in notifications:
        # Get sender info if available
        sender_info = None
        if notification.sender_id:
            sender = User.query.get(notification.sender_id)
            if sender:
                sender_info = {
                    'id': sender.id,
                    'username': sender.username,
                    'profile_picture':  url_for('main.profile_picture', user_id=sender.id)
                }
        
        # Format the notification
        result.append({
            'id': notification.id,
            'type': notification.type,
            'message': notification.message,
            'data': json.loads(notification.data) if notification.data else {},
            'sender': sender_info,
            'is_read': notification.is_read,
            'created_at': notification.created_at.isoformat()
        })
    
    return jsonify(result)

# Mark notification as read
@main.route('/api/notifications/mark-read', methods=['POST'])
@login_required
def mark_notification_read():
    data = request.json
    notification_id = data.get('notification_id')
    
    if notification_id:
        # Mark specific notification as read
        notification = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first()
        if notification:
            notification.is_read = True
            db.session.commit()
            return jsonify({'success': True, 'message': 'Notification marked as read'})
        else:
            return jsonify({'success': False, 'error': 'Notification not found'}), 404
    else:
        return jsonify({'success': False, 'error': 'Invalid request parameters'}), 400
    
@main.route('/api/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
    for n in notifications:
        n.is_read = True
    db.session.commit()
    return jsonify({'success': True, 'message': 'All notifications marked as read'})

@main.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_page():
    if not current_user.admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('main.home'))

    locations = Location.query.all()
    serialized_locations = [
        {
            'id': location.id,
            'name': location.name,
            'latitude': location.latitude,
            'longitude': location.longitude,
            'department': location.department,
            'hints': [{'id': hint.id, 'text': hint.text} for hint in location.hints]
        }
        for location in locations
    ]

    if request.method == 'POST':
        # Check if updating an existing location
        location_id = request.form.get('location_id')
        location = Location.query.get(location_id) if location_id else None

        # Get form data
        location_name = request.form.get('location_name')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        department = request.form.get('department')
        hints = request.form.getlist('hints')
        image = request.files.get('image')

        if not location_name or not latitude or not longitude:
            flash('Name, latitude, and longitude are required.', 'danger')
            return redirect(url_for('main.admin_page'))

        if location:  # Update existing location
            location.name = location_name
            location.latitude = float(latitude)
            location.longitude = float(longitude)
            location.department = department

            # Update image if a new one is uploaded
            if image:
                location.image_data = image.read()
                location.image_mimetype = image.mimetype

            # Update hints
            location.hints.clear()  # Remove existing hints
            for hint_text in hints:
                if hint_text.strip():
                    hint = Hint(location=location, text=hint_text.strip())
                    db.session.add(hint)

            flash('Location updated successfully!', 'success')
        else:  # Create a new location
            # Read the image data
            image_data = image.read() if image else None
            image_mimetype = image.mimetype if image else None

            # Create a new location
            location = Location(
                name=location_name,
                latitude=float(latitude),
                longitude=float(longitude),
                department=department,
                image_data=image_data,
                image_mimetype=image_mimetype
            )
            db.session.add(location)

            # Add hints
            for hint_text in hints:
                if hint_text.strip():
                    hint = Hint(location=location, text=hint_text.strip())
                    db.session.add(hint)

            flash('Location added successfully!', 'success')

        db.session.commit()
        return redirect(url_for('main.admin_page'))

    return render_template('admin.html', user=current_user, locations=serialized_locations)


@main.route('/location_image/<int:location_id>')
def location_image(location_id):
    location = Location.query.get(location_id)
    if not location or not location.image_data:
        return jsonify({'error': 'Image not found'}), 404
    return current_app.response_class(location.image_data, mimetype=location.image_mimetype)

# Error Handlers (can be blueprint-scoped or app-wide)
@main.app_errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@main.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
