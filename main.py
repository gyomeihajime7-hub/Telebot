import os
import asyncio
import logging
from threading import Thread

from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from telegram.ext import Application
from telegram import Update
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# Import db from models to avoid circular import
from models import db

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "a-secret-key-for-telegram-bot")

# Configure the database - prioritize Neon database for production
database_url = os.environ.get("NEON_DATABASE_URL") or os.environ.get("DATABASE_URL")
if not database_url:
    logger.error("No database URL found. Please set NEON_DATABASE_URL or DATABASE_URL environment variable.")
    exit(1)

# Clean the database URL if it contains psql command syntax
if database_url.startswith("psql"):
    # Extract the actual URL from psql command
    import re
    match = re.search(r"'(postgresql://[^']+)'", database_url)
    if match:
        database_url = match.group(1)
    else:
        logger.error("Could not extract database URL from psql command")
        exit(1)

logger.info(f"Using database URL: {database_url[:30]}...")  # Log first 30 chars for debugging
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

# Import models and bot handlers
with app.app_context():
    import models  # noqa: F401
    from bot_handlers import setup_bot_handlers
    db.create_all()


@app.route('/')
def health_check():
    """Health check endpoint for Render"""
    return {
        "status": "Bot is running",
        "service": "Telegram File Management Bot",
        "version": "1.0.0"
    }


@app.route('/health')
def health():
    """Additional health endpoint"""
    return {"status": "healthy"}


@app.route('/favicon.ico')
def favicon():
    """Favicon endpoint to prevent 404 errors"""
    return "", 204


@app.route('/debug')
def debug():
    """Debug endpoint to check environment variables (for troubleshooting)"""
    return {
        "bot_token_set": bool(os.environ.get("BOT_TOKEN")),
        "database_url_set": bool(os.environ.get("DATABASE_URL")),
        "flask_secret_set": bool(os.environ.get("FLASK_SECRET_KEY")),
        "render_env": bool(os.environ.get("RENDER")),
        "port": os.environ.get("PORT", "5000")
    }


def run_bot():
    """Run the Telegram bot"""
    try:
        bot_token = os.environ.get("BOT_TOKEN")
        if not bot_token:
            logger.error("BOT_TOKEN environment variable is required")
            return

        logger.info(f"Bot token found: {bot_token[:10]}..." if bot_token else "No token")
        
        # Create application
        application = Application.builder().token(bot_token).build()
        
        # Setup bot handlers
        with app.app_context():
            setup_bot_handlers(application, db, app)
        
        # Start the bot with proper async handling
        logger.info("Starting Telegram bot polling...")
        import asyncio
        
        # Create new event loop for this thread if needed
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Start polling
        application.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")


def run_flask():
    """Run the Flask app"""
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)


async def setup_webhook():
    """Set up webhook for production deployment"""
    try:
        bot_token = os.environ.get("BOT_TOKEN")
        if not bot_token:
            logger.error("BOT_TOKEN not found for webhook setup")
            return None
            
        application = Application.builder().token(bot_token).build()
        
        with app.app_context():
            setup_bot_handlers(application, db, app)
        
        # Get the webhook URL from environment or construct it
        webhook_url = os.environ.get("WEBHOOK_URL")
        if not webhook_url:
            # Construct from Render service URL
            service_url = os.environ.get("RENDER_EXTERNAL_URL", "https://your-service.onrender.com")
            webhook_url = f"{service_url}/webhook/{bot_token}"
        
        logger.info(f"Setting webhook URL: {webhook_url}")
        await application.bot.set_webhook(url=webhook_url)
        
        return application
        
    except Exception as e:
        logger.error(f"Error setting up webhook: {e}")
        return None


if __name__ == "__main__":
    # Check if we're running on Render (production)
    if os.environ.get("RENDER"):
        # On Render, use webhook mode with Flask
        logger.info("Running on Render - Flask app with webhook mode")
        
        # Debug environment variables
        logger.info(f"RENDER env: {os.environ.get('RENDER')}")
        logger.info(f"PORT env: {os.environ.get('PORT')}")
        logger.info(f"BOT_TOKEN set: {bool(os.environ.get('BOT_TOKEN'))}")
        logger.info(f"DATABASE_URL set: {bool(os.environ.get('DATABASE_URL'))}")
        
        # Set up bot for webhook mode with synchronous processing
        bot_token = os.environ.get("BOT_TOKEN")
        if bot_token:
            from telegram import Bot
            from telegram.ext._utils.types import HandlerCallback
            
            # Create a simple Bot instance for synchronous operations
            bot = Bot(token=bot_token)
            
            # Import required models
            from models import FileMetadata
            
            # Add webhook endpoint with direct synchronous processing
            @app.route(f'/webhook/{bot_token}', methods=['POST'])
            def webhook():
                """Handle webhook updates from Telegram - synchronous processing"""
                try:
                    json_data = request.get_json(force=True)
                    if not json_data:
                        logger.error("No JSON data received in webhook")
                        return 'No data', 400
                    
                    update = Update.de_json(json_data, bot)
                    if not update:
                        logger.error("Failed to parse update from JSON")
                        return 'Invalid update', 400
                    
                    logger.info(f"Processing update: {update.update_id}")
                    
                    # Process different types of updates synchronously
                    with app.app_context():
                        try:
                            if update.message and update.message.from_user:
                                message = update.message
                                user_id = message.from_user.id
                                
                                # Handle commands
                                if message.text:
                                    if message.text.startswith('/start'):
                                        # Send start message synchronously
                                        import asyncio
                                        loop = asyncio.new_event_loop()
                                        asyncio.set_event_loop(loop)
                                        try:
                                            loop.run_until_complete(bot.send_message(
                                                chat_id=user_id,
                                                text="🎉 Welcome to your Personal File Manager Bot!\n\n"
                                                     "I can help you store and manage your files securely. Here's what I can do:\n\n"
                                                     "📤 **Upload Files**: Send me any file and I'll store it safely\n"
                                                     "📁 **View Files**: Use /myfiles to see all your stored files\n"
                                                     "❓ **Get Help**: Use /help for more information\n\n"
                                                     "Ready to get started? Send me a file!"
                                            ))
                                        finally:
                                            loop.close()
                                    elif message.text.startswith('/help'):
                                        import asyncio
                                        loop = asyncio.new_event_loop()
                                        asyncio.set_event_loop(loop)
                                        try:
                                            loop.run_until_complete(bot.send_message(
                                                chat_id=user_id,
                                                text="🤖 **File Manager Bot Help**\n\n"
                                                     "**Available Commands:**\n"
                                                     "• /start - Welcome message and introduction\n"
                                                     "• /myfiles - View all your stored files\n"
                                                     "• /help - Show this help message\n\n"
                                                     "**How to use:**\n"
                                                     "1. Send me any file (document, image, video, etc.)\n"
                                                     "2. I'll store it and give you a confirmation\n"
                                                     "3. Use /myfiles to see your file collection\n"
                                                     "4. Click on any file to download it again\n\n"
                                                     "That's it! Simple and secure file storage at your fingertips! 📁✨"
                                            ))
                                        finally:
                                            loop.close()
                                    elif message.text.startswith('/myfiles'):
                                        # Query user's files from database
                                        files = FileMetadata.query.filter_by(user_id=user_id).order_by(FileMetadata.upload_date.desc()).all()
                                        
                                        import asyncio
                                        loop = asyncio.new_event_loop()
                                        asyncio.set_event_loop(loop)
                                        try:
                                            if not files:
                                                loop.run_until_complete(bot.send_message(
                                                    chat_id=user_id,
                                                    text="📁 Your file storage is empty!\n\nSend me any file to get started. I can store documents, images, videos, and more! 📤"
                                                ))
                                            else:
                                                # Create file list message
                                                file_list = f"📁 **Your Files** ({len(files)} total)\n\n"
                                                for i, file in enumerate(files[:10], 1):  # Show first 10 files
                                                    size_mb = round(file.file_size / (1024 * 1024), 2)
                                                    file_list += f"{i}. **{file.filename}**\n"
                                                    file_list += f"   📊 {size_mb} MB • {file.upload_date.strftime('%Y-%m-%d %H:%M')}\n\n"
                                                
                                                if len(files) > 10:
                                                    file_list += f"... and {len(files) - 10} more files"
                                                
                                                loop.run_until_complete(bot.send_message(
                                                    chat_id=user_id,
                                                    text=file_list,
                                                    parse_mode='Markdown'
                                                ))
                                        finally:
                                            loop.close()
                                
                                # Handle file uploads
                                elif message.document or message.photo or message.video or message.audio or message.voice:
                                    # Extract file information
                                    file_obj = None
                                    filename = "unknown_file"
                                    
                                    if message.document:
                                        file_obj = message.document
                                        filename = file_obj.file_name or f"document_{file_obj.file_id[:8]}"
                                    elif message.photo:
                                        file_obj = message.photo[-1]  # Get highest resolution
                                        filename = f"photo_{file_obj.file_id[:8]}.jpg"
                                    elif message.video:
                                        file_obj = message.video
                                        filename = f"video_{file_obj.file_id[:8]}.mp4"
                                    elif message.audio:
                                        file_obj = message.audio
                                        filename = file_obj.file_name or f"audio_{file_obj.file_id[:8]}.mp3"
                                    elif message.voice:
                                        file_obj = message.voice
                                        filename = f"voice_{file_obj.file_id[:8]}.ogg"
                                    
                                    if file_obj:
                                        # Save file metadata to database
                                        file_metadata = FileMetadata(
                                            user_id=user_id,
                                            filename=filename,
                                            file_id=file_obj.file_id,
                                            file_size=getattr(file_obj, 'file_size', 0),
                                            mime_type=getattr(file_obj, 'mime_type', 'application/octet-stream')
                                        )
                                        
                                        db.session.add(file_metadata)
                                        db.session.commit()
                                        
                                        # Send confirmation
                                        size_mb = round(file_metadata.file_size / (1024 * 1024), 2) if file_metadata.file_size > 0 else 0
                                        import asyncio
                                        loop = asyncio.new_event_loop()
                                        asyncio.set_event_loop(loop)
                                        try:
                                            loop.run_until_complete(bot.send_message(
                                                chat_id=user_id,
                                                text=f"✅ **File Uploaded Successfully!**\n\n"
                                                     f"📄 **Name**: {filename}\n"
                                                     f"📊 **Size**: {size_mb} MB\n"
                                                     f"🕒 **Stored**: {file_metadata.upload_date.strftime('%Y-%m-%d %H:%M')}\n\n"
                                                     f"Use /myfiles to view all your files! 📁",
                                                parse_mode='Markdown'
                                            ))
                                        finally:
                                            loop.close()
                            
                            elif update.callback_query and update.callback_query.id:
                                # Handle callback queries if needed
                                import asyncio
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                try:
                                    loop.run_until_complete(bot.answer_callback_query(callback_query_id=update.callback_query.id))
                                finally:
                                    loop.close()
                            
                            logger.info(f"Successfully processed update: {update.update_id}")
                            
                        except Exception as proc_error:
                            logger.error(f"Error processing update: {proc_error}", exc_info=True)
                            # Send error message to user
                            if update.message and update.message.from_user:
                                try:
                                    import asyncio
                                    loop = asyncio.new_event_loop()
                                    asyncio.set_event_loop(loop)
                                    try:
                                        loop.run_until_complete(bot.send_message(
                                            chat_id=update.message.from_user.id,
                                            text="❌ Sorry, something went wrong. Please try again."
                                        ))
                                    finally:
                                        loop.close()
                                except:
                                    pass
                    
                    return 'OK'
                    
                except Exception as e:
                    logger.error(f"Webhook error: {e}", exc_info=True)
                    return 'Error', 500
            
            # Set up webhook URL automatically
            try:
                # Get the service URL from Render environment
                service_url = os.environ.get("RENDER_EXTERNAL_URL")
                if not service_url:
                    # Fallback - construct from common Render pattern
                    service_name = os.environ.get("RENDER_SERVICE_NAME", "telegram-file-bot")
                    service_url = f"https://{service_name}.onrender.com"
                
                webhook_url = f"{service_url}/webhook/{bot_token}"
                logger.info(f"Setting webhook URL: {webhook_url}")
                
                # Set webhook using synchronous approach for startup
                import requests
                webhook_response = requests.post(
                    f"https://api.telegram.org/bot{bot_token}/setWebhook",
                    json={"url": webhook_url}
                )
                if webhook_response.status_code == 200:
                    logger.info("Webhook set successfully")
                else:
                    logger.error(f"Failed to set webhook: {webhook_response.text}")
                    
            except Exception as e:
                logger.error(f"Error setting webhook: {e}")
            
            logger.info("Bot configured for webhook mode")
        
        # Run Flask app (this opens the required port for Render)
        logger.info("Starting Flask app...")
        run_flask()
    else:
        # Local development - run both
        logger.info("Running locally - starting both Flask and Telegram bot")
        
        # Start Flask in a separate thread
        flask_thread = Thread(target=run_flask, daemon=True)
        flask_thread.start()
        
        # Run bot in main thread
        run_bot()
