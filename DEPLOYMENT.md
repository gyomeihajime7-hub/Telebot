# Deployment Guide for Telegram File Management Bot

## GitHub Repository Setup

Since git operations are restricted in this environment, here's how to manually create your GitHub repository:

### Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `telegram-file-bot`
3. Description: `Premium Telegram file management bot with PostgreSQL storage`
4. Make it Public (recommended for easier deployment)
5. Initialize with README: NO (we have our own)
6. Click "Create repository"

### Step 2: Upload Files to GitHub

Upload these files to your new repository:

**Essential Files:**
- `main.py` - Main application file
- `bot_handlers.py` - Telegram bot handlers
- `models.py` - Database models
- `Procfile` - Render deployment config
- `render.yaml` - Render service configuration
- `pyproject.toml` - Python dependencies
- `.env.example` - Environment template
- `README.md` - Documentation
- `.gitignore` - Git ignore rules

**Optional Files:**
- `replit.md` - Project documentation (for reference)

### Step 3: Render Web Service Deployment

1. Go to https://render.com
2. Sign up/login and connect your GitHub account
3. Click "New" → "Web Service"
4. Connect your `telegram-file-bot` repository
5. Configure deployment settings:

**Basic Settings:**
- Name: `telegram-file-bot`
- Region: Choose closest to your users
- Branch: `main`
- Runtime: `Python 3`

**Build Settings:**
- Build Command: `pip install -r requirements.txt` (auto-detected)
- Start Command: `python main.py` (from Procfile)

**Environment Variables:**
Add these in Render dashboard:
```
BOT_TOKEN=your_telegram_bot_token_from_botfather
DATABASE_URL=your_postgresql_database_url
FLASK_SECRET_KEY=your_random_secret_key_for_sessions
```

### Step 4: Database Setup

**Option 1: Neon PostgreSQL (Recommended)**
1. Go to https://neon.tech
2. Create free account
3. Create new project
4. Copy connection string to `DATABASE_URL`

**Option 2: Render PostgreSQL**
1. In Render dashboard, create "PostgreSQL" service
2. Copy connection string to `DATABASE_URL`

### Step 5: Get Bot Token

1. Message @BotFather on Telegram
2. Use `/newbot` command
3. Choose bot name and username
4. Copy the token to `BOT_TOKEN` environment variable

### Step 6: Deploy

1. Click "Deploy" in Render
2. Wait for build to complete
3. Your bot will be live!

## Verification Steps

1. Check Render logs for "Application started" message
2. Test bot with `/start` command
3. Upload a test file
4. Use `/myfiles` to verify storage works

## Configuration Files Explained

### Procfile
```
web: python main.py
```
Tells Render how to start your application.

### render.yaml
```yaml
services:
  - type: web
    name: telegram-file-bot
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python main.py
```
Alternative deployment configuration.

### pyproject.toml
Contains all Python dependencies:
- flask
- python-telegram-bot
- psycopg2-binary
- sqlalchemy
- And more...

## Environment Variables Details

- `BOT_TOKEN`: Get from @BotFather on Telegram
- `DATABASE_URL`: PostgreSQL connection string
- `FLASK_SECRET_KEY`: Random string for session security
- `PORT`: Automatically set by Render (5000)

## Troubleshooting

**Bot not responding:**
- Check Render logs for errors
- Verify BOT_TOKEN is correct
- Ensure webhook is not set elsewhere

**Database errors:**
- Verify DATABASE_URL format
- Check database service is running
- Ensure connection limits not exceeded

**Build failures:**
- Check pyproject.toml syntax
- Verify all dependencies are available
- Review Render build logs

## Support

Your bot includes:
- Health check endpoint at `/`
- Premium UI with inline keyboards
- File type detection and proper downloads
- Error handling and duplicate prevention
- Support for files up to 2GB

Ready for production deployment on Render!