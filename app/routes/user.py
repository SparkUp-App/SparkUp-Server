from datetime import datetime, timezone
from collections import OrderedDict

from flask import Blueprint, request, current_app
from flask_restx import Api, Resource, fields
from sqlalchemy import exists, select
from sqlalchemy.orm import joinedload

from app.utils import jsonify_response, to_datetime, to_iso8601
from app.extensions import db
from app.models import PostBookmark, PostApplicant, User, Post

user_bp = Blueprint('user_bp', __name__)
user_api = Api(
    user_bp,
    version='1.0',
    title='User API',
    description='User API',
    doc='/docs',
)
user_ns = user_api.namespace('', description='User information')


DynamicLoadModel = user_ns.model(
    'DynamicLoadModel',
    {
        'page': fields.Integer(description='Page number of the results, defaults to 1', default=1),
        'per_page': fields.Integer(description='Number of posts per page, defaults to 20', default=20),
    }
)


@user_ns.route('/bookmarks/<int:user_id>')
class UserBookmarks(Resource):
    @user_ns.expect(DynamicLoadModel)
    @user_ns.response(200, 'Success')
    @user_ns.response(400, 'Bad Request')
    @user_ns.response(404, 'User Not Found')
    def post(self, user_id):
        data = request.get_json()
        page = data.get('page', 1)
        per_page = data.get('per_page', 20)

        try:
            if not db.session.execute(select(exists().where(User.id == user_id))).scalar():
                current_app.logger.error(f'User not found: {user_id}')
                return jsonify_response({'error': 'User not found'}, 404)

            bookmarks = PostBookmark.query \
                .options(joinedload(PostBookmark.post)) \
                .filter_by(user_id=user_id)

            pagination = bookmarks.paginate(page=page, per_page=per_page, error_out=False)
            posts = [
                OrderedDict([('id', bookmark.post.id),
                             ('nickname', bookmark.post.user.profile.nickname),
                             ('type', bookmark.post.type),
                             ('title', bookmark.post.title),
                             ('event_start_date', to_iso8601(bookmark.post.event_start_date)),
                             ('event_end_date', to_iso8601(bookmark.post.event_end_date)),
                             ('number_of_people_required', bookmark.post.number_of_people_required),
                             ('likes', len(bookmark.post.likes)),
                             ('liked', any(like.user_id == user_id for like in bookmark.post.likes)),
                             ('bookmarks', len(bookmark.post.bookmarks)),
                             ('bookmarked', any(bookmark.user_id == user_id for bookmark in bookmark.post.bookmarks)),
                             ('comments', len(bookmark.post.comments)),
                             ('applicants', len(bookmark.post.applicants))])
                for bookmark in pagination.items
            ]

            return jsonify_response({
                'posts': posts,
                'page': pagination.page,
                'pages': pagination.pages,
                'per_page': pagination.per_page
            }, 200)

        except Exception as e:
            current_app.logger.error(e)
            return jsonify_response({'error': str(e)}, 500)


@user_ns.route('/applied/<int:user_id>')
class UserApplied(Resource):
    @user_ns.expect(DynamicLoadModel)
    @user_ns.response(200, 'Success')
    @user_ns.response(400, 'Bad Request')
    @user_ns.response(404, 'User Not Found')
    def post(self, user_id):
        data = request.get_json()
        page = data.get('page', 1)
        per_page = data.get('per_page', 20)

        try:
            if not db.session.execute(select(exists().where(User.id == user_id))).scalar():
                current_app.logger.error(f'User not found: {user_id}')
                return jsonify_response({'error': 'User not found'}, 404)

            applicants = PostApplicant.query \
                .join(PostApplicant.post) \
                .options(joinedload(PostApplicant.post)) \
                .filter(PostApplicant.user_id == user_id,
                        Post.event_end_date < datetime.now(timezone.utc))

            pagination = applicants.paginate(page=page, per_page=per_page, error_out=False)
            posts = [
                OrderedDict([('id', applicant.post.id),
                             ('nickname', applicant.post.user.profile.nickname),
                             ('type', applicant.post.type),
                             ('title', applicant.post.title),
                             ('event_start_date', to_iso8601(applicant.post.event_start_date)),
                             ('event_end_date', to_iso8601(applicant.post.event_end_date)),
                             ('number_of_people_required', applicant.post.number_of_people_required),
                             ('likes', len(applicant.post.likes)),
                             ('liked', any(like.user_id == user_id for like in applicant.post.likes)),
                             ('bookmarks', len(applicant.post.bookmarks)),
                             ('bookmarked', any(bookmark.user_id == user_id for bookmark in applicant.post.bookmarks)),
                             ('comments', len(applicant.post.comments)),
                             ('applicants', len(applicant.post.applicants)),
                             ('review_status', applicant.review_status)])
                for applicant in pagination.items
            ]

            return jsonify_response({
                'posts': posts,
                'page': pagination.page,
                'pages': pagination.pages,
                'per_page': pagination.per_page
            }, 200)

        except Exception as e:
            current_app.logger.error(e)
            return jsonify_response({'error': str(e)}, 500)