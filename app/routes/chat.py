from flask import Blueprint, request, current_app
from flask_socketio import emit, join_room, leave_room
from flask_restx import Api, Resource, fields
from sqlalchemy import exists, select, and_, func
from sqlalchemy.orm import joinedload
from functools import lru_cache
from datetime import datetime, timedelta

from app.utils import jsonify_response
from app.extensions import db, socketio
from app.models import ChatRoom, ChatRoomUser, Message, User, Profile

chat_bp = Blueprint('chat_bp', __name__)
chat_api = Api(
    chat_bp,
    version='1.0',
    title='Chat API',
    description='Chat API',
    doc='/docs',
)
chat_ns = chat_api.namespace('', description='Chat operations')

# Models
dynamic_load_model = chat_api.model(
    'DynamicLoadModel',
    {
        'page': fields.Integer(description='Page number', default=1),
        'per_page': fields.Integer(description='Items per page', default=20),
    }
)


@chat_ns.route('/rooms/<int:user_id>')
class ChatRooms(Resource):
    @chat_ns.expect(dynamic_load_model)
    @chat_ns.response(200, 'Success')
    @chat_ns.response(404, 'User not found')
    def post(self, user_id):
        """Get all chat rooms for a user"""
        data = request.get_json()

        page = data.get('page', 1)
        per_page = data.get('per_page', 20)

        try:
            # Verify user exists
            if not db.session.scalar(select(exists().where(User.id == user_id))):
                return jsonify_response({'error': 'User not found'}, 404)

            # Subquery to get latest message per room
            latest_messages = db.session.query(
                Message.post_id,
                Message.id.label('message_id'),
                Message.sender_id,
                Message.content,
                Message.created_at,
                func.row_number().over(
                    partition_by=Message.post_id,
                    order_by=Message.created_at.desc()
                ).label('rn')
            ).subquery()

            # Main query joining with latest messages
            chat_rooms = db.session.query(
                ChatRoom,
                latest_messages.c.message_id,
                latest_messages.c.sender_id,
                latest_messages.c.content,
                latest_messages.c.created_at
            ).join(
                ChatRoomUser,
                ChatRoom.post_id == ChatRoomUser.post_id
            ).outerjoin(
                latest_messages,
                and_(
                    ChatRoom.post_id == latest_messages.c.post_id,
                    latest_messages.c.rn == 1
                )
            ).filter(
                ChatRoomUser.user_id == user_id
            ).order_by(
                latest_messages.c.created_at.desc().nullslast()
            ).paginate(page=page, per_page=per_page)

            rooms_data = []
            for room, message_id, sender_id, content, created_at in chat_rooms.items:
                # Get unread count for the room
                unread_count = Message.query.filter(
                    Message.post_id == room.post_id,
                    ~Message.read_users.contains([user_id])
                ).count()

                room_data = {
                    'post_id': room.post_id,
                    'name': room.name,
                    'unread_count': unread_count
                }

                # Add latest message info if exists
                if message_id:
                    sender = Profile.query.get(sender_id)
                    room_data['latest_message'] = {
                        'id': message_id,
                        'sender_id': sender_id,
                        'sender_name': sender.nickname if sender else 'Unknown',
                        'content': content,
                        'created_at': created_at.isoformat()
                    }

                rooms_data.append(room_data)

            return jsonify_response({
                'rooms': rooms_data,
                'page': chat_rooms.page,
                'pages': chat_rooms.pages,
                'per_page': chat_rooms.per_page
            }, 200)

        except Exception as e:
            current_app.logger.error(f"Error getting chat rooms: {str(e)}")
            return jsonify_response({'error': str(e)}, 500)


message_history_model = chat_api.model(
    'MessageHistory',
    {
        'post_id': fields.Integer(required=True, description='Post/Room ID'),
        'user_id': fields.Integer(required=True, description='User ID requesting the history'),
        'before_id': fields.Integer(description='Get messages before this message ID (exclusive)', required=False),
        'limit': fields.Integer(description='Number of messages to return', default=50)
    }
)


@chat_ns.route('/messages')
class ChatMessages(Resource):
    @chat_ns.expect(message_history_model)
    @chat_ns.response(200, 'Success')
    @chat_ns.response(400, 'Bad Request')
    @chat_ns.response(403, 'Not authorized')
    @chat_ns.response(404, 'Room not found')
    def post(self):
        """Get message history for a chat room"""
        data = request.get_json()

        # Validate required fields
        if not all(key in data for key in ['post_id', 'user_id']):
            return jsonify_response({'error': 'Missing required fields'}, 400)

        post_id = data['post_id']
        user_id = data['user_id']
        before_id = data.get('before_id')
        limit = min(data.get('limit', 50), 100)  # Cap at 100 messages

        try:
            # Verify user is a member of the chat room
            chat_room_user = ChatRoomUser.query.filter_by(
                post_id=post_id,
                user_id=user_id
            ).first()

            if not chat_room_user:
                return jsonify_response(
                    {'error': 'Not authorized to access this chat room'},
                    403
                )

            # Build base query
            query = Message.query.filter(Message.post_id == post_id)

            # Add before_id filter if provided
            if before_id:
                query = query.filter(Message.id < before_id)

            # Get messages ordered by newest first with limit
            messages = query.order_by(Message.id.desc()).limit(limit + 1).all()

            # Check if there are more messages
            has_more = len(messages) > limit
            messages = messages[:limit]  # Remove the extra message if it exists

            # Format messages
            formatted_messages = []
            oldest_id = None

            for message in messages:
                # Keep track of oldest message ID
                if oldest_id is None or message.id < oldest_id:
                    oldest_id = message.id

                # Get sender's profile
                sender = Profile.query.get(message.sender_id)

                # Format message data
                message_data = {
                    'id': message.id,
                    'sender_id': message.sender_id,
                    'sender_name': sender.nickname if sender else 'Unknown',
                    'content': message.content,
                    'created_at': message.created_at.isoformat(),
                    'read_users': message.read_users
                }
                formatted_messages.append(message_data)

                # Mark messages as read if this is the initial load (no before_id)
                if not before_id:
                    unread_messages = [
                        msg for msg in messages
                        if user_id not in msg.read_users
                    ]

                    for msg in unread_messages:
                        if user_id not in msg.read_users:
                            msg.read_users.append(user_id)

            db.session.commit()
            return jsonify_response({
                'messages': formatted_messages,
                'has_more': has_more,
                'oldest_id': oldest_id
            }, 200)

        except Exception as e:
            current_app.logger.error(f"Error getting message history: {str(e)}")
            return jsonify_response({'error': str(e)}, 500)


# Cache for room members - cached for 5 minutes
@lru_cache(maxsize=1000)
def get_room_members(post_id, timestamp):
    """
    Get all members of a chat room. Result is cached with timestamp-based invalidation.
    The timestamp parameter helps invalidate cache based on time.
    """
    members = ChatRoomUser.query \
        .options(joinedload(ChatRoomUser.user).joinedload(User.profile)) \
        .filter_by(post_id=post_id) \
        .all()
    return [(m.user_id, m.user.profile.nickname if m.user.profile else 'Unknown') for m in members]


def get_current_timestamp_bucket():
    """Get current timestamp rounded to 5-minute intervals for cache key"""
    now = datetime.utcnow()
    return now.replace(second=0, microsecond=0) - timedelta(minutes=now.minute % 5)


# Connection management
connected_users = {}


@socketio.on('connect')
def handle_connect():
    try:
        current_app.logger.info("\n=== Connection Info ===")
        current_app.logger.info(f"Socket ID: {request.sid}")
        current_app.logger.info(f"Transport: {request.namespace}")
        current_app.logger.info(f"Environment: {request.environ}")
        current_app.logger.info(f"Headers: {dict(request.headers)}")
        current_app.logger.info(f"Remote Address: {request.remote_addr}")
        current_app.logger.info(f"Arguments: {request.args}")
        current_app.logger.info(f"Cookie: {request.cookies}")

        # Print custom auth/query parameters if any
        #print(f"Query String: {request.query_string.decode()}")

        user_id = request.args.get('user_id')
        if not user_id:
            current_app.logger.warning('Connection attempt without user_id')
            return False

        # Clean up any existing rooms this socket might be in
        if request.sid in [sid for sid in connected_users.values()]:
            for old_user_id, old_sid in list(connected_users.items()):
                if old_sid == request.sid:
                    leave_room(f'user_{old_user_id}')
                    del connected_users[old_user_id]

        # Join user's personal room
        user_room = f'user_{user_id}'
        join_room(user_room)
        connected_users[user_id] = request.sid

        current_app.logger.info(f'User {user_id} connected with sid {request.sid}')
        return True

    except Exception as e:
        current_app.logger.error(f'Error in handle_connect: {str(e)}')
        return False


@socketio.on('disconnect')
def handle_disconnect():
    try:
        user_id = request.args.get('user_id')
        if user_id and user_id in connected_users:
            leave_room(f'user_{user_id}')
            del connected_users[user_id]
            current_app.logger.info(f'User {user_id} disconnected')

    except Exception as e:
        current_app.logger.error(f'Error in handle_disconnect: {str(e)}')


# Batch message processing
def process_message_batch(messages, post_id, recipient_user_ids):
    """Process and emit a batch of messages efficiently"""
    try:
        message_data_batch = []
        for message in messages:
            message_data = {
                'id': message.id,
                'post_id': post_id,
                'sender_id': message.sender_id,
                'content': message.content,
                'created_at': message.created_at.isoformat(),
                'read_users': message.read_users
            }
            message_data_batch.append(message_data)

        # Emit messages to all recipients in their personal rooms
        for user_id in recipient_user_ids:
            user_room = f'user_{user_id}'
            for message_data in message_data_batch:
                emit('new_message', message_data, room=user_room)

    except Exception as e:
        current_app.logger.error(f'Error in process_message_batch: {str(e)}')
        raise


@socketio.on('send_message')
def handle_message(data):
    try:
        post_id = data.get('post_id')
        sender_id = data.get('sender_id')
        content = data.get('content')

        if not all([post_id, sender_id, content]):
            emit('error', {'message': 'Missing required fields'})
            return

        # Get current timestamp bucket for cache
        current_bucket = get_current_timestamp_bucket()

        # Get room members from cache
        room_members = get_room_members(post_id, current_bucket)

        if not any(member[0] == sender_id for member in room_members):
            emit('error', {'message': 'Not authorized to send messages in this chat room'})
            return

        # Create new message
        message = Message(
            post_id=post_id,
            sender_id=sender_id,
            content=content,
            read_users=[sender_id]
        )

        try:
            db.session.add(message)
            db.session.commit()

            # Get recipient user IDs from cached room members
            recipient_user_ids = [member[0] for member in room_members]

            # Process and emit message
            process_message_batch([message], post_id, recipient_user_ids)

            current_app.logger.info(f'Message {message.id} sent successfully to {len(recipient_user_ids)} recipients')

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Database error in handle_message: {str(e)}')
            emit('error', {'message': 'Failed to save message'})
            return

    except Exception as e:
        current_app.logger.error(f'Error in handle_message: {str(e)}')
        emit('error', {'message': 'Failed to process message'})


@socketio.on_error()
def error_handler(e):
    current_app.logger.error(f'SocketIO error: {str(e)}')
    emit('error', {'message': 'An unexpected error occurred'})
