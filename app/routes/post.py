from datetime import datetime

from flask import Blueprint, current_app, jsonify, request
from flask_migrate import current
from flask_restx import Api, Resource, fields
from sqlalchemy import case

from app.utils import jsonify_response
from app.extensions import db
from app.models import Post, User, Profile

post_bp = Blueprint('post_bp', __name__)
post_api = Api(
    post_bp,
    version='1.0',
    title='Posts Management API',
    description='A service to manage posts',
    doc='/docs',
)
post_ns = post_api.namespace('', description='Operations related to posts')


class DictItem(fields.Raw):
    def output(self, key, obj, *args, **kwargs):
        try:
            dct = getattr(obj, self.attribute)
        except AttributeError:
            return {}
        return dct or {}


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
        'attributes': DictItem("Dictionary(String : List(String))"),
    }
)


@post_ns.route('/create')
class PostCreate(Resource):
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

        user = db.session.query(User).get(data['user_id'])
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
        'user_id': fields.Integer(description='User ID'),
        'sort': fields.Integer(description='Sort, 0: For You, 1: All. Default = 1: All'),
        'type': fields.String(description='Type of the post'),
        'keyword': fields.String(description='Keyword for search'),
        'page': fields.Integer(description='Page number of the results, defaults to 1'),
        'per_page': fields.Integer(description='Number of posts per page, defaults to 20'),
    }
)


@post_ns.route('/list/<int:user_id>')
class PostList(Resource):
    @post_ns.expect(post_list_query_model)
    @post_ns.response(201, 'Post successfully listed')
    @post_ns.response(400, 'Bad Request')
    def post(self, user_id):
        data = request.get_json()
        query = Post.query

        current_app.logger.info(f"Getting posts by user: {user_id} with request: {data}")

        # Filter and Sort
        if 'user_id' in data and data['user_id'] is not None:
            query = query.filter(Post.user_id == data['user_id'])
        if 'type' in data and data['type'] is not None:
            query = query.filter(Post.type == data['type'])
        if 'keyword' in data and data['keyword'] is not None:
            query = query.filter(Post.title.ilike(f'%{data["keyword"]}%'))
        if data.get('sort', 1) == 0:

            # Recommendation System
            if 'type' not in data or data['type'] is None:
                profile = Profile.query.get(user_id)
                if profile and profile.interest_types != []:
                    query = query.order_by(
                        case(
                            (Post.type.in_(profile.interest_types), 0),
                            else_=1
                        )
                    )
            query = query.order_by(Post.post_last_updated_date.desc())
        else:
            query = query.order_by(Post.post_created_date.desc())

        current_app.logger.info(f"Query: {str(query)}")

        # Paginate
        if 'page' not in data or data['page'] is None:
            data['page'] = 1
        if 'per_page' not in data or data['per_page'] is None:
            data['per_page'] = 20
        pagination = query.paginate(page=data['page'], per_page=data['per_page'], error_out=False)
        posts = [post.serialize(simple=True) for post in pagination.items]

        return jsonify_response({
            'posts': posts,
            'page': pagination.page,
            'pages': pagination.pages,
            'per_page': pagination.per_page
        }, 201)




@post_ns.route('/view/<int:post_id>')
class PostView(Resource):
    @post_ns.param('post_id', 'The ID of the post')
    @post_ns.response(404, 'Post not found')
    @post_ns.response(200, 'Success')
    def get(self, post_id):
        print("234")
        current_app.logger.info(f"Viewing post {post_id}")
        post = Post.query.get_or_404(post_id)

        return jsonify_response(post.serialize(), 200)


