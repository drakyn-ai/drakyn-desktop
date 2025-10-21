# Background Monitor Service

Proactive monitoring service that runs in the background to provide context-aware suggestions.

## What It Does

The background monitor runs continuously (every 30 minutes by default) and:

1. **Gathers Context** - Checks emails, calendar, system state
2. **Analyzes with LLM** - Asks the agent if there are any helpful actions
3. **Generates Suggestions** - Creates proactive suggestions based on user context
4. **Respects Preferences** - Honors quiet hours and user preferences

## Architecture

```
Background Monitor Service (service.py)
  ↓
Gathers Context Snapshot
  ├─ Check emails (via MCP Gmail tool)
  ├─ Check calendar (via MCP Calendar tool) [TODO]
  └─ Check system state (battery, etc.)
  ↓
Read User Context (~/.drakyn/user_context.txt)
  ↓
Call Agent with Combined Context
  ↓
Parse Suggestions from Response
  ↓
Send Notifications (log for now, UI later)
  ↓
Append to Suggestion History (~/.drakyn/suggestion_history.txt)
  ↓
Sleep until next check (30 minutes)
```

## Files

- `service.py` - Main monitoring service
- `requirements.txt` - Python dependencies
- `~/.drakyn/user_context.txt` - User profile managed by agent
- `~/.drakyn/suggestion_history.txt` - Log of all suggestions

## Configuration

Set via environment variables when starting the service:

- `CHECK_INTERVAL_MINUTES` - How often to check (default: 30)
- User preferences read from `user_context.txt`:
  - Quiet hours (e.g., "10pm - 7am")
  - Proactive monitoring enabled/disabled
  - Notification preferences

## Running Standalone

For testing without Electron:

```bash
cd src/services/monitor
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Run with custom check interval (in minutes)
CHECK_INTERVAL_MINUTES=5 python service.py
```

## Running via Electron

The monitor service starts automatically when you launch the Electron app:

```bash
npm start
```

It runs as a background process managed by Electron and stops when you close the app.

## How Suggestions Work

The agent receives a prompt like:

```
You are Drakyn, a proactive AI assistant.

What you know about the user:
[Contents of user_context.txt]

Current situation:
Current Time: 2:45 PM, Wednesday October 20, 2024

Recent Emails:
  - From boss@company.com: Q4 Planning Meeting
  - From school@edu.com: Permission slip due Friday

System State:
  - Battery: 15%

Based on what you know about the user and their current situation,
are there any helpful actions you could take right now?

If you have 1-3 helpful suggestions, respond with:
SUGGESTIONS:
- [Brief description]: [Why this would be helpful]

If nothing urgent right now, respond with:
NO_SUGGESTIONS

Remember: Better to stay quiet than be annoying.
```

The agent responds with suggestions like:

```
SUGGESTIONS:
- Remind about permission slip: Due Friday, mentioned during school pickup
- Suggest charging laptop: Battery at 15%, meeting in 15 minutes
```

## Quiet Hours

The monitor respects quiet hours configured in user_context.txt:

```
Preferences:
- Quiet hours: 10pm - 7am (no notifications)
```

During quiet hours, the monitor sleeps and doesn't generate suggestions.

## Disabling Proactive Monitoring

Add to user_context.txt:

```
Preferences:
- Proactive monitoring: disabled
```

The monitor will check every 5 minutes if it gets re-enabled.

## Logging

Logs go to console (captured by Electron):

```
[Monitor Service]: Starting background monitor service...
[Monitor Service]: === Starting proactive check ===
[Monitor Service]: Gathered context snapshot (245 chars)
[Monitor Service]: Generated 2 suggestions
[Monitor Service]: === SUGGESTIONS ===
[Monitor Service]: 1. Remind about permission slip
[Monitor Service]:    Why: Due Friday, mentioned during school pickup
[Monitor Service]: 2. Suggest charging laptop
[Monitor Service]:    Why: Battery at 15%, meeting in 15 minutes
[Monitor Service]: === Proactive check complete ===
[Monitor Service]: Sleeping for 30 minutes...
```

## Dependencies

- **httpx** - HTTP client for calling MCP and inference servers
- **python-dotenv** - Environment variable management

Both servers (MCP and inference) must be running for the monitor to work.

## Future Enhancements

- [ ] System notifications instead of just logging
- [ ] In-app suggestion panel in UI
- [ ] Calendar integration (Google Calendar tool)
- [ ] More sophisticated preference parsing
- [ ] Learning from user acceptance/dismissal of suggestions
- [ ] Adjustable check frequency based on time of day
- [ ] Context-aware quiet hours (e.g., during meetings)
