# Logging Configuration

All servers log to both console (terminal) and rotating log files for easy debugging.

## Log Locations

### Inference Server Logs
**Path**: `src/services/inference/logs/inference_server.log`

Contains logs from:
- Model loading and management
- Agent orchestration (`[AGENT]` prefix)
- MCP tool execution (`[MCP]` prefix)
- Timing information (`[TIMING]` prefix)
- LiteLLM/vLLM operations

### MCP Server Logs
**Path**: `src/services/mcp/logs/mcp_server.log`

Contains logs from:
- Tool execution requests
- Gmail, file search, and other tool operations
- Credential management
- Tool registration

## Log Rotation

- **Max file size**: 10MB per log file
- **Backup count**: 5 files (keeps last 50MB of logs)
- **Format**: `HH:MM:SS.mmm - logger_name - LEVEL - message`

When a log file reaches 10MB, it's automatically renamed to:
- `inference_server.log.1`
- `inference_server.log.2`
- ... up to `.5`

The oldest file is deleted when a new backup is created.

## Searching Logs

### By Component
```bash
# Agent reasoning and flow
grep "\[AGENT\]" src/services/inference/logs/inference_server.log

# Tool execution via MCP
grep "\[MCP\]" src/services/inference/logs/inference_server.log

# Performance metrics
grep "\[TIMING\]" src/services/inference/logs/inference_server.log

# All errors
grep "ERROR" src/services/inference/logs/inference_server.log
```

### By Time Range
```bash
# Last 100 lines
tail -n 100 src/services/inference/logs/inference_server.log

# Follow in real-time
tail -f src/services/inference/logs/inference_server.log

# Specific time (HH:MM:SS format)
grep "14:30:" src/services/inference/logs/inference_server.log
```

### By Tool or Feature
```bash
# Gmail operations
grep -i "gmail" src/services/mcp/logs/mcp_server.log

# Setup-required errors
grep "setup_required" src/services/inference/logs/inference_server.log

# Tool results
grep "Tool result" src/services/inference/logs/inference_server.log
```

## Example: Debugging Agent Conversation

To trace a complete agent conversation:

```bash
# Find all logs from a specific minute
grep "14:30:" src/services/inference/logs/inference_server.log | grep "\[AGENT\]\|\[MCP\]"
```

This will show:
1. Agent initialization
2. Each iteration with context state
3. Tool calls and their arguments
4. Tool results (including setup_required flags)
5. Final answers or errors

## Viewing Logs in Real-Time

When developing, keep logs open in separate terminal:

**Terminal 1 - Inference Server:**
```bash
cd src/services/inference
tail -f logs/inference_server.log
```

**Terminal 2 - MCP Server (if running separately):**
```bash
cd src/services/mcp
tail -f logs/mcp_server.log
```

**Terminal 3 - Run the app:**
```bash
npm run dev
```

This gives you live visibility into all agent operations!
