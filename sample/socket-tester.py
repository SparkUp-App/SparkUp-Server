import socketio
import sys
from datetime import datetime


class ChatTester:
    def __init__(self, server_url='https://sparkup-9db24d093e0f.herokuapp.com'):
        self.sio = socketio.Client()
        self.server_url = server_url
        self.setup_event_handlers()

    def setup_event_handlers(self):
        @self.sio.on('connect')
        def on_connect():
            print(f'Connected to server at {datetime.now()}')

        @self.sio.on('disconnect')
        def on_disconnect():
            print(f'Disconnected from server at {datetime.now()}')

        @self.sio.on('new_message')
        def on_new_message(data):
            print(f'\nReceived message at {datetime.now()}:')
            print(f'From user {data["sender_id"]}:')
            print(f'Content: {data["content"]}')
            print(f'Message ID: {data["id"]}')
            print(f'Read by: {data["read_users"]}')

        @self.sio.on('error')
        def on_error(data):
            print(f'Error received: {data["message"]}')

    def connect(self, user_id):
        """Connect to the server with a specific user ID"""
        try:
            self.sio.connect(
                f"{self.server_url}?user_id={user_id}",
                transports=['websocket']
            )
            return True
        except Exception as e:
            print(f'Connection error: {str(e)}')
            return False

    def disconnect(self):
        """Disconnect from the server"""
        try:
            self.sio.disconnect()
            return True
        except Exception as e:
            print(f'Disconnection error: {str(e)}')
            return False

    def send_message(self, post_id, sender_id, content):
        """Send a message to a specific chat room"""
        try:
            self.sio.emit('send_message', {
                'post_id': post_id,
                'sender_id': sender_id,
                'content': content
            })
            print(f'Message sent at {datetime.now()}')
            return True
        except Exception as e:
            print(f'Error sending message: {str(e)}')
            return False


def main():
    user_id = 7

    # Create tester instance
    tester = ChatTester()

    try:
        # Connect to server
        if not tester.connect(user_id):
            print("Failed to connect")
            sys.exit(1)

        while True:
            # Simple command interface
            command = input("\nEnter command (send/quit): ").lower()

            if command == 'quit':
                break
            elif command == 'send':
                post_id = int(input("Enter post ID: "))
                content = input("Enter message: ")
                tester.send_message(post_id, user_id, content)
            else:
                print("Unknown command. Available commands: send, quit")

    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        tester.disconnect()


if __name__ == '__main__':
    main()
    
