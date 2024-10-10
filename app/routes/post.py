from datetime import datetime

from dns.name import empty
from flask import Blueprint, current_app, request
from flask_restx import Api, Resource, fields
from sqlalchemy import case, exists

from app.utils import jsonify_response
from app.extensions import db
from app.models import Post, PostLike, User, Profile, DictItem, PostBookmark, PostApplicant

post_bp = Blueprint('post_bp', __name__)
post_api = Api(
    post_bp,
    version='1.0',
    title='Posts Management API',
    description='A service to manage posts',
    doc='/docs',
)
post_ns = post_api.namespace('', description='Operations related to posts')

post_model = post_api.model(
    'BasePost',
    {
        'user_id': fields.Integer(required=True, description='User ID'),
        'type': fields.String(required=True, description='Type of the post'),
        'title': fields.String(required=True, description='Title'),
        'content': fields.String(required=True, description='Content'),
        'event_start_date': fields.Date(required=True, description='Event start date'),
        'event_end_date': fields.Date(required=True, description='Event end date'),
        'number_of_people_required': fields.Integer(required=True, description='Number of people'),
        'location': fields.String(required=True, description='Location'),
        'skills': fields.List(fields.String, description='Skills'),
        'personalities': fields.List(fields.String, description='Personalities'),
        'languages': fields.List(fields.String, description='Languages'),
        'attributes': DictItem("Dictionary(String : Any)"),
    }
)


@post_ns.route('/create')
class CreatePost(Resource):
    @post_ns.expect(post_model)
    @post_ns.response(201, 'Post successfully created')
    @post_ns.response(400, 'Bad Request')
    @post_ns.response(403, 'User profile must be completed first')
    @post_ns.response(404, 'User not found')
    def post(self):
        data = request.get_json()
        current_app.logger.info(f"Creating post {data}")

        required_fields = ['user_id', 'type', 'title', 'content', 'event_start_date', 'event_end_date', 'number_of_people_required', 'location']
        for field in required_fields:
            if field not in data:
                current_app.logger.error(f"Missing required field: {field}")
                return jsonify_response({'error': f"Missing required field: {field}"}, 400)

        user = User.query.get(data['user_id'])
        if not user:
            current_app.logger.error(f"User {data['user_id']} not found")
            return jsonify_response({'error': 'User not found'}, 404)

        if not user.profile:
            current_app.logger.error('User profile must be completed first')
            return jsonify_response({'error': 'User profile must be completed first'}, 403)

        try:
            event_start_date = datetime.strptime(data['event_start_date'], '%Y-%m-%d').date()
            event_end_date = datetime.strptime(data['event_end_date'], '%Y-%m-%d').date()
        except ValueError as e:
            current_app.logger.error(e)
            post_ns.abort(400, f'Invalid date format, use YYYY-MM-DD format')

        post = Post()
        post.user_id = data['user_id']
        post.type = data['type']
        post.title = data['title']
        post.content = data['content']
        post.event_start_date = event_start_date
        post.event_end_date = event_end_date
        post.number_of_people_required = data['number_of_people_required']
        post.location = data['location']
        post.skills = data.get('skills', [])
        post.personalities = data.get('personalities', [])
        post.languages = data.get('languages', [])
        post.attributes = data.get('attributes', {})

        db.session.add(post)
        db.session.commit()

        return jsonify_response({
            'post_id': post.id,
            'message': f"Post {post.id} created successful"},
            201
        )


post_list_query_model = post_api.model(
    'PostListQuery',
    {
        'user_id': fields.Integer(description='Filter User ID'),
        'sort': fields.Integer(description='Sort, 0: For You, 1: All. Default = 1: All', default=1),
        'type': fields.List(fields.String(), description='Filter types of the post'),
        'keyword': fields.String(description='Keyword for search'),
        'page': fields.Integer(description='Page number of the results, defaults to 1', default=1),
        'per_page': fields.Integer(description='Number of posts per page, defaults to 20', default=20),
    }
)


@post_ns.route('/list/<int:user_id>')
class ListPost(Resource):
    @post_ns.expect(post_list_query_model)
    @post_ns.response(201, 'Post successfully listed')
    @post_ns.response(400, 'Bad Request')
    def post(self, user_id):
        data = request.get_json()
        post_query = Post.query

        current_app.logger.info(f"Getting posts by user: {user_id} with request: {data}")

        # Filter and Sort
        if 'user_id' in data and data['user_id'] is not None:
            post_query = post_query.filter_by(user_id=data['user_id'])
        if 'type' in data and data['type'] is not None and data['type']:
            post_query = post_query.filter(Post.type.in_(data['type']))
        if 'keyword' in data and data['keyword'] is not None and data['keyword'] != "":
            post_query = post_query.filter(Post.title.ilike(f'%{data["keyword"]}%'))
        if data.get('sort', 1) == 0:
            # Recommendation System
            if 'type' not in data or data['type'] is None:
                profile = Profile.query.get(user_id)
                if profile and profile.interest_types != []:
                    post_query = post_query.order_by(
                        case(
                            (Post.type.in_(profile.interest_types), 0),
                            else_=1
                        )
                    )
            post_query = post_query.order_by(Post.post_last_updated_date.desc())
        else:
            post_query = post_query.order_by(Post.post_created_date.desc())

        current_app.logger.info(f"Getting posts with SQL query: {str(post_query)}")

        # Paginate
        if 'page' not in data or data['page'] is None:
            data['page'] = 1
        if 'per_page' not in data or data['per_page'] is None:
            data['per_page'] = 20
        pagination = post_query.paginate(page=data['page'], per_page=data['per_page'], error_out=False)
        posts = [post.serialize(user_id=user_id, simple=True) for post in pagination.items]

        return jsonify_response({
            'posts': posts,
            'page': pagination.page,
            'pages': pagination.pages,
            'per_page': pagination.per_page
        }, 201)


post_and_user_model = post_api.model(
    'PostAndUser',
    {
        'user_id': fields.Integer(required=True, description='User ID'),
        'post_id': fields.Integer(required=True, description='Post ID'),
    }
)


@post_ns.route('/view')
class ViewPost(Resource):
    @post_ns.expect(post_and_user_model)
    @post_ns.response(200, 'Success')
    @post_ns.response(400, 'Bad Request')
    @post_ns.response(404, 'Post not found')
    def post(self):
        data = request.get_json()

        required_fields = ['user_id', 'post_id']
        for field in required_fields:
            if field not in data:
                current_app.logger.error(f"Missing required field: {field}")
                return jsonify_response({'error': f"Missing required field: {field}"}, 400)

        post_id = data['post_id']
        user_id = data['user_id']

        current_app.logger.info(f"Viewing post: {post_id} by user: {user_id}")
        post = Post.query.get(post_id)

        return jsonify_response(post.serialize(user_id=user_id, simple=False), 200)


post_and_user_and_retrieve_model = post_api.model(
    'PostAndUserAndRetrieve',
    {
        'user_id': fields.Integer(required=True, description='User ID'),
        'post_id': fields.Integer(required=True, description='Post ID'),
        'retrieve': fields.Boolean(description="Whether to retrieve", default=False),
    }
)


@post_ns.route('/like')
class LikePost(Resource):
    @post_ns.expect(post_and_user_and_retrieve_model)
    @post_ns.response(200, 'Success')
    @post_ns.response(400, 'Bad Request')
    @post_ns.response(404, 'Post or User or Like not found')
    def post(self):
        data = request.get_json()

        required_fields = ['user_id', 'post_id']
        for field in required_fields:
            if field not in data:
                current_app.logger.error(f"Missing required field: {field}")
                return jsonify_response({'error': f"Missing required field: {field}"}, 400)

        post_id = data['post_id']
        user_id = data['user_id']
        retrieve = 'retrieve' in data and data['retrieve'] is True

        try:
            if retrieve:
                like = PostLike.query.get((user_id, post_id))
                if not like:
                    return jsonify_response({'error': 'Like not found'}, 404)
                db.session.delete(like)

            else:
                # Check User
                if db.session.execute(exists().where(User.id == user_id)).scalar():
                    return jsonify_response({'error': 'User not found', }, 404)

                # Check if Post exists
                post = Post.query.get(post_id)
                if not post:
                    return jsonify_response({'error': 'Post not found'}, 404)

                # Check is Like exists
                if db.session.execute(exists().where(PostLike.user_id == user_id, PostLike.post_id == post_id)).scalar():
                    return jsonify_response({'error': 'Post already liked', }, 400)

                post.manual_update()
                db.session.add(PostLike(user_id=user_id, post_id=post_id))

            db.session.commit()
            return jsonify_response({'retrieved': retrieve}, 200)

        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify_response({'error': str(e)}, 500)


@post_ns.route('/bookmark')
class BookmarkPost(Resource):
    @post_ns.expect(post_and_user_and_retrieve_model)
    @post_ns.response(200, 'Success')
    @post_ns.response(400, 'Bad Request')
    @post_ns.response(404, 'Post or User or Bookmark not found')
    def post(self):
        data = request.get_json()

        required_fields = ['user_id', 'post_id']
        for field in required_fields:
            if field not in data:
                current_app.logger.error(f"Missing required field: {field}")
                return jsonify_response({'error': f"Missing required field: {field}"}, 400)

        user_id = data['user_id']
        post_id = data['post_id']
        retrieve = 'retrieve' in data and data['retrieve'] is True

        try:
            if retrieve:
                bookmark = PostBookmark.query.get((user_id, post_id))
                if not bookmark:
                    return jsonify_response({'error': 'Bookmark not found'}, 404)
                db.session.delete(bookmark)

            else:
                if db.session.execute(exists().where(User.id == user_id)).scalar():
                    return jsonify_response({'error': 'User not found', }, 404)

                post = Post.query.get(post_id)
                if not post:
                    return jsonify_response({'error': 'Post not found', }, 404)

                post.manual_update()
                db.session.add(PostBookmark(user_id=user_id, post_id=post_id))

            db.session.commit()
            return jsonify_response({'retrieved': retrieve}, 200)

        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify_response({'error': str(e)}, 500)


post_applicant_model = post_api.model(
    'PostApplicantModel',
    {
        'user_id': fields.Integer(required=True, description='User ID'),
        'post_id': fields.Integer(required=True, description='Post ID'),
        'content': fields.String(required=True, description='Content'),
    }
)


@post_ns.route('/create_applicant')
class CreateApplicant(Resource):
    @post_ns.expect(post_applicant_model)
    @post_ns.response(200, 'Success')
    @post_ns.response(400, 'Bad Request')
    @post_ns.response(404, 'Post or User not found')
    def post(self):
        data = request.get_json()

        required_fields = ['user_id', 'post_id', 'content']
        for field in required_fields:
            if field not in data:
                current_app.logger.error(f"Missing required field: {field}")
                return jsonify_response({'error': f"Missing required field: {field}"}, 400)

        user_id = data['user_id']
        post_id = data['post_id']
        content = data['content']

        # Check if already apply:
        if db.session.execute(exists().where(PostApplicant.user_id == user_id,
                                             PostApplicant.post_id == post_id)).scalar():
            return jsonify_response({'error': 'Already apply this post', }, 400)

        # Check User
        if db.session.execute(exists().where(User.id == user_id)).scalar():
            return jsonify_response({'error': 'User not found', }, 404)

        # Check Post
        post = Post.query.get(post_id)
        if post is None:
            return jsonify_response({'error': 'Post not found',}, 404)

        applicant = PostApplicant(user_id=user_id, post_id=post_id, content=content)

        try:
            post.manual_update()
            db.session.add(applicant)
            db.session.commit()
            return jsonify_response({'message': "Application submitted successfully"}, 200)

        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify_response({'error': str(e)}, 500)


@post_ns.route('/retrieve_applicant')
class RetrieveApplicant(Resource):
    @post_ns.expect(post_and_user_model)
    @post_ns.response(200, 'Success')
    @post_ns.response(400, 'Bad Request')
    @post_ns.response(404, 'Applicant not found')
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
