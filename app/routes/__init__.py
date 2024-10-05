from .auth import auth_bp
from .profile import profile_bp
from .post import post_bp
from .comment import comment_bp

__all__ = [
    'auth_bp',
    'profile_bp',
    'post_bp',
    'comment_bp'
]