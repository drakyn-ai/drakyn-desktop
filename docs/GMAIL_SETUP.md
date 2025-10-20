# Gmail Integration Setup Guide

This guide explains how to set up Gmail access for your Drakyn AI agent.

## Prerequisites

- Google account with Gmail access
- Google Cloud Console access

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click "Select a project" → "New Project"
3. Enter project name (e.g., "Drakyn Gmail Agent")
4. Click "Create"

## Step 2: Enable Gmail API

1. In your project, go to "APIs & Services" → "Library"
2. Search for "Gmail API"
3. Click on it and press "Enable"

## Step 3: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - Choose "External" user type
   - Fill in required fields:
     - App name: "Drakyn"
     - User support email: your email
     - Developer contact: your email
   - Click "Save and Continue"
   - Add scopes (optional for now)
   - Add test users: your email
   - Click "Save and Continue"

4. Back to credentials, click "Create Credentials" → "OAuth client ID"
5. Choose "Desktop app" as application type
6. Name it "Drakyn Desktop"
7. Click "Create"

## Step 4: Download and Install Credentials

1. Click the download icon (⬇) next to your newly created OAuth client
2. This downloads a JSON file (usually named like `client_secret_XXXXX.json`)
3. Rename it to `gmail_credentials.json`
4. Move it to: `src/services/mcp/credentials/gmail_credentials.json`

## Step 5: Test the Integration

1. Start the MCP server:
   ```bash
   cd src/services/mcp
   python server.py
   ```

2. The agent can now use Gmail commands like:
   - "Show me my unread emails"
   - "Search for emails from john@example.com"
   - "Send an email to alice@example.com"

## First-Time OAuth Flow

The first time the agent tries to use Gmail:

1. A browser window will automatically open
2. Sign in to your Google account
3. Grant permissions to Drakyn
4. The browser will show "Authentication successful"
5. You can close the browser window

Future uses won't require this - the token is saved automatically.

## Troubleshooting

### "Gmail credentials not found" error

- Make sure `gmail_credentials.json` is in `src/services/mcp/credentials/`
- Check the file name is exactly `gmail_credentials.json`

### "OAuth 2.0 authentication failed"

- Delete `token.json` if it exists
- Try the OAuth flow again
- Make sure your email is added as a test user in OAuth consent screen

### "Permission denied" errors

- In Google Cloud Console, go to OAuth consent screen
- Add yourself as a test user
- Make sure Gmail API is enabled

## Privacy & Security

- Your Gmail credentials stay on your local machine
- Tokens are stored locally in `src/services/mcp/credentials/`
- The agent can only access Gmail when you explicitly ask it to
- You can revoke access anytime in your [Google Account settings](https://myaccount.google.com/permissions)

## Scopes Used

The Gmail integration requests these permissions:
- `https://www.googleapis.com/auth/gmail.readonly` - Read emails
- `https://www.googleapis.com/auth/gmail.send` - Send emails
- `https://www.googleapis.com/auth/gmail.modify` - Modify labels

You can review and revoke these anytime in your Google Account.
