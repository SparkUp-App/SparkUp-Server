from .auth import auth_bp
from .profile import profile_bp
from .post import post_bp
from .comment import comment_bp
from .applicant import applicant_bp
from .user import user_bp
from .reference import reference_bp
from .chat import chat_bp

__all__ = [
    'auth_bp',
    'profile_bp',
    'post_bp',
    'comment_bp',
    'applicant_bp',
    'user_bp',
    'reference_bp',
    'chat_bp'
]