from flask import Blueprint, current_app, request
from flask_restx import Api, Resource, fields
from sqlalchemy import case, exists, select

from app.utils import jsonify_response, to_iso8601
from app.extensions import db
from app.models import Post, User, DictItem, PostApplicant, Profile

applicant_bp = Blueprint('applicant_bp', __name__)
applicant_api = Api(
    applicant_bp,
    version='1.0',
    title='Applicant API',
    description='API for applicants',
    doc='/docs',
)
applicant_ns = applicant_api.namespace('', description='Operations related to applicants')


@applicant_ns.route('/list/<int:post_id>')
class ListApplicants(Resource):
    @applicant_ns.response(200, 'Success')
    @applicant_ns.response(400, 'Bad Request')
    @applicant_ns.response(404, 'Post not found')
    def get(self, post_id):
        if not db.session.execute(select(exists().where(Post.id == post_id))).scalar():
            return jsonify_response({'error': 'Post not found'}, 404)

        applicants = PostApplicant.query.filter_by(post_id=post_id, review_status=0).all()
        applicants_info = []
        for applicant in applicants:
            profile = Profile.query.get(applicant.user_id)
            applicants_info.append({
                'user_id': applicant.user_id,
                'nickname': profile.nickname if profile is not None else 'Anonymous',
                'applied_time': to_iso8601(applicant.applied_time),
                'attributes': applicant.attributes
            })

        return jsonify_response({'applicants': applicants_info}, 200)


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
        if db.session.execute(select(exists().where(PostApplicant.user_id == user_id,
                                             PostApplicant.post_id == post_id))).scalar():
            return jsonify_response({'error': 'Already apply this post', }, 400)

        # Check User
        if not db.session.execute(select(exists().where(User.id == user_id))).scalar():
            return jsonify_response({'error': 'User not found', }, 404)

        # Check Post
        post = Post.query.get(post_id)
        if post is None:
            return jsonify_response({'error': 'Post not found',}, 404)

        applicant = PostApplicant(user_id=user_id, post_id=post_id)
        if 'attributes' in data and data['attributes'] is not None and data['attributes'] != {}:
            applicant.attributes = data['attributes']

        try:
            post.manual_update()
            db.session.add(applicant)
            db.session.commit()
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