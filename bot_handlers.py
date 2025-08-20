import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram.constants import ParseMode

logger = logging.getLogger(__name__)


def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes is None:
        return "Unknown size"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def format_date(date_obj):
    """Format date in a user-friendly way"""
    if date_obj is None:
        return "Unknown date"
    return date_obj.strftime("%B %d, %Y at %I:%M %p")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    welcome_text = """
🌟 <b>Welcome to @SAN_mediabot!</b> 🌟

🚀 <i>Your personal cloud storage assistant</i>

<b>✨ What I can do for you:</b>
📁 Store any type of file securely
📋 Keep track of all your uploads
💾 Easy file retrieval anytime
🔍 Smart file management

<b>🎯 Quick Commands:</b>
/myfiles - 📂 View all your files
/start - 🏠 Show this welcome message
/help - ❓ Get detailed help

<b>📤 Getting Started:</b>
Simply send me any file and I'll store it safely for you!

<i>Built with ❤️ for premium experience</i>
"""
    
    keyboard = [
        [
            InlineKeyboardButton("📂 My Files", callback_data="my_files"),
            InlineKeyboardButton("❓ Help", callback_data="help")
        ],
        [
            InlineKeyboardButton("🚀 Upload First File", callback_data="upload_guide")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text,
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = """
🔧 <b>How to Use @SAN_mediabot</b> 🔧

<b>📤 Uploading Files:</b>
• Send any file directly to this chat
• Supported: Documents, Images, Videos, Audio, etc.
• Files are stored securely with metadata

<b>📁 Managing Files:</b>
• Use /myfiles to see all your uploaded files
• Click any file button to download instantly
• Files are organized by upload date

<b>🔍 File Information:</b>
• File name and size are preserved
• Upload timestamp is recorded
• Easy one-click download access

<b>⚡ Pro Tips:</b>
• Send multiple files at once
• Use descriptive filenames for easy identification
• Your files are private and secure

<b>🆘 Need Support?</b>
For any queries contact @takezo_5
"""
    
    keyboard = [
        [
            InlineKeyboardButton("📂 View My Files", callback_data="my_files"),
            InlineKeyboardButton("🏠 Home", callback_data="start")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        help_text,
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup
    )


async def handle_file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE, db, flask_app):
    """Handle file uploads"""
    try:
        from models import FileMetadata
        
        user_id = update.effective_user.id
        message = update.message
        
        # Get file information based on message type
        file_obj = None
        filename = "unknown_file"
        detected_mime_type = None
        
        if message.document:
            file_obj = message.document
            filename = file_obj.file_name or "document"
            detected_mime_type = getattr(file_obj, 'mime_type', None)
        elif message.photo:
            file_obj = message.photo[-1]  # Get highest resolution
            filename = f"photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            detected_mime_type = "image/jpeg"
        elif message.video:
            file_obj = message.video
            filename = file_obj.file_name or f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            detected_mime_type = getattr(file_obj, 'mime_type', "video/mp4")
        elif message.audio:
            file_obj = message.audio
            filename = file_obj.file_name or f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
            detected_mime_type = getattr(file_obj, 'mime_type', "audio/mpeg")
        elif message.voice:
            file_obj = message.voice
            filename = f"voice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ogg"
            detected_mime_type = "audio/ogg"
        elif message.video_note:
            file_obj = message.video_note
            filename = f"video_note_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            detected_mime_type = "video/mp4"
        
        if not file_obj:
            await message.reply_text("❌ Sorry, I couldn't process this file type.")
            return
        
        # Save to database
        with flask_app.app_context():
            # Check if file already exists for this user
            existing_file = FileMetadata.query.filter_by(
                user_id=user_id, 
                file_id=file_obj.file_id
            ).first()
            
            if existing_file:
                # File already exists, return the existing record
                file_metadata = existing_file
                success_message = "File already exists in your storage!"
            else:
                # Create new file metadata record with proper exception handling
                try:
                    file_metadata = FileMetadata(
                        user_id=user_id,
                        file_id=file_obj.file_id,
                        filename=filename,
                        file_size=getattr(file_obj, 'file_size', None),
                        mime_type=detected_mime_type or getattr(file_obj, 'mime_type', None)
                    )
                    db.session.add(file_metadata)
                    db.session.commit()
                    success_message = "File Uploaded Successfully!"
                except Exception as e:
                    db.session.rollback()
                    # Try to get existing file if unique constraint failed
                    existing_file = FileMetadata.query.filter_by(file_id=file_obj.file_id).first()
                    if existing_file:
                        file_metadata = existing_file
                        success_message = "File already exists in your storage!"
                    else:
                        raise e
            
            # Get the file metadata for response
            file_size = file_metadata.file_size
            mime_type = file_metadata.mime_type or getattr(file_obj, 'mime_type', None)
            upload_date = file_metadata.upload_date
        
        # Success response with premium styling
        success_text = f"""
✅ <b>{success_message}</b>

📁 <b>File Details:</b>
🔸 Name: <code>{filename}</code>
🔸 Size: <code>{format_file_size(file_size)}</code>
🔸 Type: <code>{mime_type or 'Unknown'}</code>
🔸 Uploaded: <code>{format_date(upload_date)}</code>

🎉 <i>Your file is safely stored! Use /myfiles to view and download all your files.</i>

💡 <b>Note:</b> Telegram supports files up to 2GB. For larger files, consider splitting them or using compression.
"""
        
        # Create keyboard with "Show My Files" button
        keyboard = [
            [InlineKeyboardButton("📂 Show My Files", callback_data="my_files")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send success message with "Show My Files" button
        await message.reply_text(
            success_text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
        
        # Delete the original file message for privacy after successful processing
        try:
            await message.delete()
        except Exception as delete_error:
            logger.warning(f"Could not delete user's file message: {str(delete_error)}")
            # Continue execution even if delete fails (might be due to permissions)
        
    except Exception as e:
        logger.error(f"Error handling file upload: {str(e)}")
        await message.reply_text(
            "❌ <b>Upload Failed</b>\n\n"
            "Sorry, there was an error processing your file. Please try again.",
            parse_mode=ParseMode.HTML
        )


async def my_files_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db, flask_app):
    """Handle /myfiles command"""
    try:
        from models import FileMetadata
        
        user_id = update.effective_user.id
        
        # Query user's files
        with flask_app.app_context():
            files = FileMetadata.query.filter_by(user_id=user_id).order_by(FileMetadata.upload_date.desc()).all()
        
        if not files:
            empty_text = """
📂 <b>Your File Storage is Empty</b>

🌟 <i>Ready to get started?</i>

Upload your first file by sending any document, image, video, or audio file to this chat!

<b>✨ Pro Features:</b>
• Unlimited file types supported
• Instant download access
• Secure cloud storage
• Smart file organization
"""
            keyboard = [
                [InlineKeyboardButton("📤 Upload Your First File", callback_data="upload_guide")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.effective_message.reply_text(
                empty_text,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )
            return
        
        # Create file list with premium styling
        header_text = f"""
📂 <b>Your Premium File Storage</b>

🗂️ <i>Total Files: {len(files)}</i>
📊 <i>Storage Used: {format_file_size(sum(f.file_size or 0 for f in files))}</i>

💎 <b>Select any file to download:</b>
"""
        
        # Create inline keyboard with file buttons (max 20 files per page)
        keyboard = []
        for i, file in enumerate(files[:20]):
            file_emoji = "📄"
            if file.mime_type:
                if file.mime_type.startswith('image/'):
                    file_emoji = "🖼️"
                elif file.mime_type.startswith('video/'):
                    file_emoji = "🎥"
                elif file.mime_type.startswith('audio/'):
                    file_emoji = "🎵"
                elif 'pdf' in file.mime_type:
                    file_emoji = "📋"
            
            # Truncate long filenames for button display
            display_name = file.filename
            if len(display_name) > 25:
                display_name = display_name[:22] + "..."
            
            button_text = f"{file_emoji} {display_name}"
            keyboard.append([
                InlineKeyboardButton(
                    button_text,
                    callback_data=f"dl_{file.id}"
                )
            ])
        
        # Add navigation and utility buttons
        if len(files) > 20:
            keyboard.append([
                InlineKeyboardButton("➡️ Show More Files", callback_data="files_page_2")
            ])
        
        keyboard.append([
            InlineKeyboardButton("📤 Upload New File", callback_data="upload_guide"),
            InlineKeyboardButton("🔄 Refresh", callback_data="my_files")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.effective_message.reply_text(
            header_text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Error in my_files_command: {str(e)}")
        await update.effective_message.reply_text(
            "❌ <b>Error Loading Files</b>\n\n"
            "Sorry, there was an error retrieving your files. Please try again.",
            parse_mode=ParseMode.HTML
        )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, db, flask_app):
    """Handle callback queries from inline buttons"""
    query = update.callback_query
    await query.answer()
    
    try:
        if query.data == "start":
            welcome_text = """
🌟 <b>Welcome to @SAN_mediabot!</b> 🌟

🚀 <i>Your personal cloud storage assistant</i>

<b>✨ What I can do for you:</b>
📁 Store any type of file securely
📋 Keep track of all your uploads
💾 Easy file retrieval anytime
🔍 Smart file management

<b>🎯 Quick Commands:</b>
/myfiles - 📂 View all your files
/start - 🏠 Show this welcome message
/help - ❓ Get detailed help

<b>📤 Getting Started:</b>
Simply send me any file and I'll store it safely for you!

<i>Built with ❤️ for premium experience</i>
"""
            
            keyboard = [
                [
                    InlineKeyboardButton("📂 My Files", callback_data="my_files"),
                    InlineKeyboardButton("❓ Help", callback_data="help")
                ],
                [
                    InlineKeyboardButton("🚀 Upload First File", callback_data="upload_guide")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                welcome_text,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )
        elif query.data == "help":
            help_text = """
🔧 <b>How to Use @SAN_mediabot</b> 🔧

<b>📤 Uploading Files:</b>
• Send any file directly to this chat
• Supported: Documents, Images, Videos, Audio, etc.
• Files are stored securely with metadata

<b>📁 Managing Files:</b>
• Use /myfiles to see all your uploaded files
• Click any file button to download instantly
• Files are organized by upload date

<b>🔍 File Information:</b>
• File name and size are preserved
• Upload timestamp is recorded
• Easy one-click download access

<b>⚡ Pro Tips:</b>
• Send multiple files at once
• Use descriptive filenames for easy identification
• Your files are private and secure

<b>🆘 Need Support?</b>
For any queries contact @takezo_5
"""
            
            keyboard = [
                [
                    InlineKeyboardButton("📂 View My Files", callback_data="my_files"),
                    InlineKeyboardButton("🏠 Home", callback_data="start")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                help_text,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )
        elif query.data == "my_files":
            await my_files_command(update, context, db, flask_app)
        elif query.data == "upload_guide":
            guide_text = """
📤 <b>How to Upload Files</b>

🎯 <i>It's super simple!</i>

<b>Just send me any file:</b>
• 📄 Documents (PDF, DOC, TXT, etc.)
• 🖼️ Images (JPG, PNG, GIF, etc.)
• 🎥 Videos (MP4, AVI, MOV, etc.)
• 🎵 Audio (MP3, WAV, OGG, etc.)
• 🗣️ Voice messages
• 📹 Video notes

<b>✨ Pro Tips:</b>
• Send multiple files at once
• Original quality is preserved
• Instant secure storage
• One-click download later

<i>Ready? Send your first file now! 🚀</i>
"""
            keyboard = [
                [InlineKeyboardButton("📂 View My Files", callback_data="my_files")],
                [InlineKeyboardButton("🏠 Back to Home", callback_data="start")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                guide_text,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )
        elif query.data.startswith("dl_"):
            from models import FileMetadata
            
            record_id = query.data.replace("dl_", "")
            
            # Get file metadata by database ID
            with flask_app.app_context():
                file_metadata = FileMetadata.query.get(int(record_id))
            
            if not file_metadata:
                await query.edit_message_text("❌ File not found or has been deleted.")
                return
            
            # Send the file
            download_text = f"""
💾 <b>Downloading: {file_metadata.filename}</b>

📊 <b>File Info:</b>
🔸 Size: <code>{format_file_size(file_metadata.file_size)}</code>
🔸 Uploaded: <code>{format_date(file_metadata.upload_date)}</code>

⬇️ <i>File sent successfully!</i>
"""
            
            keyboard = [
                [
                    InlineKeyboardButton("📂 Back to Files", callback_data="my_files"),
                    InlineKeyboardButton("📤 Upload New", callback_data="upload_guide")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send the actual file - detect type from file_id or filename
            file_id = file_metadata.file_id
            filename = file_metadata.filename.lower() if file_metadata.filename else ""
            
            # Detect if it's a photo based on file_id pattern or extension
            is_photo = (file_id.startswith('AgAC') or 
                       filename.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')) or
                       (file_metadata.mime_type and file_metadata.mime_type.startswith('image/')))
            
            is_video = (file_id.startswith('BAACAgI') or 
                       filename.endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')) or
                       (file_metadata.mime_type and file_metadata.mime_type.startswith('video/')))
            
            is_audio = (file_id.startswith('AwACAgI') or 
                       filename.endswith(('.mp3', '.wav', '.ogg', '.m4a', '.flac')) or
                       (file_metadata.mime_type and file_metadata.mime_type.startswith('audio/')))
            
            try:
                if is_photo:
                    await context.bot.send_photo(
                        chat_id=query.message.chat.id,
                        photo=file_metadata.file_id,
                        caption=download_text,
                        parse_mode=ParseMode.HTML,
                        reply_markup=reply_markup
                    )
                elif is_video:
                    await context.bot.send_video(
                        chat_id=query.message.chat.id,
                        video=file_metadata.file_id,
                        caption=download_text,
                        parse_mode=ParseMode.HTML,
                        reply_markup=reply_markup
                    )
                elif is_audio:
                    await context.bot.send_audio(
                        chat_id=query.message.chat.id,
                        audio=file_metadata.file_id,
                        caption=download_text,
                        parse_mode=ParseMode.HTML,
                        reply_markup=reply_markup
                    )
                else:
                    # Default to document for all other file types
                    await context.bot.send_document(
                        chat_id=query.message.chat.id,
                        document=file_metadata.file_id,
                        caption=download_text,
                        parse_mode=ParseMode.HTML,
                        reply_markup=reply_markup
                    )
            except Exception as e:
                # If specific method fails, try as document
                logger.error(f"Failed to send file as detected type, trying as document: {e}")
                await context.bot.send_document(
                    chat_id=query.message.chat.id,
                    document=file_metadata.file_id,
                    caption=download_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup
                )
            
            # Update the original message
            await query.edit_message_text(
                f"✅ <b>File Downloaded!</b>\n\n📁 <code>{file_metadata.filename}</code> has been sent to you.",
                parse_mode=ParseMode.HTML
            )
            
    except Exception as e:
        logger.error(f"Error in handle_callback: {str(e)}")
        await query.edit_message_text(
            "❌ <b>Error</b>\n\nSorry, there was an error processing your request."
        )


def setup_bot_handlers(application, database, flask_app):
    """Setup all bot handlers"""
    # Wrap handlers to include database and flask app
    async def start_wrapper(update, context):
        await start_command(update, context)
    
    async def help_wrapper(update, context):
        await help_command(update, context)
    
    async def file_wrapper(update, context):
        await handle_file_upload(update, context, database, flask_app)
    
    async def myfiles_wrapper(update, context):
        await my_files_command(update, context, database, flask_app)
    
    async def callback_wrapper(update, context):
        await handle_callback(update, context, database, flask_app)
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_wrapper))
    application.add_handler(CommandHandler("help", help_wrapper))
    application.add_handler(CommandHandler("myfiles", myfiles_wrapper))
    
    # Handle all types of files
    application.add_handler(MessageHandler(
        filters.Document.ALL | filters.PHOTO | filters.VIDEO | 
        filters.AUDIO | filters.VOICE | filters.VIDEO_NOTE,
        file_wrapper
    ))
    
    # Handle callback queries
    application.add_handler(CallbackQueryHandler(callback_wrapper))
    
    logger.info("Bot handlers setup complete")
