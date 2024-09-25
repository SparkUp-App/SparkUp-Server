import re

from flask import Blueprint, request, jsonify
from flask_restx import Api, Namespace, Resource, fields

from app.utils import jsonify_response

auth_bp = Blueprint('auth_bp', __name__)
api = Api(
    auth_bp,
    version='1.0',
    title='Auth API',
    description='Auth API',
    doc='/docs',
)
ns = Namespace('', description='Authentication operations')
api.add_namespace(ns)

user_model = api.model('User', {
    'email': fields.String(required=True),
    'password': fields.String(required=True),
})


@ns.route('/register', methods=['POST'])
class Register(Resource):
    @api.expect(user_model)
    @api.response(201, 'User registered successfully')
    @api.response(400, 'Validation error')
    @api.response(409, 'User already exists')
    def post(self):
        data = request.get_json()
        required_fields = ['email', 'password']

        # Check required fields
        for field in required_fields:
            # Check if exist
            if field not in data:
                return jsonify_response({'message': f"{field.capitalize()} is required"}, 400)
            # Check email format
            if field == 'email' and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', data['email']):
                return jsonify_response({'message': f"{data['email']} is invalid format"}, 400)
            # Check password contains uppercase, lowercase letters, and digits
            if field == 'password' and not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$', data['password']):
                return jsonify_response({'message': 'Password must contains uppercase, lowercase letters, and digits'}, 400)

        return "Blablablablabla", 201