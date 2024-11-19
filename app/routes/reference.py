from datetime import datetime, timezone
from collections import OrderedDict

from flask import Blueprint, request, current_app
from flask_restx import Api, Resource, fields
from sqlalchemy import exists, select, and_, or_, func, distinct
from sqlalchemy.orm import joinedload, contains_eager, aliased

from app.utils import jsonify_response, to_iso8601
from app.extensions import db
from app.models import Post, PostApplicant, Reference, User, Profile, ChatRoomUser

reference_bp = Blueprint('reference_bp', __name__)
reference_api = Api(
    reference_bp,
    version='1.0',
    title='Reference API',
    description='Reference API',
    doc='/docs',
)
reference_ns = reference_api.namespace('', description='Reference namespace')

list_referenceable_model = reference_api.model(
    'ListReferenceableModel',
    {
        'page': fields.Integer(description='Page number of the results, defaults to 1', default=1),
        'per_page': fields.Integer(description='Number of items per page, defaults to 20', default=20),
    }
)


@reference_ns.route('/list_referenceable/<int:user_id>')
class ListReferenceable(Resource):
    @reference_ns.expect(list_referenceable_model)
    @reference_ns.response(200, 'Success')
    @reference_ns.response(400, 'Bad Request')
    @reference_ns.response(404, 'User not found')
    def post(self, user_id):
        data = request.get_json()
        page = data.get('page', 1)
        per_page = data.get('per_page', 20)

        # Verify user exists
        if not db.session.scalar(select(exists().where(User.id == user_id))):
            current_app.logger.error(f'User not found: {user_id}')
            return jsonify_response({'error': 'User not found'}, 404)

        try:
            # Create aliases for self-joins
            UserChatRoom = aliased(ChatRoomUser)
            OtherChatRoom = aliased(ChatRoomUser)

            # Build the main query
            query = db.session.query(
                Post,
                User,
                Profile,
                OtherChatRoom
            ).join(
                UserChatRoom,
                and_(
                    UserChatRoom.post_id == Post.id,
                    UserChatRoom.user_id == user_id
                )
            ).join(
                OtherChatRoom,
                and_(
                    OtherChatRoom.post_id == Post.id,
                    OtherChatRoom.user_id != user_id
                )
            ).join(
                User,
                User.id == OtherChatRoom.user_id
            ).join(
                Profile,
                Profile.id == User.id
            ).outerjoin(
                Reference,
                and_(
                    Reference.from_user_id == user_id,
                    Reference.to_user_id == OtherChatRoom.user_id,
                    Reference.post_id == Post.id
                )
            ).filter(
                Post.event_end_date < datetime.now(timezone.utc),
                Reference.from_user_id == None
            ).order_by(
                Post.event_end_date.desc(),
                Profile.nickname
            )

            # Get total count for pagination
            total_items = query.count()
            total_pages = (total_items + per_page - 1) // per_page

            # Apply pagination
            results = query.offset((page - 1) * per_page).limit(per_page).all()

            referenceable_users = [
                OrderedDict([
                    ('post_id', post.id),
                    ('post_title', post.title),
                    ('post_type', post.type),
                    ('event_start_date', to_iso8601(post.event_start_date)),
                    ('event_end_date', to_iso8601(post.event_end_date)),
                    ('location', post.location),
                    ('user_id', user.id),
                    ('nickname', profile.nickname),
                    ('role', 'Host' if user.id == post.user_id else 'Participant')
                ])
                for post, user, profile, chat_room_user in results
            ]

            return jsonify_response({
                'referenceable_users': referenceable_users,
                'page': page,
                'pages': total_pages,
                'per_page': per_page,
                'total_items': total_items
            }, 200)

        except Exception as e:
            current_app.logger.error(f"Error in list_referenceable: {str(e)}")
            return jsonify_response({'error': str(e)}, 500)


create_reference_model = reference_api.model(
    'CreateReference',
    {
        'from_user_id': fields.Integer(required=True, description='User ID giving the reference'),
        'to_user_id': fields.Integer(required=True, description='User ID receiving the reference'),
        'post_id': fields.Integer(required=True, description='Post ID for which the reference is being given'),
        'rating': fields.Integer(required=True, description='Rating (1-5)'),
        'content': fields.String(required=True, description='Reference content')
    }
)


@reference_ns.route('/list/<int:user_id>')
class ListReferences(Resource):
    @reference_ns.expect(list_referenceable_model)
    @reference_ns.response(200, 'Success')
    @reference_ns.response(400, 'Bad Request')
    @reference_ns.response(404, 'User not found')
    def post(self, user_id):
        data = request.get_json()
        page = data.get('page', 1)
        per_page = data.get('per_page', 20)

        # Verify user exists
        if not db.session.scalar(select(exists().where(User.id == user_id))):
            current_app.logger.error(f'User not found: {user_id}')
            return jsonify_response({'error': 'User not found'}, 404)

        try:
            # First get the reference counts per post
            reference_counts = db.session.query(
                Reference.post_id,
                func.count().label('ref_count')
            ).filter(
                Reference.to_user_id == user_id
            ).group_by(
                Reference.post_id
            ).subquery()

            # Then get posts ordered by event_end_date with their reference counts
            posts_with_counts = db.session.query(
                Post.id.label('post_id'),
                Post.event_end_date,
                reference_counts.c.ref_count,
                func.sum(reference_counts.c.ref_count).over(
                    order_by=Post.event_end_date.desc()
                ).label('cumulative_count')
            ).join(
                reference_counts,
                Post.id == reference_counts.c.post_id
            ).order_by(
                Post.event_end_date.desc()
            ).subquery()

            # Get post IDs for the current page
            post_ids_query = db.session.query(
                posts_with_counts.c.post_id
            ).filter(
                posts_with_counts.c.cumulative_count <= (page * per_page)
            )

            if page > 1:
                previous_total = db.session.query(
                    posts_with_counts.c.cumulative_count
                ).filter(
                    posts_with_counts.c.cumulative_count <= ((page - 1) * per_page)
                ).order_by(
                    posts_with_counts.c.cumulative_count.desc()
                ).first()

                if previous_total:
                    post_ids_query = post_ids_query.filter(
                        posts_with_counts.c.cumulative_count > previous_total[0]
                    )

            post_ids = [p[0] for p in post_ids_query.all()]

            # Get total references count
            total_references = db.session.query(
                func.count(Reference.post_id)
            ).filter(
                Reference.to_user_id == user_id
            ).scalar()

            # Get the overall average rating
            overall_avg_rating = db.session.query(
                func.avg(Reference.rating)
            ).filter(
                Reference.to_user_id == user_id
            ).scalar()
            overall_avg_rating = float(overall_avg_rating) if overall_avg_rating is not None else 0.0

            # Get event-specific average ratings
            event_ratings = db.session.query(
                Reference.post_id,
                func.avg(Reference.rating).label('avg_rating'),
                func.count(Reference.rating).label('rating_count')
            ).filter(
                Reference.to_user_id == user_id,
                Reference.post_id.in_(post_ids)
            ).group_by(
                Reference.post_id
            ).all()

            # Convert to dictionary for easy lookup
            event_ratings_dict = {
                er.post_id: {
                    'avg_rating': round(float(er.avg_rating), 2) if er.avg_rating is not None else 0.0,
                    'rating_count': int(er.rating_count)
                } for er in event_ratings
            }

            # Get all references and related data for the selected events
            query = db.session.query(
                Reference,
                User,
                Profile,
                Post
            ).join(
                User, Reference.from_user_id == User.id
            ).join(
                Profile, User.id == Profile.id
            ).join(
                Post, Reference.post_id == Post.id
            ).filter(
                Reference.to_user_id == user_id,
                Reference.post_id.in_(post_ids)
            ).order_by(
                Post.event_end_date.desc(),
                Reference.post_id
            )

            results = query.all()

            # Group results by event
            events_dict = {}
            for ref, user, profile, post in results:
                if post.id not in events_dict:
                    event_rating_info = event_ratings_dict.get(post.id, {'avg_rating': 0.0, 'rating_count': 0})
                    events_dict[post.id] = {
                        'event_info': {
                            'post_id': post.id,
                            'title': post.title,
                            'type': post.type,
                            'event_start_date': to_iso8601(post.event_start_date),
                            'event_end_date': to_iso8601(post.event_end_date),
                            'location': post.location,
                            'average_rating': event_rating_info['avg_rating'],
                            'rating_count': event_rating_info['rating_count']
                        },
                        'references': []
                    }

                events_dict[post.id]['references'].append({
                    'from_user_id': user.id,
                    'from_user_nickname': profile.nickname,
                    'rating': int(ref.rating),
                    'content': ref.content,
                    'is_host': user.id == post.user_id
                })

                if events_dict[post.id]['references'][-1]['is_host']:
                    events_dict[post.id]['references'][0], events_dict[post.id]['references'][-1] = events_dict[post.id]['references'][-1], events_dict[post.id]['references'][0]

            # Convert dictionary to list for response, maintaining post_ids order
            events_list = [
                {
                    'event': events_dict[post_id]['event_info'],
                    'references': events_dict[post_id]['references']
                }
                for post_id in post_ids if post_id in events_dict
            ]

            # Calculate total pages based on references count
            total_pages = (total_references + per_page - 1) // per_page

            return jsonify_response({
                'events': events_list,
                'overall_average_rating': round(overall_avg_rating, 2),
                'total_references': total_references,
                'page': page,
                'pages': total_pages,
                'per_page': per_page
            }, 200)

        except Exception as e:
            current_app.logger.error(f"Error in list_references: {str(e)}")
            return jsonify_response({'error': str(e)}, 500)


@reference_ns.route('/create')
class CreateReference(Resource):
    @reference_ns.expect(create_reference_model)
    @reference_ns.response(201, 'Reference created successfully')
    @reference_ns.response(400, 'Bad Request')
    @reference_ns.response(404, 'User or Post not found')
    def post(self):
        data = request.get_json()

        required_fields = ['from_user_id', 'to_user_id', 'post_id', 'rating', 'content']
        for field in required_fields:
            if field not in data:
                current_app.logger.error(f"Missing required field: {field}")
                return jsonify_response({'error': f"Missing required field: {field}"}, 400)

        if not 1 <= data['rating'] <= 5:
            return jsonify_response({'error': 'Rating must be between 1 and 5'}, 400)

        try:
            # Validate post and participants in a single query
            now = datetime.now(timezone.utc)

            post_query = db.session.query(
                Post,
                func.count(distinct(ChatRoomUser.user_id)).label('participant_count')
            ).filter(
                Post.id == data['post_id']
            ).join(
                ChatRoomUser,
                and_(
                    ChatRoomUser.post_id == Post.id,
                    ChatRoomUser.user_id.in_([data['from_user_id'], data['to_user_id']])
                )
            ).group_by(Post.id).first()

            if not post_query:
                # Check if post exists at all to give more specific error
                post_exists = db.session.query(Post).filter(Post.id == data['post_id']).first()
                if not post_exists:
                    return jsonify_response({'error': 'Post not found'}, 404)
                else:
                    return jsonify_response({'error': 'Users are not participants in this event'}, 400)

            post, participant_count = post_query
            if participant_count != 2:
                return jsonify_response({'error': 'Both users must be participants in the event'}, 400)

            # Check for existing reference
            existing_ref = Reference.query.get((data['from_user_id'], data['to_user_id'], data['post_id']))
            if existing_ref:
                return jsonify_response({'error': 'Reference already exists'}, 400)

            # Calculate new rating
            rating_stats = db.session.query(
                func.count(Reference.rating).label('count'),
                func.avg(Reference.rating).label('avg')
            ).filter(
                Reference.to_user_id == data['to_user_id']
            ).first()

            # Create reference
            reference = Reference(
                from_user_id=data['from_user_id'],
                to_user_id=data['to_user_id'],
                post_id=data['post_id'],
                rating=data['rating'],
                content=data['content']
            )

            # Calculate and update new rating
            total_ratings = (rating_stats.count or 0)
            current_avg = (rating_stats.avg or 0)
            new_rating = ((current_avg * total_ratings) + data['rating']) / (total_ratings + 1)

            db.session.add(reference)

            # Update user rating
            db.session.query(User).filter(
                User.id == data['to_user_id']
            ).update({
                'rating': new_rating
            })

            db.session.commit()

            return jsonify_response({'message': 'Reference created successfully'}, 201)

        except Exception as e:
            current_app.logger.error(f"Error creating reference: {str(e)}")
            db.session.rollback()
            return jsonify_response({'error': str(e)}, 500)