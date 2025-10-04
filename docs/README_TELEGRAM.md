# Telegram Integration for Dental Clinic Assistant

This directory contains a Telegram bot integration for the dental clinic assistant, built on top of the modular OOP architecture.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Copy the example environment file and configure your tokens:

```bash
cp .env.example .env
```

Edit `.env` and add your actual tokens:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Create Your Telegram Bot

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Use `/newbot` command
3. Follow the instructions to get your bot token
4. Add the token to your `.env` file

### 4. Run the Telegram Bot

```bash
python telegram_main.py
```

## 🏗️ Architecture

The Telegram integration follows a modular architecture that allows easy replacement of chat platforms:

```
integrations/
├── chat_interface.py      # Abstract interface for all chat platforms
├── telegram_bot.py        # Telegram-specific implementation
├── session_manager.py     # Multi-user session management
└── chat_transport.py      # Custom Pipecat transport for text-only
```

### Key Components

#### 1. **ChatPlatformInterface** (`chat_interface.py`)
Abstract base class that defines the interface for any chat platform:
- `send_message()` - Send messages to users
- `send_typing_action()` - Show typing indicators
- `get_user_info()` - Get user information
- `set_message_handler()` - Set callback for incoming messages

#### 2. **TelegramBot** (`telegram_bot.py`)
Concrete implementation for Telegram:
- Handles Telegram-specific message formats
- Manages bot commands (`/start`, `/help`, `/reset`)
- Converts between Telegram updates and universal chat messages

#### 3. **ChatSessionManager** (`session_manager.py`)
Manages conversation sessions for multiple users:
- `InMemoryChatSessionManager` - Stores sessions in memory
- `FileChatSessionManager` - Persists sessions to disk
- Session timeout and cleanup
- Message history tracking

#### 4. **ChatTransport** (`chat_transport.py`)
Custom Pipecat transport that bridges text-based chat platforms with the Pipecat pipeline:
- Converts chat messages to Pipecat frames
- Handles text-only communication (no audio processing)
- Manages session state integration

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | ✅ | Your Telegram bot token from BotFather |
| `OPENAI_API_KEY` | ✅ | OpenAI API key for GPT models |
| `OPENAI_MODEL` | ❌ | OpenAI model (default: gpt-4o) |
| `APPOINTMENT_SYSTEM_TYPE` | ❌ | `mock` or `google_calendar` (default: mock) |
| `SESSION_MANAGER_TYPE` | ❌ | `memory` or `file` (default: memory) |
| `SESSION_TIMEOUT_MINUTES` | ❌ | Session timeout in minutes (default: 30) |

### Advanced Configuration

You can also pass a configuration dictionary to customize behavior:

```python
config = {
    "telegram": {
        "token": "your_token",
        "welcome_message": "Custom welcome message",
        "error_message": "Custom error message"
    },
    "session_manager": {
        "type": "file",
        "file": "custom_sessions.json",
        "timeout_minutes": 60
    }
}

assistant = TelegramDentalAssistant(config)
```

## 🤖 Bot Commands

Users can interact with the bot using these commands:

- `/start` - Start a new conversation
- `/help` - Show help information
- `/reset` - Reset the current conversation

## 💬 Conversation Flow

The bot handles the same conversation flow as the original voice assistant:

1. **Welcome & Information**
   - Clinic information
   - Services and pricing
   - Doctor information
   - Insurance details

2. **Appointment Scheduling**
   - Collect patient information
   - Select service type
   - Choose date and time
   - Confirm appointment details

3. **Appointment Management**
   - Find existing appointments
   - Cancel appointments
   - Reschedule appointments

## 🔄 Adding New Chat Platforms

To add support for other chat platforms (Discord, WhatsApp, etc.), follow these steps:

### 1. Implement ChatPlatformInterface

```python
from integrations.chat_interface import ChatPlatformInterface, ChatMessage, ChatUser

class WhatsAppBot(ChatPlatformInterface):
    async def initialize(self) -> None:
        # Initialize WhatsApp connection
        pass
    
    async def send_message(self, user_id: str, message: str, **kwargs) -> bool:
        # Send message via WhatsApp
        pass
    
    # Implement other required methods...
```

### 2. Create Platform-Specific Entry Point

```python
# whatsapp_main.py
from integrations.whatsapp_bot import WhatsAppBot

class WhatsAppDentalAssistant(TelegramDentalAssistant):
    def __init__(self, config=None):
        super().__init__(config)
        # Replace Telegram bot with WhatsApp bot
        whatsapp_config = self.config.get("whatsapp", {})
        self.whatsapp_bot = WhatsAppBot(whatsapp_config)
```

### 3. Update Configuration

Add platform-specific configuration to your environment or config dictionary.

## 🧪 Testing

### Manual Testing

1. Start the bot: `python telegram_main.py`
2. Send `/start` to your bot on Telegram
3. Test various conversation flows:
   - Ask about services
   - Schedule an appointment
   - Try to manage existing appointments

### Unit Testing

```python
import pytest
from integrations.telegram_bot import TelegramBot
from integrations.session_manager import InMemoryChatSessionManager

@pytest.mark.asyncio
async def test_session_creation():
    session_manager = InMemoryChatSessionManager()
    session_id = await session_manager.create_session("123", "telegram")
    assert session_id is not None
    assert await session_manager.is_session_active(session_id)
```

## 🚨 Error Handling

The integration includes comprehensive error handling:

- **Connection Errors**: Automatically retry platform connections
- **Message Delivery**: Fallback error messages for failed deliveries
- **Session Errors**: Session recovery and cleanup
- **Pipeline Errors**: Graceful error responses to users

## 📊 Monitoring

The system logs important events:

- User interactions
- Session creation/cleanup
- Error conditions
- Performance metrics

Use structured logging for production deployments:

```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 🔒 Security Considerations

- **Token Security**: Never commit tokens to version control
- **User Privacy**: Session data is kept separate per user
- **Input Validation**: All user inputs are sanitized
- **Rate Limiting**: Consider adding rate limiting for production

## 🚀 Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "telegram_main.py"]
```

### Environment Variables in Production

```bash
docker run -d \
  -e TELEGRAM_BOT_TOKEN=your_token \
  -e OPENAI_API_KEY=your_key \
  -e SESSION_MANAGER_TYPE=file \
  your_telegram_bot_image
```

## 🛠️ Development

### Project Structure

```
dental_clinic/
├── telegram_main.py           # Telegram entry point
├── dental_clinic_assistant.py # Original voice assistant
├── clinic_info.py            # Clinic data management
├── appointment_systems.py    # Appointment backends
├── conversation_handlers.py  # Business logic
├── flow_nodes.py             # Conversation flow
├── integrations/             # Chat platform integrations
│   ├── __init__.py
│   ├── chat_interface.py     # Abstract interface
│   ├── telegram_bot.py       # Telegram implementation
│   ├── session_manager.py    # Session management
│   └── chat_transport.py     # Pipecat transport
├── requirements.txt          # Dependencies
├── .env.example             # Environment template
└── README_TELEGRAM.md       # This file
```

### Contributing

1. Follow the existing code style
2. Add type hints to all functions
3. Include docstrings for public methods
4. Test your changes with manual testing
5. Update documentation for new features

## 📞 Support

For questions about the Telegram integration:

1. Check the main project documentation
2. Review the conversation flow diagrams
3. Test with the voice version first to understand expected behavior
4. Check logs for error messages

The integration preserves all the functionality of the original voice assistant while providing a text-based interface through Telegram.