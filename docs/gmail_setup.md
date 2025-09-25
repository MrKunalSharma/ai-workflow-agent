# Gmail API Setup Guide

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Gmail API:
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"

## Step 2: Create OAuth2 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Configure OAuth consent screen if needed:
   - Choose "External" for testing
   - Add test users (your email)
4. Application type: "Desktop app"
5. Name: "AI Workflow Agent"
6. Download credentials JSON

## Step 3: Setup Credentials

1. Rename downloaded file to `gmail_credentials.json`
2. Place in `config/` directory
3. Run the app - it will open browser for authentication
4. Authorize access to Gmail
5. Token will be saved automatically

## Testing Without Gmail

If you want to test without setting up Gmail:
- Comment out Gmail-related code in `task_processor.py`
- Use the `/api/test-email` endpoint
- Focus on Notion integration and AI processing

