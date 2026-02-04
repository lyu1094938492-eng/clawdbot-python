# Quick Start Guide

Get ClawdBot Python up and running in minutes.

## Prerequisites

- Python 3.11+
- pip or Poetry
- API keys (Anthropic or OpenAI)

## Installation

### Option 1: Poetry (Recommended)

```bash
cd clawdbot-python
poetry install
```

### Option 2: pip

```bash
cd clawdbot-python
pip install -e .
```

### Optional Dependencies

For full functionality:

```bash
# Search and memory
pip install duckduckgo-search sentence-transformers torch pyarrow lancedb

# Browser automation
pip install playwright
playwright install

# Scheduler
pip install apscheduler

# Additional channels
pip install line-bot-sdk mattermostdriver matrix-nio

# Voice and media
pip install elevenlabs twilio psutil pillow
```

## Configuration

### 1. Run Onboarding

```bash
clawdbot onboard
```

This creates `~/.clawdbot/clawdbot.json` with default configuration.

### 2. Set API Keys

```bash
export ANTHROPIC_API_KEY="your-anthropic-key"
export OPENAI_API_KEY="your-openai-key"
```

### 3. Configure Channels (Optional)

Edit `~/.clawdbot/clawdbot.json`:

```json
{
  "channels": {
    "telegram": {
      "enabled": true,
      "botToken": "your-bot-token"
    },
    "discord": {
      "enabled": true,
      "botToken": "your-bot-token"
    }
  }
}
```

## Usage

### Start Gateway

```bash
clawdbot gateway start
```

The gateway listens on WebSocket port 18789.

### Run Agent

```bash
# Interactive mode
clawdbot agent run

# Single turn
clawdbot agent run "What's the weather today?"

# With specific model
clawdbot agent run --model claude-opus-4 "Help me code"
```

### Channel Management

```bash
# List channels
clawdbot channels list

# Login to channel
clawdbot channels login telegram
clawdbot channels login discord
```

### Web UI

```bash
# Start web server
uvicorn clawdbot.web.app:app --reload --port 8080
```

Then visit http://localhost:8080

## Testing

```bash
# Run tests
pytest

# Check status
clawdbot status

# Run doctor
clawdbot doctor
```

## Common Commands

```bash
# Status check
clawdbot status

# Health check
clawdbot doctor

# List sessions
clawdbot agent sessions

# Clear sessions
rm -rf ~/.clawdbot/sessions/*
```

## Next Steps

1. Read [CONTRIBUTING.md](CONTRIBUTING.md) for development
2. Check [skills/](skills/) for available skills
3. Explore [extensions/](extensions/) for plugins
4. See [FEATURES_COMPLETE.md](FEATURES_COMPLETE.md) for full feature list

## Troubleshooting

### Gateway won't start
- Check port 18789 is available
- Verify config file exists: `~/.clawdbot/clawdbot.json`

### API errors
- Verify API keys are set
- Check API key validity
- Check internet connection

### Channel errors
- Verify bot tokens
- Check channel-specific requirements
- See channel documentation in `clawdbot/channels/`

## Support

For issues or questions, check:
- GitHub Issues
- Documentation in `docs/`
- Original ClawdBot project

## License

MIT License
