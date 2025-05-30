from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(db.Model, UserMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)
    profile_picture_data = db.Column(db.LargeBinary, nullable=True) 
    profile_picture_mimetype = db.Column(db.String(50), nullable=True)
    admin = db.Column(db.Boolean, default=False)

    friends = db.relationship("Friend", back_populates="user", foreign_keys="Friend.user_id")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Friend(db.Model):
    __tablename__ = "friend"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", name="fk_friend_user_id"), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey("user.id", name="fk_friend_friend_id"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending")

    user = db.relationship("User", back_populates="friends", foreign_keys=[user_id])
    friend = db.relationship("User", foreign_keys=[friend_id])

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    type = db.Column(db.String(50), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    data = db.Column(db.Text, nullable=True)  
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', foreign_keys=[user_id], backref='notifications')
    sender = db.relationship('User', foreign_keys=[sender_id])

class LocationGuess(db.Model):
    __tablename__ = "location_guess"

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("game.id", ondelete="CASCADE", name="fk_location_guess_game_id"), nullable=False)
    distance_error_meters = db.Column(db.Float, nullable=False)
    guess_time = db.Column(db.DateTime, server_default=db.func.now())
    game = db.relationship("Game", back_populates="guesses")

class Game(db.Model):
    __tablename__ = "game"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE", name="fk_game_user_id"), nullable=True)
    start_time = db.Column(db.DateTime, server_default=db.func.now())
    finish_time = db.Column(db.DateTime, nullable=True)
    total_score = db.Column(db.Integer, default=0)
    location_name = db.Column(db.String(255), nullable=False)
    actual_latitude = db.Column(db.Float, nullable=False)
    actual_longitude = db.Column(db.Float, nullable=False)
    guesses = db.relationship("LocationGuess", back_populates="game", cascade="all, delete-orphan")

class Stats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Foreign key to User
    total_games = db.Column(db.Integer, default=0)
    total_wins = db.Column(db.Integer, default=0)
    win_streak = db.Column(db.Integer, default=0)
    time_spent = db.Column(db.Integer, default=0)
    win_percentage = db.Column(db.Float, default=0.0)
    start_date = db.Column(db.DateTime, nullable=False)

class Location(db.Model):
    __tablename__ = "location"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    department = db.Column(db.String(255), nullable=True)
    image_data = db.Column(db.LargeBinary, nullable=True)  # New column for storing image data
    image_mimetype = db.Column(db.String(255), nullable=True)  # Store the image MIME type
    hints = db.relationship("Hint", back_populates="location", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Location {self.name}>"

class Hint(db.Model):
    __tablename__ = "hint"

    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey("location.id", ondelete="CASCADE"), nullable=False)
    text = db.Column(db.String(255), nullable=False)
    location = db.relationship("Location", back_populates="hints")

    def __repr__(self):
        return f"<Hint {self.text}>"
