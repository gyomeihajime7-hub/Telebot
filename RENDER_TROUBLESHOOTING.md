# Render Deployment Troubleshooting for @SAN_mediabot

## Step 1: Check Render Logs
Go to your Render dashboard → Your service → Logs and look for:

**✅ Success messages to look for:**
- "Running on Render - starting both Flask and Telegram bot"
- "Bot token found: 8453661836..."
- "Starting Telegram bot polling..."
- "Application started"

**❌ Error messages to watch for:**
- "BOT_TOKEN environment variable is required"
- "No database URL found"
- "Error starting bot:"
- Any Python traceback errors

## Step 2: Test Environment Variables
Visit your deployed app URL + `/debug` to check:
- `https://your-app-name.onrender.com/debug`

Should show:
```json
{
  "bot_token_set": true,
  "database_url_set": true,
  "flask_secret_set": true,
  "render_env": true,
  "port": "10000"
}
```

## Step 3: Verify Environment Variables in Render
In Render Dashboard → Your Service → Environment:

1. **BOT_TOKEN**: `8453661836:AAFijylDj1AA9RslUQcN_bpdsjCJXiFCtPo`
2. **DATABASE_URL**: `postgresql://neondb_owner:npg_Op9lFnth6iBT@ep-still-wave-a29xvy8f.eu-central-1.aws.neon.tech/neondb?sslmode=require`

## Step 4: Common Issues & Solutions

### Issue: Bot token not working
**Solution**: Double-check the bot token with @BotFather:
- Send `/mybots` to @BotFather
- Select your bot
- Get fresh API token

### Issue: Database connection fails
**Solution**: Test database connectivity:
- The Neon database should be accessible from Render
- Verify the connection string format

### Issue: Bot starts but doesn't respond
**Solutions**:
1. Check if bot is set to private/public in @BotFather
2. Send `/start` to your bot on Telegram
3. Check Render logs for HTTP requests from Telegram

### Issue: Render service stops/crashes
**Solutions**:
1. Check memory usage (free plan has limits)
2. Look for Python errors in logs
3. Verify requirements.txt has all dependencies

## Step 5: Test Bot Functionality
After fixing issues:
1. Find your bot on Telegram
2. Send `/start` command
3. Upload a test file
4. Check if file gets stored and message deleted

## Step 6: Monitor Render Logs
Keep Render logs open while testing to see:
- HTTP requests from Telegram
- Bot response processing
- Any error messages

## Emergency Fixes

### If bot still not working:
1. **Check bot username**: Make sure you're messaging the correct bot
2. **Restart Render service**: Manual restart sometimes helps
3. **Verify bot is not running elsewhere**: Only one instance should run
4. **Test with simple message**: Try `/start` first before file uploads

### If database issues:
1. **Create new Render PostgreSQL**: Use Render's built-in database
2. **Update DATABASE_URL**: Use the new connection string
3. **Redeploy**: Let database tables get created

## Contact Support
If issues persist, contact @takezo_5 with:
- Render logs (copy/paste the error messages)
- Environment variables status from `/debug` endpoint
- Specific error behavior you're seeing