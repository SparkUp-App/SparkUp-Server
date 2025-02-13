import eventlet
eventlet.monkey_patch(all=False, socket=True)

from app.extensions import db
from app.main import create_app

app, socketio = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app)
