import 'package:socket_io_client/socket_io_client.dart' as IO;

// Define event types
enum SocketStatus {
  connected,
  disconnected,
  error
}

// Define callback types
typedef MessageCallback = void Function(ChatMessage message);
typedef StatusCallback = void Function(SocketStatus status, String? message);

class SocketService {
  // Singleton pattern
  static final SocketService _instance = SocketService._internal();
  factory SocketService() => _instance;
  SocketService._internal();

  IO.Socket? socket;
  int? _userId;

  // Callbacks
  MessageCallback? onNewMessage;
  StatusCallback? onStatusChange;

  bool get isConnected => socket?.connected ?? false;
  int? get currentUserId => _userId;

  void initSocket({
    required int userId,
    required String serverUrl,
    MessageCallback? onMessage,
    StatusCallback? onStatus,
  }) {
    _userId = userId;
    onNewMessage = onMessage;
    onStatusChange = onStatus;

    // Initialize socket with configuration
    socket = IO.io(serverUrl, <String, dynamic>{
      'transports': ['websocket'],
      'autoConnect': false,
      'query': {'user_id': userId.toString()},
      'reconnection': true,
      'reconnectionDelay': 1000,
      'reconnectionDelayMax': 5000,
      'reconnectionAttempts': 5,
    });

    _setupEventHandlers();
    socket!.connect();
  }

  void _setupEventHandlers() {
    socket!
      ..onConnect((_) {
        print('Socket connected');
        onStatusChange?.call(SocketStatus.connected, 'Connected to server');
      })
      ..onDisconnect((_) {
        print('Socket disconnected');
        onStatusChange?.call(SocketStatus.disconnected, 'Disconnected from server');
      })
      ..onError((error) {
        print('Socket error: $error');
        onStatusChange?.call(SocketStatus.error, error.toString());
      })
      ..onConnectError((error) {
        print('Connection error: $error');
        onStatusChange?.call(SocketStatus.error, 'Connection failed: $error');
      })
      ..on('new_message', _handleNewMessage);
  }

  void _handleNewMessage(dynamic data) {
    try {
      final message = ChatMessage.fromJson(data as Map<String, dynamic>);
      print('New message received: ${message.content}');
      onNewMessage?.call(message);
    } catch (e) {
      print('Error parsing message: $e');
      onStatusChange?.call(SocketStatus.error, 'Error parsing message: $e');
    }
  }

  Future<void> sendMessage({
    required int postId,
    required String content,
  }) async {
    if (!isConnected || _userId == null) {
      throw SocketException('Socket is not connected');
    }

    try {
      socket!.emit('send_message', {
        'post_id': postId,
        'sender_id': _userId,
        'content': content,
      });
    } catch (e) {
      print('Error sending message: $e');
      throw SocketException('Failed to send message: $e');
    }
  }

  void disconnect() {
    socket?.disconnect();
    socket = null;
    _userId = null;
    onNewMessage = null;
    onStatusChange = null;
  }
}

class SocketException implements Exception {
  final String message;
  SocketException(this.message);

  @override
  String toString() => 'SocketException: $message';
}

class ChatMessage {
  final int id;
  final int postId;
  final int senderId;
  final String senderName;
  final String content;
  final DateTime createdAt;
  final List<int> readUsers;

  ChatMessage({
    required this.id,
    required this.postId,
    required this.senderId,
    required this.senderName,
    required this.content,
    required this.createdAt,
    required this.readUsers,
  });

  factory ChatMessage.fromJson(Map<String, dynamic> json) {
    return ChatMessage(
      id: json['id'] as int,
      postId: json['post_id'] as int,
      senderId: json['sender_id'] as int,
      senderName: json['sender_name'] as String,
      content: json['content'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
      readUsers: List<int>.from(json['read_users'] as List),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'post_id': postId,
      'sender_id': senderId,
      'sender_name': senderName,
      'content': content,
      'created_at': createdAt.toIso8601String(),
      'read_users': readUsers,
    };
  }
}