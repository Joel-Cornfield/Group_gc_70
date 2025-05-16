# Group_gc_70

## Purpose and Design
This web application is a UWA-themed GeoGuessr-style game designed to challenge users to identify locations around the UWA campus based on images and hints. Players log in to their accounts, guess the location, earn scores, and view their performance stats. The app includes user authentication, real-time gameplay, personal statistics, leaderboards, and a profile system, along with support for a friend system and receiving notifications. 

Users can view the stats pages of their friends, enabling a form of controlled/private data sharing that enhances friendly competition.

Admins can manage location data and game content, while players can challenge themselves and track their progress.

## Group Members
| UWA ID     | Name                 | GitHub Username   |
|------------|----------------------|-------------------|
| 23749925   | Joel Cornfield       | Joel-Cornfield    |
| 23715959   | Malachy McGrath      | kiki286           |
| 24268033   | Rachel Hii           | RachelHiiYuZhen   |
| 23863104   | Jashan Toor          | Jashan-Toor       |

*(Replace the above with your actual group member details.)*

## How to Launch the Application
1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-org/your-repo.git
   cd your-repo

Create and activate a virtual environment:
bashpython -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

Install dependencies:
```bash
pip install -r requirements.txt
```

Use the provided database:
A small pre-populated app.db is included in the repository with a couple user accounts (including admin), locations, hints and images. 

Run the application:
```bash
flask run
```

By default, the app runs on http://127.0.0.1:5000/
# How to Run the Tests

Run unit or integration tests using:
```bash
python -m unittest tests/test_unit.py
```
Run Selenium browser-based tests using:
```bash
python -m unittest tests/test_selenium.py
```

Browser Options for Selenium
The default browser is Chrome. To change the browser used in Selenium tests, edit the BROWSER variable in tests/test_selenium.py:
```python
BROWSER = "firefox"  # Options: "chrome", "firefox", "edge"
```
