from app.main import create_app
from app.extensions import db, socketio

app, socketio = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app)