from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)

class Friend(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    __table_args__  = (
        db.UniqueConstraint('user_id', 'friend_id', name='unique_friendship')
    )

class GameHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    guess_location = db.Column(db.String(120), nullable=False)
    guess_time = db.Column(db.DateTime, nullable=False)
    result = db.Column(db.String(120), nullable=False)
    time_finished = db.Column(db.Integer, nullable=False)

class Stats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    win_streak = db.Column(db.Integer, nullable=True)
    total_wins = db.Column(db.Integer, nullable=True)
    win_percentage = db.Column(db.Float, nullable=True)
    total_games = db.Column(db.Integer, nullable=True)
    time_spent = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)