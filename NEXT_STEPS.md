# Next Steps - Gmail OAuth Implementation

## Completed ✓

- ✅ Refactored Gmail tool to use browser-based OAuth
- ✅ Implemented automatic token refresh
- ✅ Added environment variable support for credentials
- ✅ Created comprehensive documentation
- ✅ Updated dependencies
- ✅ Added .gitignore entries for tokens

## Required: Set Up OAuth Credentials

Before testing, you need to create Google OAuth credentials:

### Quick Start (5 minutes)

1. **Go to Google Cloud Console:**
   https://console.cloud.google.com

2. **Create/Select Project:**
   - Create new project "Drakyn Desktop" or select existing

3. **Enable Gmail API:**
   - Go to APIs & Services > Library
   - Search "Gmail API"
   - Click Enable

4. **Configure OAuth Consent Screen:**
   - Go to OAuth consent screen
   - Choose "External"
   - Fill in app name: "Drakyn Desktop"
   - Add your email
   - Add scopes:
     - `gmail.readonly`
     - `gmail.send`
     - `gmail.compose`
   - Save

5. **Create OAuth Client:**
   - Go to Credentials > Create Credentials > OAuth client ID
   - Type: Desktop app
   - Name: Drakyn Desktop Client
   - Download JSON or copy credentials

6. **Add to Project:**

   **Option A: Environment Variables (Recommended)**
   ```bash
   cd src/services/mcp
   cp .env.example .env
   # Edit .env and add:
   # GOOGLE_CLIENT_ID=your_id.apps.googleusercontent.com
   # GOOGLE_CLIENT_SECRET=your_secret
   ```

   **Option B: Hardcode (Dev Only)**
   Edit `src/services/mcp/tools/gmail.py` lines 34-35

7. **Restart MCP Server:**
   ```bash
   cd src/services/mcp
   python3 server.py
   ```

**Detailed guide:** See `src/services/mcp/GMAIL_SETUP.md`

## Testing Plan

### 1. Unit Test - Direct Tool Call

Test the Gmail tool directly:

```bash
# Terminal 1: Start MCP server
cd src/services/mcp
python3 server.py

# Terminal 2: Test authentication
curl -X POST http://localhost:8001/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "gmail",
    "arguments": {"action": "authenticate"}
  }'
```

**Expected:**
- Browser opens to Google sign-in
- After allowing access, returns:
  ```json
  {
    "result": {
      "action": "authenticate",
      "success": true,
      "message": "Successfully authenticated with Gmail!"
    }
  }
  ```
- Token file created at: `src/services/mcp/tokens/gmail_token.json`

### 2. Integration Test - Search Email

```bash
curl -X POST http://localhost:8001/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "gmail",
    "arguments": {
      "action": "search",
      "query": "in:inbox",
      "max_results": 5
    }
  }'
```

**Expected:**
- Returns list of 5 most recent emails
- Each with: id, subject, from, date, snippet

### 3. End-to-End Test - Agent Chat

```bash
# Terminal 1: Start inference server
cd src/services/inference
./venv/bin/python server.py  # or venv\Scripts\python.exe on Windows

# Terminal 2: Start MCP server
cd src/services/mcp
python3 server.py

# Terminal 3: Test via CLI
cd ../..
./drakyn chat
# Then type: "Can you read my latest email?"
```

**Expected:**
- Agent recognizes Gmail is needed
- Browser opens (if first time)
- Agent searches for latest email
- Agent reads the email
- Agent responds with email content

### 4. CLI Test - Direct Usage

```bash
./drakyn chat
# Try these commands:
```

1. `Read my latest email`
2. `Show me emails from today`
3. `Find unread emails`
4. `Send email to test@example.com saying "Test message"`

### 5. Token Persistence Test

```bash
# 1. Authenticate (browser opens)
curl -X POST http://localhost:8001/execute \
  -H "Content-Type: application/json" \
  -d '{"tool": "gmail", "arguments": {"action": "authenticate"}}'

# 2. Restart MCP server
# Kill and restart: python3 src/services/mcp/server.py

# 3. Try to search (should NOT open browser)
curl -X POST http://localhost:8001/execute \
  -H "Content-Type: application/json" \
  -d '{"tool": "gmail", "arguments": {"action": "search", "query": "in:inbox"}}'
```

**Expected:** No browser opens, uses saved token

### 6. Token Refresh Test

```bash
# 1. Manually expire the access token
# Edit tokens/gmail_token.json and change "expiry" to past date

# 2. Make a request
curl -X POST http://localhost:8001/execute \
  -H "Content-Type: application/json" \
  -d '{"tool": "gmail", "arguments": {"action": "search", "query": "in:inbox"}}'

# 3. Check logs
tail -f src/services/mcp/logs/mcp_server.log
```

**Expected:**
- Log shows: "Refreshing expired Gmail credentials"
- Request succeeds without browser opening
- Token file updated with new expiry

## Troubleshooting

### "Access blocked: This app's request is invalid"
- Check OAuth consent screen is configured
- Verify scopes are correct
- Make sure Gmail API is enabled

### "This app hasn't been verified"
- Normal for development
- Click "Advanced" > "Go to Drakyn (unsafe)"
- For production: Submit for Google verification

### Browser doesn't open
- Check firewall settings
- Look for URL in console output
- Manually open the URL if needed

### Token not persisting
- Check directory exists: `src/services/mcp/tokens/`
- Check write permissions
- Look for errors in logs: `src/services/mcp/logs/mcp_server.log`

### Authentication loops
- Delete token file: `rm src/services/mcp/tokens/gmail_token.json`
- Try authenticating again
- Check for errors in logs

## Production Checklist

Before deploying to users:

- [ ] OAuth credentials created and configured
- [ ] Environment variables set (not hardcoded)
- [ ] Tested on all platforms (Mac, Windows, Linux)
- [ ] Token directory created with correct permissions
- [ ] .gitignore entries prevent token commit
- [ ] Documentation reviewed and accurate
- [ ] Error messages are user-friendly
- [ ] Logs don't expose sensitive data
- [ ] (Optional) Submit app for Google verification

## Future Enhancements

### Priority
1. **Multi-account support** - Allow switching between Gmail accounts
2. **Attachment handling** - Download and view email attachments
3. **HTML rendering** - Display HTML emails properly
4. **Draft support** - Save and send drafts

### Nice-to-Have
1. **Label management** - Add/remove Gmail labels
2. **Calendar integration** - Access Google Calendar
3. **Drive integration** - Access Google Drive files
4. **Contacts integration** - Access Google Contacts
5. **Batch operations** - Archive/delete multiple emails

## Questions/Issues?

- **Developer Guide:** `src/services/mcp/GMAIL_SETUP.md`
- **User Guide:** `docs/GMAIL_INTEGRATION.md`
- **Implementation Details:** `IMPLEMENTATION_SUMMARY.md`

## Summary

**Status:** ✅ Implementation complete, ready for OAuth credential setup and testing

**What's needed:**
1. Create Google OAuth credentials (5 minutes)
2. Add credentials to `.env` file
3. Run tests
4. Start using!

**Time to production:**
- Setup: 5 minutes
- Testing: 15 minutes
- **Total: ~20 minutes**
