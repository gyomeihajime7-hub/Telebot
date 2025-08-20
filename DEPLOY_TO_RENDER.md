# Deploy Telegram Bot to Render

## Files Required for Deployment

Copy these files to your Git repository:

### Core Application Files
- `main.py` - Main application entry point
- `bot_handlers.py` - Telegram bot command handlers  
- `models.py` - Database models

### Configuration Files
- `render_requirements.txt` → rename to `requirements.txt` 
- `render.yaml` - Render service configuration
- `Procfile` - Process configuration for Render
- `.gitignore` - Git ignore rules

### Documentation (Optional)
- `README.md` - Project documentation
- `DEPLOYMENT.md` - Deployment guide
- `RENDER_TROUBLESHOOTING.md` - Troubleshooting guide

## Git Repository Setup

1. **Create a new repository** on GitHub/GitLab
2. **Clone the repository** to your local machine:
   ```bash
   git clone <your-repo-url>
   cd <your-repo-name>
   ```

3. **Copy the required files** to your local repository folder

4. **Rename render_requirements.txt to requirements.txt**:
   ```bash
   mv render_requirements.txt requirements.txt
   ```

5. **Commit and push**:
   ```bash
   git add .
   git commit -m "Initial commit - Telegram file management bot"
   git push origin main
   ```

## Render Deployment

1. **Connect to Render**:
   - Go to [render.com](https://render.com)
   - Sign up/Login
   - Click "New +" → "Web Service"
   - Connect your Git repository

2. **Configure Environment Variables** in Render Dashboard:
   - `BOT_TOKEN` = Your Telegram bot token from @BotFather
   - `DATABASE_URL` = Your PostgreSQL database URL
   - `FLASK_SECRET_KEY` = Random secret key for sessions
   - `RENDER` = true

3. **Deploy**:
   - Render will automatically deploy using the `render.yaml` configuration
   - Check logs for any errors
   - Test the bot by visiting `/health` endpoint

## Environment Variables Setup

### BOT_TOKEN
Get from @BotFather on Telegram:
1. Message @BotFather
2. Send `/newbot` or `/mybots`
3. Copy the token that looks like: `123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`

### DATABASE_URL  
Options:
- **Neon** (recommended): Get free PostgreSQL from neon.tech
- **Render PostgreSQL**: Add PostgreSQL add-on in Render
- **Supabase**: Get free PostgreSQL from supabase.com

Format: `postgresql://username:password@host:port/database`

### FLASK_SECRET_KEY
Generate a random string:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Testing After Deployment

1. Visit your app URL + `/health` - should show bot status
2. Find your bot on Telegram
3. Send `/start` command
4. Upload a test file
5. Check if file metadata is stored

## Troubleshooting

- Check Render logs for Python errors
- Verify all environment variables are set
- Test database connection
- Confirm bot token is valid with @BotFather