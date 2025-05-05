from app import app, db
from app.models import User, Game, Stats
from datetime import datetime
 
# Initialize the app context
with app.app_context():
    # Drop all tables and recreate them (optional, for a clean slate)
    db.drop_all()
    db.create_all()
 
    # Seed Users
    user1 = User(username="john_doe", email="john@example.com", password_hash="hashed_password", first_name="John", last_name="Doe")
    user2 = User(username="jane_doe", email="jane@example.com", password_hash="hashed_password", first_name="Jane", last_name="Doe")
    db.session.add(user1)
    db.session.add(user2)
 
 
    # Seed Stats
    stats1 = Stats(user_id=1, win_streak=3, total_wins=10, win_percentage=75.0, total_games=15, time_spent=3600, start_date=datetime.strptime("2025-01-01", "%Y-%m-%d"))
    stats2 = Stats(user_id=2, win_streak=0, total_wins=5, win_percentage=50.0, total_games=10, time_spent=1800, start_date=datetime.strptime("2025-02-01", "%Y-%m-%d"))
    db.session.add(stats1)
    db.session.add(stats2)
 
    # Commit the changes
    db.session.commit()
 
    # Query and display the data
    users = User.query.all()
    print("Users:")
    for user in users:
        print(f"ID: {user.id}, Username: {user.username}, Email: {user.email}")
 
    stats = Stats.query.all()
    print("\nStats:")
    for stat in stats:
        print(f"User ID: {stat.user_id}, Total Wins: {stat.total_wins}, Win Percentage: {stat.win_percentage}")