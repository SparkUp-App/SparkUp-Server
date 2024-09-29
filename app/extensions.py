from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_security import Security
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import sessionmaker

db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO()
security = Security()
db_session = sessionmaker()
