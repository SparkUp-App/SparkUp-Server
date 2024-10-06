import re

from flask import Blueprint, request, current_app
from flask_restx import Api, Resource, fields
from flask_security import hash_password, verify_password, login_user
from sqlalchemy import select, exists

from app.utils import jsonify_response
from app.models import user_datastore, Profile, User
from app.extensions import db

auth_bp = Blueprint('auth_bp', __name__)
auth_api = Api(
    auth_bp,
    version='1.0',
    title='Auth API',
    description='Auth API',
    doc='/docs',
)
auth_ns = auth_api.namespace('', description='Authentication operations')

# Models
user_model = auth_api.model('User', {
    'email': fields.String(required=True),
    'password': fields.String(required=True),
})


# Routes
@auth_ns.route('/register', methods=['POST'])
class Register(Resource):
    @auth_api.expect(user_model)
    @auth_api.response(201, 'User registered successfully')
    @auth_api.response(400, 'Validation error')
    @auth_api.response(409, 'User already exists')
    def post(self):
        data = request.get_json()
        required_fields = ['email', 'password']

        # Check required fields
        for field in required_fields:
            # Check if exist
            if field not in data:
                current_app.logger.info(f"Registration failed: {field.capitalize()} is required")
                return jsonify_response({'message': f"{field.capitalize()} is required"}, 400)
            # Check email format
            if field == 'email' and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', data['email']):
                current_app.logger.info(f"Registration failed: Invalid email format - {data['email']}")
                return jsonify_response({'message': f"{data['email']} is invalid format"}, 400)
            # Check password contains uppercase, lowercase letters, and digits
            if field == 'password' and not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$', data['password']):
                current_app.logger.info('Registration failed: Password complexity requirement not met')
                return jsonify_response({'message': 'Password must contains uppercase, lowercase letters, and digits'}, 400)

        # Check user existence
        existing_user = user_datastore.find_user(email=data['email'])
        if existing_user:
            _ = db.session.merge(existing_user)
            return jsonify_response({'message': 'User already exists'}, 409)

        try:
            new_user = user_datastore.create_user(
                email=data['email'],
                password=hash_password(data['password']),
            )
            login_user(new_user)

            current_app.logger.info(f"User registered successfully: {data['email']}")

            db.session.add(new_user)
            db.session.commit()

            return jsonify_response({
                'message': 'User created successfully',
                'user_id': new_user.id,
            }, 201)

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to register user or create chat room: {e}")
            return jsonify_response({
                'error': str(e),
                'message': 'An error occurred during registration'
            }, 500)

        finally:
            db.session.close()


@auth_ns.route('/login', methods=['POST'])
class Login(Resource):
    @auth_api.expect(user_model)
    @auth_api.response(200, 'User logged successfully')
    @auth_api.response(400, 'Validation error')
    @auth_api.response(401, 'Invalid login credentials')
    def post(self):
        data = request.get_json()
        required_fields = ['email', 'password']

        # Check required fields
        for field in required_fields:
            if field not in data:
                current_app.logger.info(f"Login failed: {field.capitalize()} is required")
                return jsonify_response({'message': 'Login field and password are required'}, 400)

        # Check user
        user = user_datastore.find_user(email=data['email'])
        if not user or not verify_password(data['password'], user.password):
            if not user:
                current_app.logger.error(f"Login attempt failed for unregistered email: {data['email']}")
            else:
                current_app.logger.error(f"Login attempt failed for login field: {data['email']} due to incorrect password")
            return jsonify_response({'message': 'Invalid login credentials'}, 401)

        try:
            user = db.session.merge(user)
            login_user(user)

            # Check profile
            profile_exists = db.session.execute(select(exists().where(Profile.id == user.id))).scalar()

            current_app.logger.info(f"User login successfully: {user.id}, email: {user.email}")

            return jsonify_response({
                'message': 'User login successfully',
                'profile_exists': profile_exists,
                'user_id': user.id
            }, 200)

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to login user: {e}")
            return jsonify_response({
                'error': str(e),
                'message': 'An error occurred during login'},
                500
            )