# Proactive Agent - Testing Guide

Complete guide for testing the proactive agent system end-to-end.

## Prerequisites

Before testing, ensure:

1. **Python environment set up**
   - venv created with all dependencies
   - Both inference and MCP servers can start

2. **LLM configured**
   - Either local Ollama model loaded
   - OR cloud API key (Anthropic/OpenAI) configured

3. **Gmail configured (optional but recommended)**
   - OAuth credentials set up
   - Gmail tool working

## Quick Start Testing

### 1. Start the Application

```bash
cd drakyn-desktop
npm start
```

This automatically starts:
- Electron UI
- Inference server (port 8000)
- MCP server (port 8001)
- IPC server (port 9999)
- Background monitor service

### 2. Verify Services Running

Check Electron console for:
```
[IPC Server] Listening on http://127.0.0.1:9999
[MCP Server]: INFO: Started server process
[Inference Server]: INFO: Started server process
[Monitor Service]: Background monitor initialized with 30min interval
```

### 3. Test Manual Notification

**Method 1: Direct HTTP test**

```bash
curl -X POST http://localhost:9999/notify \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Suggestion",
    "body": "This is a test proactive suggestion",
    "data": {
      "action": "Test action",
      "reasoning": "Testing the notification system"
    }
  }'
```

**Expected:**
- System notification appears
- In-app suggestion panel shows the suggestion
- Badge shows "1" in header

### 4. Test User Context Tool

```bash
# Read user context
curl -X POST http://localhost:8001/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "user_context",
    "arguments": {"action": "read"}
  }'

# Update user context
curl -X POST http://localhost:8001/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "user_context",
    "arguments": {
      "action": "update",
      "content": "About the User:\n- Testing proactive agent\n- Preferences: Enable notifications"
    }
  }'
```

**Expected:**
- File created/updated at `~/.drakyn/user_context.txt`
- Can read back the content

## Full Flow Testing

### Test 1: Background Monitoring (Shortened Interval)

For faster testing, reduce check interval:

1. **Temporarily modify check interval:**

```bash
# Edit src/services/monitor/service.py
# Change check_interval_minutes default to 2 (2 minutes instead of 30)
```

2. **Restart the app:**

```bash
npm start
```

3. **Monitor logs:**

Watch for:
```
[Monitor Service]: === Starting proactive check ===
[Monitor Service]: Gathered context snapshot (X chars)
[Monitor Service]: Generated N suggestions
[Monitor Service]: === Proactive check complete ===
```

4. **Check for suggestions:**

- System notification should appear (if suggestions generated)
- In-app panel should update
- History file: `~/.drakyn/suggestion_history.txt`

**Expected Timeline:**
- Check 1 (2 min): Suggestions if context interesting
- Check 2 (4 min): More suggestions
- Check 3 (6 min): Learning question (every 3rd check)

### Test 2: Learning System

The agent asks questions every 3rd check (90 minutes at default interval).

**To test quickly:**

1. Set check interval to 2 minutes
2. Wait for 3 checks (6 minutes)
3. Look for learning question notification

**Expected:**
- Title: "Drakyn wants to learn"
- Body: A conversational question
- Type: learning_question in data

**Check logs:**
```
[Monitor Service]: Checking if should ask learning question...
[Monitor Service]: Asked learning question: [question]
```

**Verify:**
- Question logged to `~/.drakyn/questions_asked.txt`
- Max 3 questions per day

### Test 3: Quiet Hours

**Setup:**

1. Go to Settings page
2. Set quiet hours: current time to 1 hour from now
3. Save settings

**Expected:**
- Monitor service skips checks during quiet hours
- Log: "Currently in quiet hours. Skipping this check."
- No notifications during this time

### Test 4: Enable/Disable Monitoring

**In Settings:**

1. Uncheck "Enable proactive monitoring"
2. Save settings
3. Update `user_context.txt`:
   ```
   Preferences:
   - Proactive monitoring: disabled
   ```

**Expected:**
- Monitor service sleeps
- Log: "Proactive monitoring is disabled. Sleeping..."
- Checks every 5 minutes if re-enabled

**Re-enable:**

1. Check the box again
2. Update context file to "enabled"

### Test 5: Suggestion Interaction

1. **Generate a suggestion** (via manual test or wait for real one)

2. **Click notification:**
   - App should focus
   - Suggestion panel should open

3. **In suggestion panel:**
   - Click "Accept" on a suggestion
   - Click "Dismiss" on another

**Expected:**
- Buttons work
- Status changes to "Accepted" / "Dismissed"
- Buttons disappear after action
- Badge count updates

4. **Check logs:**

```bash
cat ~/.drakyn/suggestion_history.txt
```

Should show:
```
[2024-10-20 14:30] SUGGESTED: [action]
  REASONING: [reason]
  STATUS: pending
```

### Test 6: Gmail Integration

**Prerequisites:**
- Gmail OAuth configured
- Gmail tool working

**Test:**

1. **Send yourself an email** with subject "TEST PROACTIVE AGENT"

2. **Wait for next check** (or restart with 2-min interval)

3. **Monitor logs:**
```
[Monitor Service]: Recent Emails:
[Monitor Service]:   - From: you@example.com: TEST PROACTIVE AGENT
```

4. **Expected suggestion:**

Agent might suggest:
- "You have a new email from yourself about testing. Would you like me to read it?"
- Or similar, depending on agent's analysis

## Edge Cases & Error Scenarios

### Test: No Suggestions

If agent decides nothing is helpful:

**Expected:**
- Log: "No suggestions generated (agent decided nothing helpful right now)"
- No notification
- No error

### Test: Tool Errors

**Simulate Gmail error:**

1. Rename OAuth token file temporarily
2. Wait for check

**Expected:**
- Log: "Failed to check emails: [error]"
- Monitor continues working
- Uses context from other sources

### Test: IPC Server Down

**Stop IPC server:**

1. In main.js, comment out IPC server start
2. Restart app

**Expected:**
- Monitor tries to send notifications
- Falls back to logging
- No crash

## Performance Testing

### Memory Usage

```bash
# Monitor process memory
ps aux | grep "python.*monitor"
```

**Expected:** <100MB for monitor service

### Response Time

Check logs for timing:
```
[Monitor Service]: === Proactive check complete ===
```

**Expected:** 5-15 seconds per check (depending on LLM)

## Verification Checklist

After all tests:

- [ ] Background monitor runs continuously
- [ ] Checks happen at configured interval
- [ ] System notifications appear
- [ ] In-app panel shows suggestions
- [ ] Accept/dismiss buttons work
- [ ] Learning questions asked (max 3/day)
- [ ] Quiet hours respected
- [ ] Enable/disable toggle works
- [ ] Settings persist across restarts
- [ ] Gmail monitoring works (if configured)
- [ ] User context file updates
- [ ] Suggestion history logged
- [ ] No memory leaks
- [ ] No crashes

## Troubleshooting

### No suggestions appearing

**Check:**
1. Is monitor service running? (look for logs)
2. Is IPC server running? (port 9999)
3. Is user_context.txt readable?
4. Check quiet hours settings

### Notifications not showing

**Check:**
1. System notification permissions (OS level)
2. Electron notification API working
3. IPC server receiving requests
4. Browser console for errors

### Learning questions not asked

**Check:**
1. Questions logged? `~/.drakyn/questions_asked.txt`
2. Already hit daily limit (3)?
3. Check counter (every 3rd check)
4. Check logs for "should ask learning question"

### Settings not persisting

**Check:**
1. localStorage in browser console
2. user_context.txt file manually
3. File permissions on ~/.drakyn/

## Advanced Testing

### Stress Test

**Rapid interval:**

1. Set check interval to 1 minute
2. Run for 30 minutes
3. Monitor memory/CPU
4. Check for crashes

**Expected:**
- Stable performance
- No memory growth
- All suggestions logged

### Multi-Day Test

1. Leave running overnight
2. Check suggestion_history.txt next day
3. Verify quiet hours worked
4. Check question count (max 3/day)

## Test Data Cleanup

After testing:

```bash
# Clear test data
rm ~/.drakyn/suggestion_history.txt
rm ~/.drakyn/questions_asked.txt

# Reset user context (keep template)
# Edit ~/.drakyn/user_context.txt manually

# Clear UI state
# Open DevTools > Application > Local Storage > Clear
```

## Success Criteria

System is working correctly if:

1. ✅ Monitor runs continuously without crashes
2. ✅ Suggestions appear based on context
3. ✅ Notifications delivered reliably
4. ✅ UI responds to user actions
5. ✅ Learning system asks relevant questions
6. ✅ Settings control behavior
7. ✅ Quiet hours respected
8. ✅ History logged correctly
9. ✅ Performance acceptable (<100MB RAM)
10. ✅ No data loss or corruption

## Known Limitations

Current version:

- Calendar integration is placeholder only
- Cannot handle learning question answers yet (manual context update)
- Settings don't restart monitor service automatically
- No analytics/metrics dashboard
- Suggestion quality depends on LLM model

## Next Steps After Testing

If all tests pass:

1. Document any issues found
2. Tune check interval for production use (30-60 min recommended)
3. Set up Gmail if not already done
4. Customize user_context.txt with real information
5. Use in daily workflow
6. Collect feedback for improvements
