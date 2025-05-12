import unittest
from app import create_app, db
from app.models import User
from config import TestConfig

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
        db.session.commit()

    def tearDown(self):
        """Tear down the test environment."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_app_initialization(self):
        """Test if the app initializes correctly."""
        self.assertIsNotNone(self.app)
        self.assertEqual(self.app.config["TESTING"], True)

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

    def test_404_error(self):
        """Test if a 404 error page is displayed for an invalid route."""
        response = self.client.get("/nonexistent_route", follow_redirects=True)
        self.assertEqual(response.status_code, 404)
        self.assertIn(b"Page Not Found", response.data)  # Replace with a string from your 404 page

if __name__ == "__main__":
    unittest.main()