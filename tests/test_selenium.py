import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from app import create_app, db
from app.models import User
from config import TestConfig
from threading import Thread

class SeleniumTestCase(unittest.TestCase):
    def setUp(self):
        """Set up the Flask server and Selenium WebDriver."""
        # Create the Flask app with the test configuration
        self.app = create_app(config_class=TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Create the test database and add a test user
        db.drop_all()
        db.create_all()
        print("Database created")
        test_user = User(username="testuser", email="testuser@example.com", first_name="Test", last_name="User")
        test_user.set_password("password123")
        db.session.add(test_user)
        db.session.commit()
        user = User.query.filter_by(username="testuser").first()
        print("Test user created:", user.username)

        # Start the Flask server in a separate thread
        # This is a workaround because I kept getting a windows permission error when trying to spawn a different proccess
        def run_server():
            self.app.run("127.0.0.1", 5000, use_reloader=False)

        self.server_thread = Thread(target=run_server)
        self.server_thread.daemon = True
        self.server_thread.start()

        # Initialize the Selenium WebDriver in headless mode
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")  # Run in headless mode (optional)
        options.add_argument("--disable-gpu")  # Disable GPU acceleration
        options.add_argument("--window-size=1920,1080")  # Set a default window size
        options.add_argument("--disable-password-manager-reauthentication")  # Disable password manager alerts
        options.add_argument("--disable-features=PasswordCheck")  # Disable password safety check
        options.add_argument("--no-sandbox")  # Required for some environments
        self.driver = webdriver.Chrome(options=options)
        self.driver.get("http://127.0.0.1:5000/")  # Base URL of the app

    def tearDown(self):
        """Tear down the Flask server and Selenium WebDriver."""
        # Stop the Flask server
        self.server_thread.join(1)  # Allow the thread to terminate

        # Close the browser and quit the WebDriver
        self.driver.quit()

        # Remove the test database
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_login(self):
        """Test the login functionality."""
        with self.app.app_context():  # Ensure the test runs within the application context
            driver = self.driver

            # Navigate to the login page
            login_link = driver.find_element(By.LINK_TEXT, "Login/Signup")
            login_link.click()

            # Wait for the login form to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )

            # Fill in the login form
            username_field = driver.find_element(By.NAME, "username")
            password_field = driver.find_element(By.NAME, "password")
            username_field.send_keys("testuser")
            password_field.send_keys("password123")

            # Submit the form
            password_field.send_keys(Keys.RETURN)

            # Wait for the home page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "notificationBell"))
            )

            # Verify that the user is logged in
            self.assertIn("notificationBell", driver.page_source)
    
    
    def test_logout(self):
        """Test the logout functionality."""
        with self.app.app_context():  
            driver = self.driver
            self.test_login()  # Log in first
            # Open the dropdown menu
            dropdown_toggle = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".dropdown-toggle"))
            )
            dropdown_toggle.click()

            # Click the "Logout" link
            logout_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.dropdown-item.text-danger"))
            )
            logout_link.click()

            # Wait for the login page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.LINK_TEXT, "Login/Signup"))
            )

            # Verify that the user is logged out
            self.assertIn("Login/Signup", driver.page_source)


    def test_signup(self):
        """Test the signup functionality."""
        with self.app.app_context():  
            driver = self.driver

            # Navigate to the signup page
            signup_link = driver.find_element(By.LINK_TEXT, "Login/Signup")
            signup_link.click()

            # Wait for the signup tab to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "signup-tab"))
            )

            # Click the "Sign Up" tab
            signup_tab = driver.find_element(By.ID, "signup-tab")
            signup_tab.click()

            # Wait for the signup form to be visible
            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.ID, "signup-username"))
            )

            # Fill in the signup form
            first_name_field = driver.find_element(By.ID, "signup-first-name")
            last_name_field = driver.find_element(By.ID, "signup-last-name")
            username_field = driver.find_element(By.ID, "signup-username")
            email_field = driver.find_element(By.ID, "signup-email")
            password_field = driver.find_element(By.ID, "signup-password")
            confirm_password_field = driver.find_element(By.ID, "signup-confirm-password")

            first_name_field.send_keys("New")
            last_name_field.send_keys("User")
            username_field.send_keys("newuser")
            email_field.send_keys("newuser@example.com")
            password_field.send_keys("password123")
            confirm_password_field.send_keys("password123")

            # Submit the form
            confirm_password_field.send_keys(Keys.RETURN)

            # Wait for the signup form to be visible
            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.ID, "username"))
            )

            # Verify that the user is logged in
            self.assertIn("Welcome back!", driver.page_source)

    def test_update_profile(self):
        """Test updating the profile information."""
        with self.app.app_context():  
            driver = self.driver

            # Log in first
            self.test_login()

            # Open the dropdown menu
            dropdown_toggle = driver.find_element(By.CSS_SELECTOR, ".dropdown-toggle")
            dropdown_toggle.click()

            # Navigate to the profile page
            profile_link = driver.find_element(By.LINK_TEXT, "Your Profile")
            profile_link.click()

            # Wait for the profile page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "current_password"))
            )

            # Update the profile information
            current_password_field = driver.find_element(By.ID, "current_password")
            new_password_field = driver.find_element(By.ID, "new_password")
            confirm_password_field = driver.find_element(By.ID, "confirm_password")
            current_password_field.send_keys("password123")
            new_password_field.send_keys("newpassword123")
            confirm_password_field.send_keys("newpassword123")

            # Submit the form
            confirm_password_field.send_keys(Keys.RETURN)

            # Verify that the profile update was successful
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "alert-success"))
            )
            self.assertIn("Password updated successfully", driver.page_source)

if __name__ == "__main__":
    unittest.main()
