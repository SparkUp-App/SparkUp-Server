import os


class Config:
    SECRET_KEY = 'SparkUp_secret_key'
    SECURITY_JOIN_USER_ROLES = True
    SECURITY_PASSWORD_HASH = 'bcrypt'
    SECURITY_PASSWORD_SALT = 'SparkUp_SECURITY_PASSWORD_SALT'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL').replace('postgres://', 'postgresql://')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

