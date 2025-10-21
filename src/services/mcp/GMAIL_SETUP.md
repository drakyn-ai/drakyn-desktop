# Gmail OAuth Setup for Drakyn Desktop

This document explains how to set up OAuth credentials for the Gmail integration in Drakyn Desktop.

## Overview

Drakyn Desktop uses **browser-based OAuth** for Gmail authentication. This means:
- ✅ Users just sign in with Google (like any email app)
- ✅ No manual credential management needed
- ✅ Secure and standard OAuth 2.0 flow
- ✅ Works out of the box once credentials are configured

## One-Time Setup (For Developers/Maintainers)

You need to create OAuth credentials **once** for the Drakyn Desktop application. These credentials will be shared by all users of the app.

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project called "Drakyn Desktop" (or use existing)
3. Select the project

### Step 2: Enable Gmail API

1. Go to **APIs & Services > Library**
2. Search for "Gmail API"
3. Click **Enable**

### Step 3: Configure OAuth Consent Screen

1. Go to **APIs & Services > OAuth consent screen**
2. Choose **External** (unless you have Google Workspace)
3. Fill in the required fields:
   - App name: **Drakyn Desktop**
   - User support email: Your email
   - Developer contact email: Your email
4. Click **Save and Continue**
5. On the Scopes page, click **Add or Remove Scopes**
6. Add these scopes:
   - `https://www.googleapis.com/auth/gmail.readonly` (Read email)
   - `https://www.googleapis.com/auth/gmail.send` (Send email)
   - `https://www.googleapis.com/auth/gmail.compose` (Compose email)
7. Click **Save and Continue**
8. Click **Back to Dashboard**

### Step 4: Create OAuth Client ID

1. Go to **APIs & Services > Credentials**
2. Click **Create Credentials > OAuth client ID**
3. Choose **Desktop app** as application type
4. Name it "Drakyn Desktop Client"
5. Click **Create**
6. You'll see a dialog with your **Client ID** and **Client Secret**
7. **Download the JSON** or copy the credentials

### Step 5: Add Credentials to Code

Edit `src/services/mcp/tools/gmail.py` and update the `OAUTH_CLIENT_CONFIG`:

```python
OAUTH_CLIENT_CONFIG = {
    "installed": {
        "client_id": "YOUR_ACTUAL_CLIENT_ID.apps.googleusercontent.com",
        "client_secret": "YOUR_ACTUAL_CLIENT_SECRET",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "redirect_uris": ["http://localhost"]
    }
}
```

**Note:** For production, you should move these to environment variables or a secure config file.

### Step 6: Publish Your App (Optional but Recommended)

While in "Testing" mode, only users you explicitly add can use the app. To make it available to everyone:

1. Go to **OAuth consent screen**
2. Click **Publish App**
3. Submit for verification (recommended for public distribution)

During testing, you can add test users:
1. Go to **OAuth consent screen > Test users**
2. Add email addresses of users who should be able to test

## Security Notes

### Why Client Credentials Are Public in Desktop Apps

For desktop applications, the OAuth client secret is **not actually secret**:
- It's embedded in the app code
- Users can extract it from the binary
- This is **normal and expected** by Google

Security comes from:
- ✅ **User consent** - Users must explicitly grant permission
- ✅ **Redirect URI validation** - Only localhost redirects are allowed
- ✅ **Token-based auth** - Each user gets their own access/refresh tokens
- ✅ **Scope restrictions** - App can only do what user approved

### Token Storage

User tokens are stored locally at:
- Location: `src/services/mcp/tokens/gmail_token.json`
- Contains: User's access token and refresh token (NOT client credentials)
- Permissions: Should be readable only by the user

## User Experience

Once set up, users will experience:

1. **First time:** "Can you read my latest email?"
2. **Agent response:** "I need to connect to Gmail. I'll open your browser..."
3. **Browser opens** to Google sign-in
4. **User signs in** and clicks "Allow"
5. **Browser shows:** "Authentication successful! You can close this window."
6. **Agent:** "Successfully connected! Here's your latest email..."
7. **Future requests:** Work automatically (no re-authentication needed)

Tokens are automatically refreshed when they expire.

## Troubleshooting

### "Access blocked: This app's request is invalid"
- Make sure you've enabled the Gmail API
- Check that your OAuth consent screen is configured
- Verify the scopes match what's in the code

### "This app hasn't been verified"
- If in testing mode, add the user as a test user
- Or click "Advanced > Go to Drakyn (unsafe)" - this is safe for your own app
- For production, submit for Google verification

### "No browser opened"
- Check firewall settings
- Make sure port is available
- Check logs for specific error messages

### Tokens not persisting
- Check write permissions on `src/services/mcp/tokens/` directory
- Look for errors in the MCP server logs

## Environment Variables (Alternative)

For better security, you can use environment variables instead of hardcoding:

```bash
# In .env file
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret
```

Then update the code to read from environment:

```python
import os

OAUTH_CLIENT_CONFIG = {
    "installed": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        # ... rest of config
    }
}
```

## References

- [Google OAuth 2.0 for Desktop Apps](https://developers.google.com/identity/protocols/oauth2/native-app)
- [Gmail API Python Quickstart](https://developers.google.com/gmail/api/quickstart/python)
- [OAuth 2.0 Scopes for Google APIs](https://developers.google.com/identity/protocols/oauth2/scopes#gmail)
