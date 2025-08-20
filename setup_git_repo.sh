#!/bin/bash

# Git Repository Setup Script
# Run this script locally after downloading the files from Replit

echo "Setting up Git repository for Telegram Bot deployment..."

# Configure Git with your credentials
git config user.email "your-email@example.com"  # Replace with your actual email
git config user.name "Your Name"  # Replace with your actual name

# Add all files to Git
echo "Adding files to repository..."
git add .

# Commit the changes
echo "Committing files..."
git commit -m "Initial commit: Telegram file management bot

✅ Core application files (main.py, bot_handlers.py, models.py)
✅ Configuration files (requirements.txt, render.yaml, Procfile)
✅ Documentation (README.md, deployment guides)
✅ Ready for Render deployment"

# Push to remote repository
echo "Pushing to remote repository..."
git push origin main

echo ""
echo "🎉 Repository setup complete!"
echo ""
echo "Next steps:"
echo "1. Go to render.com"
echo "2. Create new Web Service"
echo "3. Connect your Git repository"
echo "4. Set environment variables:"
echo "   - BOT_TOKEN (your bot token)"
echo "   - DATABASE_URL (PostgreSQL connection)"
echo "   - FLASK_SECRET_KEY (random secret)"
echo "   - RENDER=true"
echo "5. Deploy and test!"
echo ""
echo "Your bot is ready for production! 🚀"