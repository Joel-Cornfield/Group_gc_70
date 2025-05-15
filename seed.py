from datetime import datetime, timedelta
from app import app, db
from app.models import User, Friend, Notification, Game, Stats, Location, Hint, LocationGuess
import json
import random

with app.app_context():
    db.drop_all()
    db.create_all()

    # --- Seed Users ---
    users = []

    admin = User(username="admin", email="admin@uwa.edu.au", first_name="Admin", last_name="User", admin=True)
    admin.set_password("admin")
    users.append(admin)

    for i in range(1, 6):
        u = User(
            username=f"user{i}",
            email=f"user{i}@example.com",
            first_name=f"First{i}",
            last_name=f"Last{i}"
        )
        u.set_password("test1234")
        users.append(u)

    db.session.add_all(users)
    db.session.flush()

    # --- Seed Stats ---
    for user in users:
        s = Stats(
            user_id=user.id,
            win_streak=random.randint(0, 5),
            total_wins=random.randint(0, 20),
            win_percentage=round(random.uniform(30, 100), 2),
            total_games=random.randint(10, 30),
            time_spent=random.randint(500, 5000),
            start_date=datetime(2024, random.randint(1, 12), random.randint(1, 28))
        )
        db.session.add(s)

    # --- Seed Locations and Hints ---
    with open("app/static/locations.json", "r", encoding="utf-8") as file:
        locations_data = json.load(file)

    locations = []
    for loc_data in locations_data:
        location = Location(
            name=loc_data["name"],
            latitude=loc_data["latitude"],
            longitude=loc_data["longitude"],
            department=loc_data.get("department")
        )
        db.session.add(location)
        locations.append(location)

        for hint_text in loc_data.get("hints", []):
            db.session.add(Hint(location=location, text=hint_text))

    db.session.flush()

    # --- Seed Games and LocationGuesses ---
    for user in users:
        for _ in range(2):  # 2 games per user
            loc = random.choice(locations)
            start = datetime.utcnow() - timedelta(minutes=random.randint(5, 20))
            finish = start + timedelta(minutes=random.randint(1, 5))

            game = Game(
                user_id=user.id,
                start_time=start,
                finish_time=finish,
                total_score=random.randint(50, 500),
                location_name=loc.name,
                actual_latitude=loc.latitude,
                actual_longitude=loc.longitude
            )
            db.session.add(game)
            db.session.flush()

            # Add guesses
            for _ in range(random.randint(2, 4)):
                error = round(random.uniform(5, 150), 2)  # Simulated guess error in meters
                guess = LocationGuess(
                    game_id=game.id,
                    distance_error_meters=error
                )
                db.session.add(guess)

    db.session.commit()

    # --- Summary Output ---
    print("\nUsers:")
    for u in User.query.all():
        print(f"{u.id}: {u.username} ({'Admin' if u.admin else 'User'})")

    print("\nLocations and Hints:")
    for l in Location.query.all():
        print(f"{l.id}: {l.name}")
        for h in l.hints:
            print(f"  Hint: {h.text}")

    print("\nGames:")
    for g in Game.query.all():
        print(f"Game {g.id}: User {g.user_id}, Location: {g.location_name}, Score: {g.total_score}")
