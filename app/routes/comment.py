from flask import Blueprint, current_app, request
from flask_restx import Api, Resource, fields
from sqlalchemy import exists, select

from app.utils import jsonify_response
from app.extensions import db
from app.models import User, Post, PostComment, PostCommentLike

comment_bp = Blueprint('comment_bp', __name__)
comment_api = Api(
    comment_bp,
    version='1.0',
    title='Comment API',
    description='API for comments',
    doc='/docs',
)
comment_ns = comment_api.namespace('', description='Operations related to comments')

list_comment_model = comment_api.model(
    'ListComment',
    {
        'user_id': fields.Integer(required=True, description='User id'),
        'post_id': fields.Integer(required=True, description='Post ID'),
        'page': fields.Integer(description='Page number', default=1),
        'per_page': fields.Integer(description='Number of comments per page', default=20),
    }
)


@comment_ns.route('/list')
class ListComment(Resource):
    @comment_ns.expect(list_comment_model)
    @comment_ns.response(200, 'Success')
    @comment_ns.response(400, 'Bad Request')
    @comment_ns.response(404, 'Post not found')
    def post(self):
        data = request.get_json()

        required_fields = ['user_id', 'post_id']
        for field in required_fields:
            if field not in data:
                return jsonify_response({'error': f'Missing required field {field}'}, 400)

        user_id = data['user_id']
        post_id = data['post_id']
        page = data['page'] if 'page' in data else 1
        per_page = data['per_page'] if 'per_page' in data else 20

        try:
            if not db.session.scalar(select(exists().where(Post.id == post_id))):
                return jsonify_response({'error': 'Post not found'}, 404)

            comments = PostComment.query.filter_by(post_id=post_id).paginate(page=page,
                                                                             per_page=per_page,
                                                                             error_out=False).items
            return jsonify_response({
                'comments': [comment.serialize(user_id=user_id) for comment in comments],
            }, 200)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify_response({'error': str(e)}, 400)


comment_model = comment_api.model(
    'Comment',
    {
        'user_id': fields.Integer(required=True, description='User id'),
        'post_id': fields.Integer(required=True, description='Post id'),
        'content': fields.String(required=True, description='Content'),
    }
)


@comment_ns.route('/create')
class CreateComment(Resource):
    @comment_ns.expect(comment_model)
    @comment_ns.response(200, 'Comment successfully created.')
    @comment_ns.response(400, 'Bad request.')
    @comment_ns.response(404, 'User or Post does not exist.')
    def post(self):
        data = request.get_json()

        require_fields = ['user_id', 'post_id', 'content']
        for field in require_fields:
            if field not in data:
                current_app.logger.error(f"Missing required field: {field}")
                return jsonify_response({'error': f"Missing required field: {field}"}, 400)

        user_id = data['user_id']
        post_id = data['post_id']
        content = data['content']

        try:
            if not db.session.scalar(select(exists().where(User.id == user_id))):
                return jsonify_response({'error': 'User does not exist'}, 404)

            post = Post.query.options(db.joinedload(Post.comments)).get(post_id)
            if not post:
                return jsonify_response({'error': 'Post does not exist'}, 404)

            floor = PostComment.query.filter_by(user_id=user_id, post_id=post_id).count() + 1
            comment = PostComment(user_id=user_id, post_id=post_id, content=content, floor=floor)
            post.manual_update()
            db.session.add(comment)
            db.session.commit()
            return jsonify_response({
                'message': 'Comment created successful',
                'comment': comment.serialize(user_id=user_id)
            }, 200)
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify_response({'error': str(e)}, 500)


comment_and_user_model = comment_api.model(
    'CommentAndUser',
    {
        'user_id': fields.Integer(required=True, description='User ID'),
        'comment_id': fields.Integer(required=True, description='Comment ID'),
    }
)


@comment_ns.route('/delete')
class DeleteComment(Resource):
    @comment_ns.expect(comment_and_user_model)
    @comment_ns.response(200, 'Comment successfully deleted.')
    @comment_ns.response(400, 'Bad request.')
    @comment_ns.response(404, 'Comment does not exist.')
    def post(self):
        data = request.get_json()

        require_fields = ['user_id', 'comment_id']
        for field in require_fields:
            if field not in data:
                current_app.logger.error(f"Missing required field: {field}")
                return jsonify_response({'error': f"Missing required field: {field}"}, 400)

        user_id = data['user_id']
        comment_id = data['comment_id']

        try:
            comment = PostComment.query.get(comment_id)
            if not comment:
                return jsonify_response({'error': 'Comment does not exist'}, 404)

            if comment.user_id != user_id:
                return jsonify_response({'error': 'User does not match'}, 400)

            comment.content = "The author has deleted this comment."
            comment.deleted = True

            db.session.commit()
            return jsonify_response({'message': 'Comment deleted successful'}, 200)
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify_response({'error': str(e)}, 500)


comment_and_user_and_retrieve_model = comment_api.model(
    'CommentAndUserAndRetrieve',
    {
        'user_id': fields.Integer(required=True, description='User ID'),
        'comment_id': fields.Integer(required=True, description='Comment ID'),
        'retrieve': fields.Boolean(required=True, description='Whether to retrieve the like'),
    }
)


@comment_ns.route('/like')
class LikeComment(Resource):
    @comment_ns.expect(comment_and_user_and_retrieve_model)
    @comment_ns.response(200, 'Successfully liked comment.')
    @comment_ns.response(400, 'Bad request.')
    @comment_ns.response(404, 'Comment does not exist.')
    def post(self):
        data = request.get_json()

        require_fields = ['user_id', 'comment_id', 'retrieve']
        for field in require_fields:
            if field not in data:
                current_app.logger.error(f"Missing required field: {field}")
                return jsonify_response({'error': f"Missing required field: {field}"}, 400)

        user_id = data['user_id']
        comment_id = data['comment_id']
        retrieve = data['retrieve']

        try:
            if retrieve:
                like = PostCommentLike.query.get((user_id, comment_id))
                if not like:
                    return jsonify_response({'error': 'Comment does not exist'}, 404)
                db.session.delete(like)
            else:
                like = PostCommentLike(user_id=user_id, comment_id=comment_id)
                db.session.add(like)

            db.session.commit()
            return jsonify_response({'message': 'Comment liked successfully'}, 200)

        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify_response({'error': str(e)}, 500)