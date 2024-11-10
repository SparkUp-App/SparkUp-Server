import monkey  # This must be the first import

from app.main import create_app
from app.extensions import db, socketio

app = create_app()
socketio.init_app(app, cors_allowed_origins='*', async_mode='eventlet')

with app.app_context():
    db.create_all()