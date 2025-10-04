# Dental Clinic Assistant - Complete System

This is a comprehensive dental clinic assistant system built with Pipecat AI, featuring both voice and text-based chat integrations through a modular OOP architecture.

## 🌟 Features

- **Voice Assistant**: Full voice-based conversation with STT/TTS integration
- **Telegram Bot**: Text-based chat through Telegram with multi-user support
- **Appointment Management**: Schedule, modify, and cancel appointments
- **Clinic Information**: Services, dentists, insurance, and contact details
- **Modular Architecture**: Easy to extend and customize
- **Multiple Backends**: Mock or Google Calendar appointment systems

## 🏗️ System Architecture

### Voice Assistant (Original)
- **Entry Point**: `dental_clinic_assistant.py` or `main.py`
- **Audio Pipeline**: Speech-to-Text → LLM → Text-to-Speech
- **Transports**: Daily.co, WebRTC, or WebSocket
- **Services**: OpenAI GPT, ElevenLabs TTS, Soniox STT

### Telegram Bot Integration (New)
- **Entry Point**: `telegram_main.py`
- **Text Pipeline**: Telegram → LLM → Telegram
- **Transport**: Custom text-only transport
- **Session Management**: Multi-user conversation tracking
- **Platform Agnostic**: Easy to add Discord, WhatsApp, etc.

## 📁 Project Structure

```
dental_clinic/
├── Core Components
│   ├── clinic_info.py              # Clinic data management
│   ├── appointment_systems.py      # Appointment backends
│   ├── flow_nodes.py               # Conversation flow nodes
│   ├── conversation_handlers.py    # Business logic handlers
│   └── dental_clinic_assistant.py  # Voice assistant orchestrator
│
├── Chat Integrations
│   ├── integrations/
│   │   ├── chat_interface.py       # Abstract chat platform interface
│   │   ├── telegram_bot.py         # Telegram implementation
│   │   ├── session_manager.py      # Multi-user session management
│   │   └── chat_transport.py       # Custom Pipecat transport
│   └── telegram_main.py            # Telegram bot entry point
│
├── Configuration & Testing
│   ├── requirements.txt            # Dependencies
│   ├── .env.example               # Environment template
│   ├── test_core_components.py    # Core component tests
│   └── test_telegram.py           # Telegram integration tests
│
├── Documentation
│   ├── README.md                  # This file
│   ├── README_TELEGRAM.md         # Telegram-specific documentation
│   ├── SYSTEM_ARCHITECTURE.md    # Complete system documentation
│   └── TUTORIAL.md                # Step-by-step tutorial
│
└── Legacy
    └── dental_clinic.py           # Original monolithic file
```

## 🚀 Quick Start

### Option 1: Voice Assistant

1. **Set up environment**:
   ```bash
   cp .env.example .env
   # Add your API keys: OPENAI_API_KEY, ELEVENLABS_API_KEY, SONIOX_API_KEY
   ```

2. **Install dependencies**:
   ```bash
   pip install pipecat-ai pipecat-flows openai elevenlabs
   ```

3. **Run voice assistant**:
   ```bash
   python dental_clinic_assistant.py
   # Or: python main.py
   ```

### Option 2: Telegram Bot

1. **Create Telegram bot**:
   - Message [@BotFather](https://t.me/BotFather) 
   - Use `/newbot` command
   - Get your bot token

2. **Set up environment**:
   ```bash
   cp .env.example .env
   # Add: TELEGRAM_BOT_TOKEN, OPENAI_API_KEY
   ```

3. **Install dependencies**:
   ```bash
   pip install python-telegram-bot pipecat-ai pipecat-flows openai
   ```

4. **Run Telegram bot**:
   ```bash
   python telegram_main.py
   ```

5. **Test on Telegram**:
   - Send `/start` to your bot
   - Ask about services, schedule appointments, etc.

## 🎯 Core Components Explained

### 1. ClinicInfo (`clinic_info.py`)
Centralizes all clinic data including services, dentists, schedules, and contact information.

**Key Features**:
- Structured clinic data with services and pricing
- Dentist profiles with specialties
- Operating hours and contact details
- Helper methods for formatted output

### 2. Appointment Systems (`appointment_systems.py`)
Modular appointment backend supporting different calendar systems.

**Implementations**:
- `MockAppointmentSystem`: For testing and development
- `GoogleCalendarAppointmentSystem`: Full Google Calendar integration
- `AppointmentSystemFactory`: Creates appropriate system instances

### 3. Conversation Handlers (`conversation_handlers.py`)
Contains all business logic for handling user conversations.

**Capabilities**:
- Information requests (services, dentists, insurance)
- Appointment scheduling workflow
- Existing appointment management (cancel, reschedule)
- Navigation and flow control

### 4. Flow Nodes (`flow_nodes.py`)
Creates conversation nodes for the Pipecat flow system.

**Node Types**:
- Initial/welcome nodes
- Information nodes
- Appointment scheduling nodes
- Confirmation and success nodes

### 5. Chat Integrations (`integrations/`)
Modular system for adding text-based chat platforms.

**Components**:
- **Abstract Interface**: Platform-agnostic chat interface
- **Telegram Implementation**: Full Telegram bot functionality
- **Session Manager**: Multi-user conversation state
- **Custom Transport**: Bridges chat platforms with Pipecat

## 🔧 Configuration Options

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | ✅ | - | OpenAI API key for LLM |
| `TELEGRAM_BOT_TOKEN` | For Telegram | - | Bot token from BotFather |
| `ELEVENLABS_API_KEY` | For voice | - | ElevenLabs TTS API key |
| `SONIOX_API_KEY` | For voice | - | Soniox STT API key |
| `APPOINTMENT_SYSTEM_TYPE` | ❌ | `mock` | `mock` or `google_calendar` |
| `SESSION_MANAGER_TYPE` | ❌ | `memory` | `memory` or `file` |

### Appointment Systems

**Mock System** (Default):
```python
assistant = DentalClinicAssistant()  # Uses mock by default
```

**Google Calendar Integration**:
```python
assistant = DentalClinicAssistant(
    appointment_system_type="google_calendar",
    service_account_file="path/to/credentials.json"
)
```

## 🧪 Testing

### Core Components Test
```bash
python test_core_components.py
```
Tests all core components without external dependencies.

### Telegram Integration Test
```bash
python test_telegram.py  # Requires telegram library
```
Tests Telegram-specific components.

### Manual Testing
1. Run the assistant
2. Test conversation flows:
   - Ask about clinic services
   - Schedule an appointment
   - Manage existing appointments
   - Navigate through different options

## 🔄 Extending the System

### Adding New Chat Platforms

1. **Implement ChatPlatformInterface**:
   ```python
   class WhatsAppBot(ChatPlatformInterface):
       async def send_message(self, user_id: str, message: str) -> bool:
           # WhatsApp-specific implementation
   ```

2. **Create platform entry point**:
   ```python
   # whatsapp_main.py - similar to telegram_main.py
   ```

3. **Update configuration** for the new platform.

### Adding New Services

1. **Update ClinicInfo** with new service data
2. **Add handler methods** in ConversationHandlers
3. **Create flow nodes** in FlowNodeFactory
4. **Test the new functionality**

### Custom Appointment Systems

1. **Implement AppointmentSystemInterface**:
   ```python
   class MyAppointmentSystem(AppointmentSystemInterface):
       # Implement all required methods
   ```

2. **Register in factory**:
   ```python
   # Add to AppointmentSystemFactory.create_system()
   ```

## 🛠️ Development Guidelines

### Code Organization
- One class per file when possible
- Clear separation of concerns
- Abstract interfaces for extensibility
- Comprehensive error handling

### Testing Strategy
- Unit tests for each component
- Integration tests for workflows
- Manual testing for user experience
- Mock external dependencies

### Documentation Standards
- Docstrings for all public methods
- Type hints throughout
- Clear README files
- Architecture documentation

## 📖 Additional Documentation

- **[Telegram Integration Guide](README_TELEGRAM.md)**: Detailed Telegram setup and usage
- **[System Architecture](SYSTEM_ARCHITECTURE.md)**: Complete technical deep-dive
- **[Tutorial](TUTORIAL.md)**: Step-by-step implementation guide

## 🤝 Support

For questions or issues:
1. Check the documentation files
2. Review the test files for usage examples
3. Examine the conversation flow diagrams
4. Test with the voice version first to understand expected behavior

## 🎉 Key Benefits

**For Users**:
- Natural conversation flow
- Multiple interaction methods (voice/text)
- Comprehensive appointment management
- 24/7 availability

**For Developers**:
- Modular, maintainable code
- Easy to extend and customize
- Comprehensive test coverage
- Clear architecture documentation
- Multiple platform support

This system demonstrates how to build scalable, maintainable AI assistants using modern software engineering principles while leveraging the power of Pipecat AI framework.