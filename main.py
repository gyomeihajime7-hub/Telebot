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
        
        # Set up bot for webhook mode
        bot_token = os.environ.get("BOT_TOKEN")
        if bot_token:
            application = Application.builder().token(bot_token).build()
            with app.app_context():
                setup_bot_handlers(application, db, app)
            
            # Add webhook endpoint
            @app.route(f'/webhook/{bot_token}', methods=['POST'])
            def webhook():
                """Handle webhook updates from Telegram"""
                try:
                    update = Update.de_json(request.get_json(force=True), application.bot)
                    # Process update asynchronously
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(application.process_update(update))
                    loop.close()
                    return 'OK'
                except Exception as e:
                    logger.error(f"Webhook error: {e}")
                    return 'Error', 500
            
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
