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
        db.create_all()
        test_user = User(username="testuser", email="testuser@example.com", first_name="Test", last_name="User")
        test_user.set_password("password123")
        db.session.add(test_user)
        db.session.commit()

        # Start the Flask server in a separate thread
        # This is a workaround because I kept getting a windows permission error when trying to spawn a different proccess
        def run_server():
            self.app.run("127.0.0.1", 5000, use_reloader=False)

        self.server_thread = Thread(target=run_server)
        self.server_thread.daemon = True
        self.server_thread.start()

        # Initialize the Selenium WebDriver in headless mode
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")  # Run in headless mode
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
        driver = self.driver

        # Navigate to the login page
        login_link = driver.find_element(By.LINK_TEXT, "Login/Signup")
        login_link.click()

        # Wait for the login form to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
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
            EC.presence_of_element_located((By.CLASS_NAME, "navbar"))
        )

        # Open the dropdown menu
        dropdown_toggle = driver.find_element(By.CSS_SELECTOR, ".dropdown-toggle")
        dropdown_toggle.click()

        # Wait for the "Logout" link to appear in the dropdown
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.LINK_TEXT, "Logout"))
        )

        # Verify that the "Logout" link is present
        self.assertIn("Logout", driver.page_source)

if __name__ == "__main__":
    unittest.main()
