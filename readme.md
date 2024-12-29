# SparkUp-Server

SparkUp is a Flask-based social platform that enables users to connect, collaborate, and participate in various activities. The platform features real-time chat, user profiles, event posting, and a reference system.

## Features

- **User Authentication**: Secure user registration and login system
- **Profile Management**: Detailed user profiles with customizable fields
- **Event Posts**: Create and manage event posts with various attributes
- **Real-time Chat**: WebSocket-based chat rooms for event participants
- **Reference System**: Post-event rating and reference system
- **Applicant Management**: System for managing event applications
- **Bookmarking System**: Save and organize interesting events
- **Comment System**: Engage in discussions through comments
- **Dynamic Content Loading**: Pagination support for efficient data loading

## Tech Stack

- **Backend Framework**: Flask
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: Flask-Security
- **Real-time Communication**: Flask-SocketIO with eventlet
- **API Documentation**: Flask-RESTX
- **Database Migration**: Alembic with Flask-Migrate
- **CORS Support**: Flask-CORS

## Requirements

- Python 3.x
- PostgreSQL
- Additional requirements listed in `requirements.txt`

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd sparkup
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
export FLASK_APP="run.py"
export DATABASE_URL="postgresql://username:password@localhost:5432/database_name"
export FLASK_CORS_ORIGINS="*"  # Configure as needed for production
```

5. Initialize the database:
```bash
flask db upgrade
```

## Running the Application

Start the application using gunicorn with eventlet worker:
```bash
gunicorn -k eventlet -w 1 run:app
```

Or for development:
```bash
python run.py
```

## API Documentation

API documentation is available at `/docs` endpoint for each blueprint:
- Auth API: `/auth/docs`
- Profile API: `/profile/docs`
- Post API: `/post/docs`
- Comment API: `/comment/docs`
- Applicant API: `/applicant/docs`
- Reference API: `/reference/docs`
- Chat API: `/chat/docs`

## Project Structure

```
sparkup/
├── app/
│   ├── extensions.py    # Flask extensions
│   ├── config.py        # Configuration
│   ├── main.py          # Application factory
│   ├── models.py        # Database models
│   ├── utils.py         # Utility functions
│   └── routes/          # API routes
├── migrations/          # Database migrations
├── requirements.txt     # Project dependencies
├── run.py               # Application entry point
└── README.md            # This file
```

## Database Models

- **User**: Core user information and authentication
- **Profile**: Extended user profile details
- **Post**: Event and activity posts
- **PostComment**: Comment system
- **ChatRoom**: Real-time chat functionality
- **Reference**: User rating and reference system
- **PostApplicant**: Event application management

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the GNU General Public License v3.0 - see the LICENSE file for details.

## Security

- Password hashing using bcrypt
- JWT-based authentication
- CORS protection
- SQL injection prevention through SQLAlchemy
- WebSocket security measures

## Deployment Notes

- Configure `FLASK_CORS_ORIGINS` appropriately for production
- Use proper SSL/TLS certificates for production
- Set up proper database backup procedures
- Configure proper logging for production environment
- Consider using a process manager like supervisord
- Set up proper monitoring and alerting

## Support

For support, please open an issue in the GitHub repository.
