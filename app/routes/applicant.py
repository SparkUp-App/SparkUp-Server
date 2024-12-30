from flask import Blueprint, current_app, request
from flask_restx import Api, Resource, fields
from sqlalchemy import exists, select
from sqlalchemy.orm import joinedload

from app.utils import jsonify_response, to_iso8601
from app.extensions import db, socketio
from app.models import Post, User, DictItem, PostApplicant, Profile, ChatRoomUser

applicant_bp = Blueprint('applicant_bp', __name__)
applicant_api = Api(
    applicant_bp,
    version='1.0',
    title='Applicant API',
    description='API for applicants',
    doc='/docs',
)
applicant_ns = applicant_api.namespace('', description='Operations related to applicants')


@applicant_ns.route('/list/<int:user_id>')
class ListApplicants(Resource):
    @applicant_ns.response(200, 'Success')
    @applicant_ns.response(400, 'Bad Request')
    @applicant_ns.response(404, 'User not found')
    def get(self, user_id):
        # Verify user exists
        if not db.session.scalar(select(exists().where(User.id == user_id))):
            return jsonify_response({'error': 'User not found'}, 404)

        try:
            results = db.session.query(
                PostApplicant, Post, Profile, User
            ).options(
                joinedload(PostApplicant.post),
                joinedload(PostApplicant.user)
            ).join(
                Post, PostApplicant.post_id == Post.id
            ).join(
                Profile, PostApplicant.user_id == Profile.id
            ).join(
                User, PostApplicant.user_id == User.id
            ).filter(
                Post.user_id == user_id,
                PostApplicant.review_status == 0
            ).order_by(
                Post.event_start_date.desc(),
                PostApplicant.applied_time.desc()
            ).all()

            # Calculate participation count and level for each user
            grouped_applicants = {}
            for applicant, post, profile, user in results:
                if post.id not in grouped_applicants:
                    grouped_applicants[post.id] = {
                        'post_id': post.id,
                        'post_title': post.title,
                        'post_type': post.type,
                        'number_of_people_required': post.number_of_people_required,
                        'applicants': []
                    }

                # Calculate participation count and level
                participated = user.chat_rooms.count() - user.posts.count()
                level = 0
                if 11 <= participated <= 20:
                    level = 1
                elif 21 <= participated <= 30:
                    level = 2
                elif 31 <= participated <= 40:
                    level = 3
                elif participated >= 41:
                    level = 4

                grouped_applicants[post.id]['applicants'].append({
                    'user_id': applicant.user_id,
                    'nickname': profile.nickname if profile is not None else 'Anonymous',
                    'bio': profile.bio if profile is not None and profile.bio is not None else '',
                    'applied_time': to_iso8601(applicant.applied_time),
                    'attributes': applicant.attributes,
                    'level': level,
                    'participated': participated
                })

            posts_with_applicants = list(grouped_applicants.values())
            return jsonify_response({'posts': posts_with_applicants}, 200)

        except Exception as e:
            current_app.logger.error(f"Error listing applicants: {str(e)}")
            return jsonify_response({'error': str(e)}, 500)


create_applicant_model = applicant_api.model(
    'CreateApplicantModel',
    {
        'user_id': fields.Integer(required=True, description='User ID'),
        'post_id': fields.Integer(required=True, description='Post ID'),
        'attributes': DictItem("Dictionary(String : Any)"),
    }
)


@applicant_ns.route('/create')
class CreateApplicant(Resource):
    @applicant_ns.expect(create_applicant_model)
    @applicant_ns.response(200, 'Success')
    @applicant_ns.response(400, 'Bad Request')
    @applicant_ns.response(404, 'Post or User not found')
    def post(self):
        data = request.get_json()

        required_fields = ['user_id', 'post_id']
        for field in required_fields:
            if field not in data:
                current_app.logger.error(f"Missing required field: {field}")
                return jsonify_response({'error': f"Missing required field: {field}"}, 400)

        user_id = data['user_id']
        post_id = data['post_id']

        # Check if already apply:
        if db.session.scalar(select(exists().where(PostApplicant.user_id == user_id,
                                             PostApplicant.post_id == post_id))):
            return jsonify_response({'error': 'Already apply this post', }, 400)

        # Check User
        user_profile = Profile.query.get(user_id)
        if not user_profile:
            return jsonify_response({'error': 'User not found', }, 404)

        # Check Post
        post = Post.query.get(post_id)
        if post is None:
            return jsonify_response({'error': 'Post not found',}, 404)

        if post.user_id == user_id:
            return jsonify_response({'error': "Can't applied to it's own post. "}, 400)

        applicant = PostApplicant(user_id=user_id, post_id=post_id)
        if 'attributes' in data and data['attributes'] is not None and data['attributes'] != {}:
            applicant.attributes = data['attributes']

        try:
            post.manual_update()
            db.session.add(applicant)
            db.session.commit()

            host_room = f"user_{post.user_id}"
            socketio.emit('new_application', {
                'post_id': data['post_id'],
                'post_title': post.title,
                'user_nickname': user_profile.nickname,
                'message': f"New application for '{post.title}' from {user_profile.nickname}!"
            }, to=host_room)

            return jsonify_response({'message': "Application create successfully"}, 200)

        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify_response({'error': str(e)}, 500)


post_and_user_model = applicant_ns.model(
    'PostAndUser',
    {
        'user_id': fields.Integer(required=True, description='User ID'),
        'post_id': fields.Integer(required=True, description='Post ID'),
    }
)


@applicant_ns.route('/retrieve')
class RetrieveApplicant(Resource):
    @applicant_ns.expect(post_and_user_model)
    @applicant_ns.response(200, 'Success')
    @applicant_ns.response(400, 'Bad Request')
    @applicant_ns.response(404, 'Applicant not found')
    def delete(self):
        data = request.get_json()

        required_fields = ['user_id', 'post_id']
        for field in required_fields:
            if field not in data:
                current_app.logger.error(f"Missing required field: {field}")
                return jsonify_response({'error': f"Missing required field: {field}"}, 400)

        user_id = data['user_id']
        post_id = data['post_id']

        applicant = PostApplicant.query.get((user_id, post_id))

        if not applicant:
            return jsonify_response({'error': 'Applicant not found',}, 404)

        try:
            applicant.post.manual_update()
            db.session.delete(applicant)
            db.session.commit()
            return jsonify_response({'message': "Applicant deleted successfully"}, 200)
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify_response({'error': str(e)}, 500)


approve_model = applicant_ns.model(
    'ApproveModel',
    {
        'user_id': fields.Integer(required=True, description='User ID'),
        'post_id': fields.Integer(required=True, description='Post ID'),
        'approve': fields.Boolean(required=True, description='True: Approve, False: Reject')
    }
)


@applicant_ns.route('/review')
class ReviewApplicant(Resource):
    @applicant_ns.expect(approve_model)
    @applicant_ns.response(200, 'Success')
    @applicant_ns.response(400, 'Bad Request')
    @applicant_ns.response(404, 'Applicant not found')
    def post(self):
        data = request.get_json()
        required_fields = ['user_id', 'post_id', 'approve']
        for field in required_fields:
            if field not in data or data[field] is None:
                current_app.logger.error(f"Missing required field: {field}")
                return jsonify_response({'error': f"Missing required field: {field}"}, 400)

        applicant = PostApplicant.query \
            .options(joinedload(PostApplicant.post)) \
            .options(joinedload(PostApplicant.post).joinedload(Post.user).joinedload(User.profile)) \
            .filter_by(user_id=data['user_id'], post_id=data['post_id']) \
            .first()

        if not applicant:
            current_app.logger.error(f"Applicant not found: {data['post_id']}")
            return jsonify_response({'error': 'Applicant not found'}, 404)

        if applicant.review_status != 0:
            current_app.logger.error(f"Applicant already reviewed: {applicant.review_status}")
            return jsonify_response({'error': f'Applicant already reviewed: {applicant.review_status}'}, 400)

        try:
            if data['approve']:
                if applicant.post.number_of_people_required == 0:
                    applicant.review_status = 1
                    current_app.logger.error('No people required')
                    return jsonify_response({'error': 'No people required'}, 400)

                applicant.post.number_of_people_required -= 1
                applicant.post.manual_update()
                applicant.review_status = 2

                # Create chat room user
                chat_room_user = ChatRoomUser(post_id=data['post_id'], user_id=data['user_id'])
                db.session.add(chat_room_user)

                # Emit socket event to the approved user
                user_room = f"user_{data['user_id']}"
                socketio.emit('application_approved', {
                    'post_id': data['post_id'],
                    'post_title': applicant.post.title,
                    'host_nickname': applicant.post.user.profile.nickname,
                    'message': f"Your application for '{applicant.post.title}' has been approved by {applicant.post.user.profile.nickname}! You can now join the chat room."
                }, to=user_room)
            else:
                applicant.review_status = 1

                # Emit socket event for rejection
                user_room = f"user_{data['user_id']}"
                socketio.emit('application_rejected', {
                    'post_id': data['post_id'],
                    'post_title': applicant.post.title,
                    'host_nickname': applicant.post.user.profile.nickname,
                    'message': f"Your application for '{applicant.post.title}' has been rejected by {applicant.post.user.profile.nickname}."
                }, to=user_room)

            db.session.commit()
            return jsonify_response({'message': "Applicant review successfully"}, 200)

        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify_response({'error': str(e)}, 500)
