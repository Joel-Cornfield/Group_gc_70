from datetime import datetime
from app import app, db
from app.models import User, Friend, Notification, Game, Stats, Location, Hint, LocationGuess
import json

with app.app_context():
    db.drop_all()
    db.create_all()

    # Seed Users
    user1 = User(username="john_doe", email="john@example.com", first_name="John", last_name="Doe")
    user1.set_password("password123")

    user2 = User(username="jane_doe", email="jane@example.com", first_name="Jane", last_name="Doe")
    user2.set_password("password456")

    db.session.add_all([user1, user2])
    db.session.flush()  # Assigns IDs before we use them below

    # Seed Stats
    stats1 = Stats(
        user_id=user1.id,
        win_streak=3,
        total_wins=10,
        win_percentage=75.0,
        total_games=15,
        time_spent=3600,
        start_date=datetime(2025, 1, 1)
    )
    stats2 = Stats(
        user_id=user2.id,
        win_streak=0,
        total_wins=5,
        win_percentage=50.0,
        total_games=10,
        time_spent=1800,
        start_date=datetime(2025, 2, 1)
    )
    db.session.add_all([stats1, stats2])

    # Load and seed Locations and Hints from JSON
    with open("app/static/locations.json", "r", encoding="utf-8") as file:
        locations_data = json.load(file)

    for loc_data in locations_data:
        location = Location(
            name=loc_data["name"],
            latitude=loc_data["latitude"],
            longitude=loc_data["longitude"],
            department=loc_data.get("department")
        )
        db.session.add(location)

        for hint_text in loc_data.get("hints", []):
            db.session.add(Hint(location=location, text=hint_text))

    db.session.commit()

    # Display summary
    print("\nUsers:")
    for user in User.query.all():
        print(f"{user.id} - {user.username} ({user.email})")

    print("\nStats:")
    for stat in Stats.query.all():
        print(f"User {stat.user_id}: Wins={stat.total_wins}, Win%={stat.win_percentage}")

    print("\nLocations and Hints:")
    for loc in Location.query.all():
        print(f"{loc.id} - {loc.name}")
        for hint in loc.hints:
            print(f"  Hint: {hint.text}")

