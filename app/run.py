from app import create_app, socketio, db
from flask_migrate import Migrate

app = create_app()
migrate = Migrate(app, db)


if __name__ == "__main__":
    socketio.run(app)
    
