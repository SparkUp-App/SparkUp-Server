import os


class Config:
    SECRET_KEY = 'SparkUp_secret_key'
    SECURITY_JOIN_USER_ROLES = True
    SECURITY_PASSWORD_HASH = 'bcrypt'
    SECURITY_PASSWORD_SALT = 'SparkUp_SECURITY_PASSWORD_SALT'
    FLASK_CORS_ORIGINS = os.environ.get('FLASK_CORS_ORIGINS', "*")
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL').replace('postgres://', 'postgresql://')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 1800,
        'pool_timeout': 30,
        'pool_size': 20,
        'max_overflow': 10,
    }