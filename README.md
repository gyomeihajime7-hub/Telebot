# Telegram File Management Bot

A premium Telegram bot that provides secure file management services. Users can upload, store, and manage files through Telegram, acting as a personal cloud storage assistant.

## Features

- 📁 **File Upload & Storage**: Upload any type of file through Telegram
- 🗃️ **File Management**: View and manage your uploaded files
- 👤 **Multi-User Support**: Each user has their own file space
- 🔒 **Secure Storage**: Files are stored securely with metadata tracking
- ⚡ **Fast Retrieval**: Quick access to your files with inline keyboards
- 📊 **File Metadata**: Track file size, type, upload date, and more

## Commands

- `/start` - Initialize the bot and get welcome message
- `/help` - Show help information and available commands
- `/myfiles` - View all your uploaded files with interactive buttons

## Tech Stack

- **Backend**: Python Flask with SQLAlchemy ORM
- **Database**: PostgreSQL for metadata storage
- **Bot Framework**: python-telegram-bot library
- **Deployment**: Render.com with automatic scaling
- **File Storage**: Telegram's infrastructure (files up to 20MB)

## Quick Start

1. Find the bot on Telegram (contact the developer for bot username)
2. Send `/start` to initialize
3. Upload any file by sending it directly to the bot
4. Use `/myfiles` to view and manage your uploads

## For Developers

### Local Development

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set environment variables:
   - `BOT_TOKEN`: Get from @BotFather on Telegram
   - `DATABASE_URL`: PostgreSQL connection string
   - `FLASK_SECRET_KEY`: Random secret for sessions

4. Run: `python main.py`

### Deployment to Render

See `DEPLOY_TO_RENDER.md` for detailed deployment instructions.

### Environment Variables

- `BOT_TOKEN`: Telegram bot token from @BotFather
- `DATABASE_URL`: PostgreSQL database URL
- `FLASK_SECRET_KEY`: Flask session secret key
- `RENDER`: Set to "true" for production deployment

## Database Schema

### FileMetadata Table
- `id`: Primary key
- `user_id`: Telegram user ID
- `file_id`: Telegram file ID for retrieval
- `filename`: Original filename
- `file_size`: File size in bytes
- `mime_type`: File MIME type
- `upload_date`: Upload timestamp

## API Endpoints

- `GET /`: Health check and bot status
- `GET /health`: Detailed health check for monitoring
- `POST /webhook/{bot_token}`: Telegram webhook endpoint (production only)

## Security Features

- User isolation: Files are tied to Telegram user IDs
- Secure token handling: Bot token stored as environment variable
- Database security: PostgreSQL with proper connection handling
- Input validation: File type and size validation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support or questions, contact the developer or create an issue in the repository.