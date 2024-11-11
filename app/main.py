import logging
from sqlalchemy import text
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from app.extensions import db, socketio, security, migrate
from app.models import user_datastore
from app.config import Config
from app.routes import *


def create_app(config_class=Config):
    # Logger setup
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )
    logger = logging.getLogger(__name__)
    logger.info('Logger is set up')

    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    security.init_app(app, user_datastore)
    socketio.init_app(app, cors_allowed_origins='*', async_mode='eventlet')

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(profile_bp, url_prefix='/profile')
    app.register_blueprint(post_bp, url_prefix='/post')
    app.register_blueprint(comment_bp, url_prefix='/comment')
    app.register_blueprint(applicant_bp, url_prefix='/applicant')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(reference_bp, url_prefix='/reference')
    app.register_blueprint(chat_bp, url_prefix='/chat')

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

    @app.route('/test_db')
    def test_db():
        try:
            result = db.session.execute(text('SELECT 1'))
            return "Database connection successful!", 200
        except Exception as e:
            return str(e), 500

    return app, socketio
