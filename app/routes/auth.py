from flask import Blueprint
from flask_restx import Api, Namespace

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