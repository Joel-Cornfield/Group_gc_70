from flask import Flask 
from config import Config 
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_socketio import SocketIO

app = Flask(__name__)
app.config.from_object(Config)
app.config['SECRET_KEY'] = '4e2b6d9f8a7c4a937fc3882efhfjdb62b8df3sbdhfeb80d34dd0221bdc6b2a0efbb4'

db = SQLAlchemy(app)
migrate = Migrate(app, db)
socketio = SocketIO(app, cors_allowed_origins="*") 

login_manager = LoginManager()
login_manager.login_view = 'auth' # Redirect to the auth page if not logged in
login_manager.init_app(app)

from app.models import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


from app import routes, models, socket_events 