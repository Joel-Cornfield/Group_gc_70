from app import socketio, db
from flask import request
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room
from app.models import User, Friend, Notification
import json 

# Store connected users' socket IDs
connected_users = {}

@socketio.on('connect')
def handle_connect(auth):
    if current_user.is_authenticated:
        # Store the user's socket ID to allow sending targeted notifications
        connected_users[current_user.id] = request.sid
        # Join a personal room based on user_id
        join_room(f'user_{current_user.id}')
        print(f"User  {current_user.username} connected with SID: {request.sid}")
        # Fetch unread notifications from the database
        notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).order_by(Notification.created_at.desc()).all()
        notification_data = [{
            'id': notification.id,
            'type': notification.type,
            'message': notification.message,
            'data': json.loads(notification.data) if notification.data else {},
            'created_at': notification.created_at.isoformat()
        } for notification in notifications]
        # Emit the notifications to the user
        socketio.emit('notification', {
            'type': 'initial_notifications',
            'data': notification_data
        }, to=request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    if current_user.is_authenticated:
        # Remove user from connected users dictionary
        if current_user.id in connected_users:
            del connected_users[current_user.id]
        # Leave personal room
        leave_room(f'user_{current_user.id}')
        print(f"User {current_user.username} disconnected")

# Helper function to send notifications to a specific user
def send_notification_to_user(user_id, notification_type, data):
    # Create a new notification instance
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        message=data.get('message', ''),
        data=json.dumps(data),  # Store additional data as JSON
        is_read=False
    )
    
    # Save the notification to the database
    db.session.add(notification)
    db.session.commit()
    # Check if the user is connected
    sid = connected_users.get(user_id)
    if sid:
        # Emit the notification to the specific user
        socketio.emit('notification', {
            'type': notification_type,
            'data': data
        }, to=sid)