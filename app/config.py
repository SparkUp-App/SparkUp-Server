import os


class Config:
    SECRET_KEY = 'SparkUp_secret_key'
    SECURITY_JOIN_USER_ROLES = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL').replace('postgres://', 'postgresql://')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

