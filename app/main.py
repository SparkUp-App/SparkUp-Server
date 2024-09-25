import socketio
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from app.extensions import db, socketio
from app.config import Config
from app.routes import *


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    socketio.init_app(app)

    app.register_blueprint(auth_bp, url_prefix='/auth')

    @app.errorhandler(HTTPException)
    def http_exception_handler(error):
        response = error.get_response()
        response.data = jsonify({
            'code': error.code,
            'name': error.name,
            'description': error.description,
        }).data
        return response

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Resource not found',
            'message': str(error)
        }), 404

    return app, socketio
