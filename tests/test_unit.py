import unittest
from app import create_app, db
from app.models import User, Game, Location, Hint, Friend, Notification, LocationGuess, Stats
from config import TestConfig
from datetime import datetime, timedelta
import json
from app.game_logic import haversine_distance, process_guess

class AppTestCase(unittest.TestCase):
    def setUp(self):
        """Set up the test environment."""
        self.app = create_app(config_class=TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()
        
        # Create a test user
        self.test_user = User(username="testuser", email="testuser@example.com", first_name="Test", last_name="User")
        self.test_user.set_password("password123")
        db.session.add(self.test_user)
        
        # Create another test user for friend functionality
        self.test_friend = User(username="testfriend", email="testfriend@example.com", first_name="Test", last_name="Friend")
        self.test_friend.set_password("password123")
        db.session.add(self.test_friend)
        
        # Create a test admin user
        self.test_admin = User(username="testadmin", email="testadmin@example.com", first_name="Test", last_name="Admin", admin=True)
        self.test_admin.set_password("adminpass123")
        db.session.add(self.test_admin)
        
        # Create a test location
        self.test_location = Location(
            name="UWA Library", 
            latitude=-31.979296, 
            longitude=115.817674,
            department="Main Campus"
        )
        db.session.add(self.test_location)
        
        # Add hints for the test location
        hint1 = Hint(location=self.test_location, text="Where students study")
        hint2 = Hint(location=self.test_location, text="Has lots of books")
        db.session.add_all([hint1, hint2])
        
        db.session.commit()
        
        # Store IDs for later use
        self.user_id = self.test_user.id
        self.friend_id = self.test_friend.id
        self.admin_id = self.test_admin.id
        self.location_id = self.test_location.id

    def login(self, username="testuser", password="password123"):
        return self.client.post("/auth/login", data={
            "username": username,
            "password": password
        }, follow_redirects=True)
    
    def tearDown(self):
        """Tear down the test environment."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_app_initialization(self):
        """Test if the app initializes correctly."""
        self.assertIsNotNone(self.app)
        self.assertEqual(self.app.config["TESTING"], True)
    
    # ------------------------------------------------- #
    # Auth Tests #
    
    def test_login_success(self):
        """Test if a user can log in successfully."""
        response = self.client.post("/auth/login", data={
            "username": "testuser",
            "password": "password123"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Explore UWA", response.data)
    
    def test_login_failure(self):
        """Test if login fails with incorrect credentials."""
        response = self.client.post("/auth/login", data={
            "username": "testuser",
            "password": "wrongpassword"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Welcome back!", response.data)
    
    def test_signup(self):
        """Test if a new user can sign up successfully."""
        response = self.client.post("/auth/signup", data={
            "username": "newuser",
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
            "password": "newpassword123",
            "confirm_password": "newpassword123"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Welcome back!", response.data)
    
    def test_logout(self):
        """Test if a user can log out successfully"""
        response = self.client.post("/auth/login", data={
            "username": "testuser",
            "password": "password123"
        }, follow_redirects=True)
        self.assertIn(b"Explore UWA", response.data)
        
        response = self.client.get("/auth/logout", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"You have been logged out", response.data)
    
    # ------------------------------------------------- #
    # Error Tests #
    
    def test_404_error(self):
        """Test if a 404 error page is displayed for an invalid route."""
        response = self.client.get("/nonexistent_route", follow_redirects=True)
        self.assertEqual(response.status_code, 404)
        self.assertIn(b"Page Not Found", response.data)
    
    # ------------------------------------------------- #
    # Game Tests #
    
    def test_game_initialization(self):
        """Test if a new game can be initialized."""
        self.login()
        response = self.client.get("/play")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('game_id', data)
        self.assertIn('guess_image', data)
        
        # Verify game was created in database
        game = Game.query.get(data['game_id'])
        self.assertIsNotNone(game)
        self.assertEqual(game.user_id, self.user_id)
        self.assertEqual(game.total_score, 100)
    
    def test_game_guess_correct(self):
        """Test submitting a correct guess."""
        # Create a game
        game = Game(
            user_id=self.user_id,
            actual_latitude=self.test_location.latitude,
            actual_longitude=self.test_location.longitude,
            location_name=self.test_location.name,
            total_score=100
        )
        db.session.add(game)
        db.session.commit()
        
        # Submit a correct guess (within 25 meters)
        self.login()
        response = self.client.post("/guess", 
            json={
                'game_id': game.id,
                'guessed_latitude': self.test_location.latitude + 0.0001,  # Very close
                'guessed_longitude': self.test_location.longitude
            },
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('guesses', data)
        self.assertIn('score', data)
        
        # Check that game was updated
        updated_game = Game.query.get(game.id)
        self.assertIsNotNone(updated_game.finish_time)  # Game should be finished
        
        # Check that stats were updated
        stats = Stats.query.filter_by(user_id=self.user_id).first()
        self.assertIsNotNone(stats)
        self.assertEqual(stats.total_games, 1)
        self.assertEqual(stats.total_wins, 1)
        self.assertEqual(stats.win_streak, 1)
    
    def test_game_guess_incorrect(self):
        """Test submitting incorrect guesses."""
        # Create a game
        game = Game(
            user_id=self.user_id,
            actual_latitude=self.test_location.latitude,
            actual_longitude=self.test_location.longitude,
            location_name=self.test_location.name,
            total_score=100
        )
        db.session.add(game)
        db.session.commit()
        
        self.login()
        
        # Submit first wrong guess
        response = self.client.post("/guess", 
            json={
                'game_id': game.id,
                'guessed_latitude': self.test_location.latitude + 0.1,  # Far away
                'guessed_longitude': self.test_location.longitude + 0.1
            },
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data['guesses']), 1)
        self.assertEqual(data['score'], 75)  # Score reduced by 25
        
        # Submit second wrong guess
        response = self.client.post("/guess", 
            json={
                'game_id': game.id,
                'guessed_latitude': self.test_location.latitude - 0.1,
                'guessed_longitude': self.test_location.longitude - 0.1
            },
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data['guesses']), 2)
        self.assertEqual(data['score'], 50)  # Score reduced by another 25
        
        # Submit third wrong guess (game should end)
        response = self.client.post("/guess", 
            json={
                'game_id': game.id,
                'guessed_latitude': self.test_location.latitude - 0.2,
                'guessed_longitude': self.test_location.longitude - 0.2
            },
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data['guesses']), 3)
        self.assertEqual(data['score'], 0)  # Score should be 0 after 3 wrong guesses
        
        # Check that game was updated
        updated_game = Game.query.get(game.id)
        self.assertIsNotNone(updated_game.finish_time)  # Game should be finished
        
        # Check that stats were updated
        stats = Stats.query.filter_by(user_id=self.user_id).first()
        self.assertIsNotNone(stats)
        self.assertEqual(stats.total_games, 1)
        self.assertEqual(stats.total_wins, 0)
        self.assertEqual(stats.win_streak, 0)
    
    def test_get_hint(self):
        """Test retrieving a hint."""
        # Create a game
        game = Game(
            user_id=self.user_id,
            actual_latitude=self.test_location.latitude,
            actual_longitude=self.test_location.longitude,
            location_name=self.test_location.name,
            total_score=100
        )
        db.session.add(game)
        db.session.commit()
        
        self.login()
        response = self.client.post(f"/hint/{game.id}", 
            json={'received_hint_ids': []},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('hint', data)
        self.assertEqual(data['score'], 90)  # Score reduced by 10 for hint
        
        # Test getting a second hint
        game_update = Game.query.get(game.id)
        self.assertEqual(game_update.total_score, 90)
        
        hint1 = Hint.query.filter_by(location_id=self.location_id).first()
        response = self.client.post(f"/hint/{game.id}", 
            json={'received_hint_ids': [hint1.id]},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('hint', data)
        self.assertEqual(data['score'], 80)  # Score reduced by another 10
    
    def test_unblur(self):
        """Test unblurring an image."""
        # Create a game
        game = Game(
            user_id=self.user_id,
            actual_latitude=self.test_location.latitude,
            actual_longitude=self.test_location.longitude,
            location_name=self.test_location.name,
            total_score=100
        )
        db.session.add(game)
        db.session.commit()
        
        self.login()
        response = self.client.post(f"/unblur/{game.id}", 
            json={},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['score'], 80)  # Score reduced by 20 for unblur
    
    def test_haversine_distance(self):
        """Test the haversine distance calculation function."""
        # Distance between two points in Perth, WA
        distance = haversine_distance(-31.95, 115.86, -31.96, 115.87)
        self.assertIsInstance(distance, float)
        self.assertGreater(distance, 0)
        
        # Test same point should be zero distance
        distance = haversine_distance(-31.95, 115.86, -31.95, 115.86)
        self.assertEqual(distance, 0)
    
    # ------------------------------------------------- #
    # Friend Tests #
    
    def test_add_friend(self):
        """Test adding a friend."""
        self.login()
        response = self.client.post("/api/friends/add",
            json={"username": "testfriend"},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('Friend request sent', data['message'])
        
        # Verify friend request was created in database
        friend_request = Friend.query.filter_by(user_id=self.user_id, friend_id=self.friend_id).first()
        self.assertIsNotNone(friend_request)
        self.assertEqual(friend_request.status, "pending")
    
    def test_get_friend_requests(self):
        """Test getting pending friend requests."""
        # Create a friend request
        friend_request = Friend(user_id=self.friend_id, friend_id=self.user_id, status="pending")
        db.session.add(friend_request)
        db.session.commit()
        
        self.login()
        response = self.client.get("/api/friends/requests")
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['user_id'], self.friend_id)
    
    def test_accept_friend_request(self):
        """Test accepting a friend request."""
        # Create a friend request
        friend_request = Friend(user_id=self.friend_id, friend_id=self.user_id, status="pending")
        db.session.add(friend_request)
        db.session.commit()
        
        self.login()
        response = self.client.post("/api/friends/accept",
            json={"request_id": friend_request.id},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('accepted', data['message'])
        
        # Verify request was updated to accepted
        updated_request = Friend.query.get(friend_request.id)
        self.assertEqual(updated_request.status, "accepted")
        
        # Verify reciprocal relationship was created
        reciprocal = Friend.query.filter_by(user_id=self.user_id, friend_id=self.friend_id).first()
        self.assertIsNotNone(reciprocal)
        self.assertEqual(reciprocal.status, "accepted")
    
    def test_reject_friend_request(self):
        """Test rejecting a friend request."""
        # Create a friend request
        friend_request = Friend(user_id=self.friend_id, friend_id=self.user_id, status="pending")
        db.session.add(friend_request)
        db.session.commit()
        
        self.login()
        response = self.client.post("/api/friends/reject",
            json={"request_id": friend_request.id},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('rejected', data['message'])
        
        # Verify request was deleted
        deleted_request = Friend.query.get(friend_request.id)
        self.assertIsNone(deleted_request)
    
    def test_get_friends(self):
        """Test getting list of friends."""
        # Create an accepted friendship
        friendship1 = Friend(user_id=self.user_id, friend_id=self.friend_id, status="accepted")
        friendship2 = Friend(user_id=self.friend_id, friend_id=self.user_id, status="accepted")
        db.session.add_all([friendship1, friendship2])
        db.session.commit()
        
        self.login()
        response = self.client.get("/api/friends")
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['id'], self.friend_id)
    
    def test_remove_friend(self):
        """Test removing a friend."""
        # Create an accepted friendship
        friendship1 = Friend(user_id=self.user_id, friend_id=self.friend_id, status="accepted")
        friendship2 = Friend(user_id=self.friend_id, friend_id=self.user_id, status="accepted")
        db.session.add_all([friendship1, friendship2])
        db.session.commit()
        
        self.login()
        response = self.client.post("/api/friends/remove",
            json={"friend_id": self.friend_id},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('removed', data['message'])
        
        # Verify both friendship records were deleted
        friendship1 = Friend.query.filter_by(user_id=self.user_id, friend_id=self.friend_id).first()
        friendship2 = Friend.query.filter_by(user_id=self.friend_id, friend_id=self.user_id).first()
        self.assertIsNone(friendship1)
        self.assertIsNone(friendship2)
    
    # ------------------------------------------------- #
    # Notification Tests #
    
    def test_get_notifications(self):
        """Test getting user notifications."""
        # Create notifications for the user
        notification = Notification(
            user_id=self.user_id,
            sender_id=self.friend_id,
            type="friend_request",
            message="Friend request from testfriend",
            data='{"request_id": 1}'
        )
        db.session.add(notification)
        db.session.commit()
        
        self.login()
        response = self.client.get("/api/notifications")
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        # Check the notifications are in descending order (newest first)
        self.assertEqual(data[0]['type'], "friend_request")
    
    def test_mark_notification_read(self):
        """Test marking a notification as read."""
        # Create a notification
        notification = Notification(
            user_id=self.user_id,
            type="system",
            message="Test notification",
            is_read=False
        )
        db.session.add(notification)
        db.session.commit()
        
        self.login()
        response = self.client.post("/api/notifications/mark-read",
            json={"notification_id": notification.id},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        # Verify notification was marked as read
        updated_notification = Notification.query.get(notification.id)
        self.assertTrue(updated_notification.is_read)
    
    def test_mark_all_notifications_read(self):
        """Test marking all notifications as read."""
        # Create multiple notifications
        notification1 = Notification(
            user_id=self.user_id,
            type="system",
            message="Test notification 1",
            is_read=False
        )
        notification2 = Notification(
            user_id=self.user_id,
            type="system",
            message="Test notification 2",
            is_read=False
        )
        db.session.add_all([notification1, notification2])
        db.session.commit()
        
        self.login()
        response = self.client.post("/api/notifications/mark-all-read")
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        # Verify all notifications were marked as read
        notifications = Notification.query.filter_by(user_id=self.user_id, is_read=False).all()
        self.assertEqual(len(notifications), 0)
    
    # ------------------------------------------------- #
    # Admin Tests #
    
    def test_admin_page_access(self):
        """Test that only admin users can access the admin page."""
        # Test with regular user
        self.login()
        response = self.client.get("/admin")
        self.assertEqual(response.status_code, 302)  # Should redirect
        
        # Test with admin user
        self.client.get("/auth/logout")
        self.client.post("/auth/login", data={
            "username": "testadmin",
            "password": "adminpass123"
        })
        response = self.client.get("/admin")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Manage Locations", response.data)
    
    def test_admin_add_location(self):
        """Test adding a new location as admin."""
        self.client.post("/auth/login", data={
            "username": "testadmin",
            "password": "adminpass123"
        })
        
        # Create a mock form data
        form_data = {
            "location_name": "New Test Location",
            "latitude": "31.975",
            "longitude": "115.819",
            "department": "Test Department",
            "hints": ["Test hint 1", "Test hint 2"]
        }
        
        response = self.client.post("/admin", data=form_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Verify the location was added
        new_location = Location.query.filter_by(name="New Test Location").first()
        self.assertIsNotNone(new_location)
        self.assertEqual(len(new_location.hints), 2)

if __name__ == "__main__":
    unittest.main()