# Gmail Integration - User Guide

## Overview

Drakyn Desktop can read, search, and send emails from your Gmail account. The setup is simple - just sign in with Google!

## Quick Start

### First Time Setup

1. **Ask Drakyn about your email:**
   ```
   You: Can you read my latest email?
   ```

2. **Drakyn will respond:**
   ```
   I need to connect to Gmail first. I'll open your browser
   so you can sign in with Google...
   ```

3. **Your browser will open** to Google's sign-in page

4. **Sign in** with your Google account

5. **Review permissions** and click "Allow"
   - Read your email messages and settings
   - Send email on your behalf
   - Manage drafts and email

6. **Success!** You'll see:
   ```
   Authentication successful! You can close this window.
   ```

7. **Back in Drakyn:**
   ```
   Agent: Successfully connected to Gmail!
   Here's your latest email from John Doe...
   ```

That's it! You're now connected.

## What You Can Do

### Read Email

```
You: Show me my latest email
You: Read my unread emails
You: What emails did I get today?
You: Show me emails from john@example.com
```

### Search Email

```
You: Find emails about "project status"
You: Search for emails from my boss
You: Show me important emails from this week
You: Find the email with "invoice" in the subject
```

### Send Email

```
You: Send an email to jane@example.com saying "Thanks for the update!"
You: Email john@example.com with subject "Meeting Tomorrow" and body "Let's meet at 2pm"
```

## How It Works

### Security & Privacy

- ✅ **Your credentials stay with Google** - Drakyn never sees your password
- ✅ **Standard OAuth 2.0** - The same technology banks and apps use
- ✅ **Token-based access** - Drakyn only gets temporary access tokens
- ✅ **Stored locally** - Your tokens are saved on your computer only
- ✅ **You're in control** - Revoke access anytime from Google Account settings

### What Drakyn Can Access

When you grant permission, Drakyn can:
- ✅ Read your email messages
- ✅ Search your emails
- ✅ Send emails on your behalf
- ✅ Create drafts

Drakyn **cannot**:
- ❌ Access your password
- ❌ Delete emails (read-only access)
- ❌ Access other Google services
- ❌ Work when you revoke access

### Token Management

Your Gmail access is managed through tokens:

- **Access Token**: Valid for ~1 hour, automatically refreshed
- **Refresh Token**: Allows Drakyn to get new access tokens
- **Storage**: Tokens saved in `src/services/mcp/tokens/gmail_token.json`

You won't need to sign in again unless:
- You revoke access in Google Account settings
- The refresh token expires (rare)
- The token file is deleted

## Troubleshooting

### "This app hasn't been verified"

If you see a warning that says "This app hasn't been verified":

1. This is normal for apps in development
2. Click **"Advanced"**
3. Click **"Go to Drakyn (unsafe)"**
4. This is safe - it just means Google hasn't reviewed the app yet

### "Authentication failed"

If authentication fails:

1. **Check your internet connection**
2. **Try again** - The agent will automatically retry
3. **Check browser** - Make sure a browser window opened
4. **Check logs** - Look in `src/services/mcp/logs/mcp_server.log`

### "Access blocked"

If you see "Access blocked: This app's request is invalid":

This means the OAuth credentials haven't been set up yet. Contact the Drakyn maintainer or see [GMAIL_SETUP.md](../src/services/mcp/GMAIL_SETUP.md) for developer setup instructions.

### Token issues

If Drakyn keeps asking you to sign in:

1. **Check token file exists**: `src/services/mcp/tokens/gmail_token.json`
2. **Check permissions**: Make sure the file is readable/writable
3. **Delete and retry**: Delete the token file and authenticate again
4. **Check logs**: Look for errors in the MCP server logs

### Browser doesn't open

If the browser doesn't open automatically:

1. Check the console output for a URL
2. Copy and paste the URL into your browser manually
3. Complete the authentication
4. The agent should detect the successful auth

## Revoking Access

To revoke Drakyn's access to Gmail:

1. Go to [Google Account > Security > Third-party apps](https://myaccount.google.com/permissions)
2. Find "Drakyn Desktop" in the list
3. Click **"Remove access"**
4. Delete the token file: `src/services/mcp/tokens/gmail_token.json`

Drakyn will ask you to sign in again the next time you use Gmail features.

## Advanced Usage

### Email Search Queries

Drakyn supports Gmail's advanced search syntax:

```
You: Find emails with label:important
You: Search for emails after:2024/01/01 before:2024/12/31
You: Show me has:attachment from:boss@example.com
You: Find emails larger:10MB
```

Learn more: [Gmail Search Operators](https://support.google.com/mail/answer/7190)

### Multiple Accounts

Currently, Drakyn supports one Gmail account at a time. To switch accounts:

1. Delete the token file: `src/services/mcp/tokens/gmail_token.json`
2. Ask Drakyn to access Gmail again
3. Sign in with the different account

## Privacy Note

**Your emails stay private:**
- Emails are only accessed when you ask
- Email content is not stored by Drakyn
- Tokens are stored locally on your machine
- No data is sent to external servers (except Google for API calls)

**What the agent sees:**
- The agent processes your emails to answer your questions
- The LLM (language model) may see email content to respond
- If using cloud models (like OpenAI), check their privacy policy
- For maximum privacy, use local models (like Ollama)

## Support

Having issues? Check:
- 📝 Logs: `src/services/mcp/logs/mcp_server.log`
- 🔧 Developer docs: [GMAIL_SETUP.md](../src/services/mcp/GMAIL_SETUP.md)
- 🐛 Issues: [GitHub Issues](https://github.com/drakyn-ai/drakyn-desktop/issues)
