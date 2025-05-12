import math
from app.models import Game, LocationGuess, Stats
from app import db

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points on the Earth.
    
    Parameters:
        lat1, lon1: Latitude and longitude of the first point in decimal degrees.
        lat2, lon2: Latitude and longitude of the second point in decimal degrees.
    
    Returns:
        Distance in meters.
    """
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Radius of Earth in meters
    R = 6371000
    distance = R * c

    return distance

def serialize_guess(guess):
    return {
        'id': guess.id,
        'game_id': guess.game_id,
        'distance_error_meters': guess.distance_error_meters,
    }

def process_guess(game_id, user_id, data):
    # Fetch the game
    game = Game.query.get(game_id)
    if not game or (game.user_id and game.user_id != user_id):
        return {'error': 'Invalid game ID'}, 400

    # Calculate distance
    actual_lat = game.actual_latitude
    actual_lng = game.actual_longitude
    
    guessed_lat = data['guessed_latitude']
    guessed_lng = data['guessed_longitude']
    print(f"Actual: ({actual_lat}, {actual_lng}), Guessed: ({guessed_lat}, {guessed_lng})")
    distance = haversine_distance(actual_lat, actual_lng, guessed_lat, guessed_lng)

    # Add a new LocationGuess entry
    guess = LocationGuess(
        game_id=game.id,
        distance_error_meters=distance,
    )
    db.session.add(guess)

    # Check if the game should be finalized
    if distance <= 25:  # Correct guess threshold
        submit_game(game, user_id, True)
    elif len(game.guesses) == 3:  # Max guesses reached
        game.total_score = 0
        submit_game(game, user_id, False)
    else:
        game.total_score = max(0, game.total_score-25) 
    db.session.commit()

    return {'guesses': [serialize_guess(g) for g in game.guesses], 'score': game.total_score}

def submit_game(game, user_id, success):
    # Finalize the game
    game.finish_time = db.func.now()
    if not success:
        game.total_score = 0
    db.session.commit()

    # Update user stats
    if user_id:
        stats = Stats.query.filter_by(user_id=user_id).first()
        if not stats:
            stats = Stats(user_id=user_id, total_games=0, total_wins=0, win_streak=0, time_spent=0, start_date=db.func.now())
            db.session.add(stats)

        stats.total_games += 1
        if success:
            stats.total_wins += 1
            stats.win_streak += 1
        else:
            stats.win_streak = 0

        stats.win_percentage = (stats.total_wins / stats.total_games) * 100
        db.session.commit()

