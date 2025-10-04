# Dental Clinic Assistant - Complete System Architecture

This document provides a comprehensive, explicit explanation of how the entire dental clinic assistant system works from top to bottom. Use this as your definitive reference for understanding the system architecture, data flow, and component interactions.

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Patterns](#architecture-patterns)
3. [Core Components Deep Dive](#core-components-deep-dive)
4. [Data Flow Analysis](#data-flow-analysis)
5. [Integration Layers](#integration-layers)
6. [Session Management](#session-management)
7. [Conversation Flow Engine](#conversation-flow-engine)
8. [Component Interactions](#component-interactions)
9. [Error Handling & Resilience](#error-handling--resilience)
10. [Extension Points](#extension-points)

---

## 1. System Overview

### High-Level Architecture

The system follows a **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Voice     │  │  Telegram   │  │   Future    │        │
│  │ Assistant   │  │    Bot      │  │ Platforms   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────────┐
│                   Transport Layer                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Audio     │  │    Chat     │  │   Custom    │        │
│  │ Transport   │  │ Transport   │  │ Transports  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────────┐
│                 Processing Pipeline                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │     STT     │  │     LLM     │  │     TTS     │        │
│  │   (Voice)   │  │  (OpenAI)   │  │   (Voice)   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────────┐
│                  Conversation Engine                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │    Flow     │  │ Conversation│  │   Session   │        │
│  │  Manager    │  │  Handlers   │  │   Manager   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────────┐
│                   Business Logic                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Clinic    │  │ Appointment │  │    Flow     │        │
│  │    Info     │  │   Systems   │  │   Nodes     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### System Variants

The system supports **two main interaction modes**:

1. **Voice Assistant**: Audio input/output with STT/TTS processing
2. **Text Chat**: Text-only interaction through messaging platforms

Both variants share the same core business logic and conversation engine.

---

## 2. Architecture Patterns

### Design Patterns Used

#### 2.1 Factory Pattern
**Location**: `appointment_systems.py:AppointmentSystemFactory`

**Purpose**: Creates appointment system instances without exposing creation logic.

```python
# Usage Pattern
appointment_system = AppointmentSystemFactory.create_system(
    system_type="google_calendar",  # or "mock"
    service_account_file="credentials.json"
)
```

**Benefits**:
- Easy to add new appointment backends
- Configuration-driven system selection
- Centralizes system creation logic

#### 2.2 Strategy Pattern
**Location**: `appointment_systems.py:AppointmentSystemInterface`

**Purpose**: Allows interchangeable appointment backends.

```python
class AppointmentSystemInterface(ABC):
    @abstractmethod
    def create_appointment(self, ...): pass
    @abstractmethod
    def cancel_appointment(self, ...): pass
    # ... other methods
```

**Implementations**:
- `MockAppointmentSystem`: For testing/development
- `GoogleCalendarAppointmentSystem`: Production calendar integration

#### 2.3 Template Method Pattern
**Location**: `flow_nodes.py:FlowNodeFactory`

**Purpose**: Defines conversation flow structure while allowing customization.

```python
def create_initial_node(self, functions):
    # Template structure
    return NodeConfig(
        system_prompt=self._build_initial_prompt(),
        tools=self._build_tools(functions),
        # ... standard structure
    )
```

#### 2.4 Observer Pattern
**Location**: `integrations/chat_transport.py`

**Purpose**: Handles platform events and message updates.

```python
# Platform notifies transport of new messages
platform.set_message_handler(transport._handle_platform_message)
```

#### 2.5 State Pattern
**Location**: `conversation_handlers.py:ConversationState`

**Purpose**: Manages conversation state transitions.

```python
class ConversationState:
    def __init__(self):
        self.current_appointment = None
        self.patient_info = {}
        self.found_appointment = {}
```

---

## 3. Core Components Deep Dive

### 3.1 ClinicInfo (`clinic_info.py`)

**Responsibility**: Central repository for all clinic-related data.

**Data Structure**:
```python
{
    "name": "Clinica Dentară Zâmbet Strălucitor",
    "services": {
        "teeth_cleaning": {
            "name": "Detartraj Dentar",
            "description": "...",
            "duration": 45,
            "price": "200 RON"
        },
        # ... more services
    },
    "dentists": [
        {
            "name": "Dr. Ana Popescu",
            "specialty": "Stomatologie Generală",
            "experience": "15 ani"
        },
        # ... more dentists
    ],
    "hours": { "monday": "08:00 - 18:00", ... },
    "insurance": ["Regina Maria", "Medicover", ...]
}
```

**Key Methods**:
- `get_service(service_key)`: Returns service details
- `get_dentist_by_name(name)`: Returns dentist information
- `get_services_text()`: Formatted service list for LLM
- `get_dentists_text()`: Formatted dentist list for LLM

**Usage Pattern**:
```python
clinic_info = ClinicInfo()
service = clinic_info.get_service("teeth_cleaning")
# Returns: {"name": "Detartraj Dentar", "price": "200 RON", ...}
```

### 3.2 Appointment Systems (`appointment_systems.py`)

**Interface Definition**:
```python
class AppointmentSystemInterface(ABC):
    @abstractmethod
    def check_availability(self, date: str, time: str, duration_minutes: int = 60, doctor: str = None) -> bool
    
    @abstractmethod
    def get_available_slots(self, date: str, doctor: str = None) -> List[str]
    
    @abstractmethod
    def create_appointment(self, patient_name: str, phone: str, date: str, time: str, service: str, dentist: Optional[str] = None) -> Optional[str]
    
    @abstractmethod
    def cancel_appointment(self, appointment_id: str) -> bool
    
    @abstractmethod
    def update_appointment(self, appointment_id: str, **updates) -> bool
    
    @abstractmethod
    def find_appointment(self, patient_name: str, phone: Optional[str] = None) -> Optional[Dict]
```

**Mock Implementation Flow**:
```python
# MockAppointmentSystem.create_appointment()
def create_appointment(self, patient_name, phone, date, time, service, dentist=None):
    appointment_id = f"APPT{self.next_id:04d}"
    self.next_id += 1
    
    self.appointments[appointment_id] = {
        "id": appointment_id,
        "patient_name": patient_name,
        "phone": phone,
        "date": date,
        "time": time,
        "service": service,
        "dentist": dentist or "Dr. Ana Popescu",
        "status": "scheduled",
        "created_at": datetime.now().isoformat()
    }
    
    return appointment_id
```

**Google Calendar Integration Flow**:
1. Initialize Google Calendar service with service account
2. Check availability using freebusy API
3. Create events in main calendar and doctor-specific calendars
4. Set up event reminders and notifications
5. Handle calendar-specific errors and timeouts

### 3.3 Conversation Handlers (`conversation_handlers.py`)

**State Management**:
```python
class ConversationState:
    current_appointment: Optional[str]    # Active appointment being worked on
    patient_info: Dict                   # Collected patient information
    found_appointment: Dict              # Located existing appointment
    available_slots: List[str]           # Available time slots for booking
```

**Handler Method Pattern**:
```python
async def handler_method(self, flow_manager: FlowManager, *args) -> Tuple[None, NodeConfig]:
    # 1. Process input parameters
    # 2. Update conversation state
    # 3. Perform business logic (e.g., create appointment)
    # 4. Determine next conversation functions
    # 5. Create and return appropriate flow node
    
    functions = [self.next_handler_1, self.next_handler_2, self.back_to_main]
    return None, self.node_factory.create_appropriate_node(functions)
```

**Example: Appointment Booking Flow**:
```python
async def provide_patient_info(self, flow_manager, patient_name: str, phone_number: str):
    # 1. Store patient information
    self.conversation_state.patient_info = {
        "name": patient_name,
        "phone": phone_number
    }
    
    # 2. Prepare next step functions
    functions = [self.select_service, self.back_to_main]
    
    # 3. Return service selection node
    return None, self.node_factory.create_service_selection_node(functions)
```

### 3.4 Flow Nodes (`flow_nodes.py`)

**Node Creation Pattern**:
```python
def create_node_type(self, functions: List) -> NodeConfig:
    return NodeConfig(
        system_prompt=self._build_prompt_for_type(),
        tools=self._build_tools(functions),
        tool_choice="auto"
    )

def _build_tools(self, functions: List) -> List[Dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": func.__name__,
                "description": self._get_function_description(func),
                "parameters": self._get_function_parameters(func)
            }
        }
        for func in functions
    ]
```

**Node Types and Their Prompts**:

1. **Initial Node**: Welcomes users and presents main options
2. **Info Nodes**: Provide clinic information (services, dentists, insurance)
3. **Appointment Nodes**: Handle appointment scheduling workflow
4. **Management Nodes**: Handle existing appointment operations
5. **Confirmation Nodes**: Confirm actions before execution
6. **Success/Error Nodes**: Provide feedback on completed operations

---

## 4. Data Flow Analysis

### 4.1 Voice Assistant Data Flow

```
User Voice Input
       ↓
   STT Service (Soniox)
       ↓
   TranscriptionFrame
       ↓
   LLM Context Aggregator (User)
       ↓
   LLM Service (OpenAI GPT)
       ↓
   Function Call or Text Response
       ↓
   [If Function Call]
       ↓
   Flow Manager → Conversation Handlers
       ↓
   Business Logic Execution
       ↓
   Updated Flow Node
       ↓
   New System Prompt + Tools
       ↓
   LLM Service (with updated context)
       ↓
   Text Response
       ↓
   TTS Service (ElevenLabs)
       ↓
   AudioFrame
       ↓
   Transport Output
       ↓
   User Hears Response
```

### 4.2 Telegram Bot Data Flow

```
User Telegram Message
       ↓
   Telegram Bot API
       ↓
   TelegramBot.handle_message()
       ↓
   ChatMessage + ChatUser Objects
       ↓
   ChatTransport.handle_platform_message()
       ↓
   Session Manager (get/create session)
       ↓
   TranscriptionFrame (text → frame)
       ↓
   LLM Context Aggregator
       ↓
   LLM Service (OpenAI GPT)
       ↓
   Function Call or Text Response
       ↓
   [Same business logic as voice]
       ↓
   TextFrame Response
       ↓
   ChatTransport.send_message()
       ↓
   TelegramBot.send_message()
       ↓
   Telegram Bot API
       ↓
   User Receives Telegram Message
```

### 4.3 Appointment Booking Data Flow

**Step-by-Step Process**:

1. **Initial Request**: User says "I want to schedule an appointment"
   ```python
   # Flow Manager receives function call
   await conversation_handlers.schedule_appointment(flow_manager)
   
   # Returns node asking for patient information
   node = create_appointment_node([provide_patient_info, back_to_main])
   ```

2. **Patient Information**: User provides name and phone
   ```python
   await provide_patient_info(flow_manager, "John Doe", "0700123456")
   
   # Updates conversation state
   conversation_state.patient_info = {
       "name": "John Doe", 
       "phone": "0700123456"
   }
   
   # Returns service selection node
   ```

3. **Service Selection**: User chooses service type
   ```python
   await select_service(flow_manager, "teeth_cleaning")
   
   # Updates conversation state
   conversation_state.patient_info["service"] = "teeth_cleaning"
   
   # Returns date/time selection node
   ```

4. **Date/Time Selection**: User provides preferred date/time
   ```python
   await select_date_time(flow_manager, "2024-12-15", "10:00")
   
   # Check availability
   available = appointment_system.check_availability("2024-12-15", "10:00")
   
   if available:
       # Store and confirm
       conversation_state.patient_info.update({"date": "2024-12-15", "time": "10:00"})
       return confirmation_node()
   else:
       # Show alternatives
       slots = appointment_system.get_available_slots("2024-12-15")
       return alternatives_node(slots)
   ```

5. **Confirmation**: User confirms appointment details
   ```python
   await confirm_appointment(flow_manager)
   
   # Create actual appointment
   appointment_id = appointment_system.create_appointment(
       patient_name=patient_info["name"],
       phone=patient_info["phone"],
       date=patient_info["date"],
       time=patient_info["time"],
       service=patient_info["service"]
   )
   
   # Store appointment ID
   conversation_state.current_appointment = appointment_id
   
   # Return success node
   ```

---

## 5. Integration Layers

### 5.1 Chat Platform Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Chat Platform Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Telegram   │  │  Discord    │  │  WhatsApp   │        │
│  │    Bot      │  │    Bot      │  │    Bot      │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────┬───────────────────────────────────────────┘
                  │ Implements ChatPlatformInterface
┌─────────────────┴───────────────────────────────────────────┐
│              Chat Interface Abstraction                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         ChatPlatformInterface                       │   │
│  │  • send_message(user_id, message)                  │   │
│  │  • send_typing_action(user_id)                     │   │
│  │  • get_user_info(user_id)                          │   │
│  │  • set_message_handler(callback)                   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────┬───────────────────────────────────────────┘
                  │ Used by ChatTransport
┌─────────────────┴───────────────────────────────────────────┐
│                Chat Transport Layer                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              ChatTransport                          │   │
│  │  • Converts platform messages to Pipecat frames    │   │
│  │  • Handles session management integration          │   │
│  │  • Manages text-only communication                 │   │
│  │  • Bridges chat platforms with Pipecat pipeline    │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────┬───────────────────────────────────────────┘
                  │ Integrates with Pipecat Pipeline
┌─────────────────┴───────────────────────────────────────────┐
│                  Pipecat Pipeline                          │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Session Management Integration

**Session Lifecycle**:

1. **Session Creation**:
   ```python
   # When user first interacts
   session_id = await session_manager.create_session(user_id, platform)
   
   # Session data structure
   {
       "session_id": "uuid-string",
       "user_id": "telegram_user_123",
       "platform": "telegram",
       "created_at": "2024-12-15T10:00:00",
       "last_activity": "2024-12-15T10:30:00",
       "conversation_state": {},
       "message_history": [],
       "metadata": {}
   }
   ```

2. **Session Updates**:
   ```python
   # On each message
   await session_manager.update_session_data(session_id, {
       "conversation_state": conversation_state.__dict__,
       "last_activity": datetime.now().isoformat()
   })
   
   # Add message to history
   await session_manager.add_message_to_history(session_id, {
       "type": "user_message",
       "content": message.content,
       "timestamp": datetime.now().isoformat()
   })
   ```

3. **Session Cleanup**:
   ```python
   # Background cleanup task
   async def _cleanup_expired_sessions(self):
       while self._running:
           expired_sessions = []
           for session_id in self.sessions:
               if not await self.is_session_active(session_id):
                   expired_sessions.append(session_id)
           
           for session_id in expired_sessions:
               await self.end_session(session_id)
   ```

### 5.3 Transport Integration Points

**ChatTransport Integration**:

```python
class ChatTransport(BaseTransport):
    async def _handle_platform_message(self, message: ChatMessage, user: ChatUser):
        # 1. Set current session context
        self._current_user = user
        self._current_session_id = await self._get_or_create_session(user)
        
        # 2. Convert to Pipecat frames
        if message.is_command:
            await self._handle_command_message(message, user)
        elif message.is_text:
            await self._handle_text_message(message, user)
    
    async def _handle_text_message(self, message: ChatMessage, user: ChatUser):
        # Convert chat message to Pipecat frames
        await self.push_frame(UserStartedSpeakingFrame())
        await self.push_frame(TranscriptionFrame(text=message.content))
        await self.push_frame(UserStoppedSpeakingFrame())
    
    async def send_message(self, frame: TextFrame):
        # Convert Pipecat frame to platform message
        await self._platform.send_message(self._current_user.user_id, frame.text)
```

---

## 6. Session Management

### 6.1 Multi-User Session Architecture

**Problem Solved**: Multiple users can interact with the system simultaneously, each maintaining their own conversation state.

**Solution Components**:

1. **Session Identification**:
   ```python
   def _get_user_key(self, user_id: str, platform: str) -> str:
       return f"{platform}:{user_id}"  # e.g., "telegram:123456"
   ```

2. **Session Storage**:
   ```python
   # In-memory storage structure
   {
       "sessions": {
           "session-uuid-1": { ... session_data ... },
           "session-uuid-2": { ... session_data ... }
       },
       "user_sessions": {
           "telegram:123456": "session-uuid-1",
           "telegram:789012": "session-uuid-2"
       },
       "session_users": {
           "session-uuid-1": "telegram:123456",
           "session-uuid-2": "telegram:789012"
       },
       "session_timestamps": {
           "session-uuid-1": datetime.now(),
           "session-uuid-2": datetime.now()
       }
   }
   ```

3. **Session Isolation**:
   Each session maintains independent:
   - Conversation state
   - Message history
   - Appointment data
   - Flow context

### 6.2 Session State Persistence

**In-Memory Manager** (`InMemoryChatSessionManager`):
- Fast access
- No I/O overhead
- Lost on restart

**File-Based Manager** (`FileChatSessionManager`):
- Persists across restarts
- JSON file storage
- Automatic save on updates

```python
def _save_sessions(self):
    data = {
        "sessions": self.sessions,
        "user_sessions": self.user_sessions,
        "session_users": self.session_users,
        "saved_at": datetime.now().isoformat()
    }
    
    with open(self.session_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
```

---

## 7. Conversation Flow Engine

### 7.1 Flow Manager Integration

**Pipecat Flows Architecture**:
```python
flow_manager = FlowManager(
    task=pipeline_task,
    llm=llm_service,
    context_aggregator=context_aggregator,
    transport=transport
)

# Initialize with starting node
await flow_manager.initialize(initial_node)
```

**Node Structure**:
```python
NodeConfig = {
    "system_prompt": "You are a dental clinic assistant...",
    "tools": [
        {
            "type": "function",
            "function": {
                "name": "schedule_appointment",
                "description": "User wants to schedule a new appointment",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
    ],
    "tool_choice": "auto"
}
```

### 7.2 Function Call Resolution

**Flow Process**:
1. User input → LLM processes with current node's tools
2. LLM decides to call a function or respond with text
3. If function call → Flow Manager routes to appropriate handler
4. Handler executes business logic and returns new node
5. Flow Manager updates system prompt and tools
6. Process continues with new context

**Example Function Call Resolution**:
```python
# LLM generates function call
{
    "tool_calls": [
        {
            "function": {
                "name": "provide_patient_info",
                "arguments": {
                    "patient_name": "John Doe",
                    "phone_number": "0700123456"
                }
            }
        }
    ]
}

# Flow Manager routes to handler
result, new_node = await conversation_handlers.provide_patient_info(
    flow_manager, "John Doe", "0700123456"
)

# Flow Manager updates context with new node
await flow_manager.set_current_node(new_node)
```

### 7.3 Context Management

**LLM Context Structure**:
```python
context = LLMContext()

# System messages (from current node)
context.add_system_message("You are a dental clinic assistant...")

# User messages
context.add_user_message("I want to schedule an appointment")

# Assistant responses
context.add_assistant_message("I'll help you schedule an appointment...")

# Function calls and responses
context.add_function_call("provide_patient_info", {"name": "John"})
context.add_function_response("Patient information collected successfully")
```

**Context Aggregation**:
```python
context_aggregator = LLMContextAggregatorPair(context)

# In pipeline
pipeline = Pipeline([
    transport.input(),
    stt,                          # Voice only
    context_aggregator.user(),    # Adds user message to context
    llm,                         # Processes with full context
    tts,                         # Voice only
    transport.output(),
    context_aggregator.assistant() # Adds assistant response to context
])
```

---

## 8. Component Interactions

### 8.1 Voice Assistant Component Interaction

**Initialization Sequence**:
```python
# 1. Create core components
clinic_info = ClinicInfo()
appointment_system = AppointmentSystemFactory.create_system("mock")
conversation_state = ConversationState()

# 2. Create factory and handlers
node_factory = FlowNodeFactory(clinic_info, conversation_state.__dict__)
conversation_handlers = ConversationHandlers(
    clinic_info, appointment_system, node_factory, conversation_state
)

# 3. Set up services
stt = SonioxSTTService(api_key=os.getenv("SONIOX_API_KEY"))
tts = ElevenLabsTTSService(api_key=os.getenv("ELEVENLABS_API_KEY"))
llm = OpenAILLMService(api_key=os.getenv("OPENAI_API_KEY"))

# 4. Create pipeline
context = LLMContext()
context_aggregator = LLMContextAggregatorPair(context)
pipeline = Pipeline([
    transport.input(), stt, context_aggregator.user(),
    llm, tts, transport.output(), context_aggregator.assistant()
])

# 5. Initialize flow manager
flow_manager = FlowManager(task, llm, context_aggregator, transport)
initial_functions = [handlers.get_clinic_info, handlers.schedule_appointment, ...]
await flow_manager.initialize(node_factory.create_initial_node(initial_functions))
```

**Runtime Interaction Flow**:
```python
# User speaks → STT → TranscriptionFrame
user_input = "I want to schedule an appointment"

# LLM processes with current node context
# LLM generates function call: schedule_appointment()

# Flow Manager routes call
result, new_node = await conversation_handlers.schedule_appointment(flow_manager)

# New node has updated system prompt and tools
new_node = {
    "system_prompt": "You are helping to collect patient information...",
    "tools": [provide_patient_info, back_to_main]
}

# LLM continues with new context
# LLM responds: "I'll help you schedule an appointment. What's your name and phone number?"

# TTS → Audio → User hears response
```

### 8.2 Telegram Bot Component Interaction

**Message Processing Sequence**:
```python
# 1. User sends Telegram message
telegram_update = Update(...)

# 2. TelegramBot processes update
await telegram_bot._handle_message(update, context)

# 3. Convert to unified objects
chat_user = ChatUser(user_id="123", username="john", ...)
chat_message = ChatMessage(content="Hello", type=MessageType.TEXT, ...)

# 4. ChatTransport handles platform message
await chat_transport._handle_platform_message(chat_message, chat_user)

# 5. Session management
session_id = await session_manager.get_or_create_session("123", "telegram")

# 6. Convert to Pipecat frames
await chat_transport.push_frame(TranscriptionFrame(text="Hello"))

# 7. Pipeline processing (same as voice)
# User frame → LLM → Function call → Business logic → Response

# 8. Convert response back to platform message
await chat_transport.send_message(TextFrame(text="Hello! How can I help?"))

# 9. Send via Telegram API
await telegram_bot.send_message("123", "Hello! How can I help?")
```

### 8.3 Cross-Component Data Flow

**Appointment Creation Cross-Component Flow**:

```python
# 1. User Request (Voice or Text)
"I want to schedule an appointment for teeth cleaning on December 15th at 2 PM"

# 2. LLM Function Call Resolution
function_call = {
    "name": "select_date_time",
    "arguments": {
        "preferred_date": "2024-12-15",
        "preferred_time": "14:00"
    }
}

# 3. Conversation Handler Processing
async def select_date_time(self, flow_manager, preferred_date, preferred_time):
    # Business logic interaction
    available = self.appointment_system.check_availability(preferred_date, preferred_time)
    
    if available:
        # Update conversation state
        self.conversation_state.patient_info.update({
            "date": preferred_date,
            "time": preferred_time
        })
        
        # Create next flow node
        functions = [self.confirm_appointment, self.modify_appointment_details, self.back_to_main]
        return None, self.node_factory.create_appointment_confirmation_node(functions)
    else:
        # Get alternatives from appointment system
        available_slots = self.appointment_system.get_available_slots(preferred_date)
        self.conversation_state.available_slots = available_slots
        
        # Create alternatives flow node
        functions = [self.select_alternative_time, self.select_date_time, self.back_to_main]
        return None, self.node_factory.create_alternative_times_node(functions)

# 4. Node Factory Creates Response Context
def create_appointment_confirmation_node(self, functions):
    # Build system prompt with current state
    patient_info = self.conversation_state["patient_info"]
    service_info = self.clinic_info.get_service(patient_info["service"])
    
    system_prompt = f"""
    You are confirming appointment details:
    
    Patient: {patient_info["name"]}
    Phone: {patient_info["phone"]}
    Service: {service_info["name"]} ({service_info["duration"]} minutes)
    Date: {patient_info["date"]}
    Time: {patient_info["time"]}
    Estimated Cost: {service_info["price"]}
    
    Ask the patient to confirm these details or make changes.
    """
    
    return NodeConfig(
        system_prompt=system_prompt,
        tools=self._build_tools(functions)
    )

# 5. Flow Manager Updates Context
# 6. LLM Generates Confirmation Response
# 7. Response Delivered via Transport (Voice TTS or Text Chat)
```

---

## 9. Error Handling & Resilience

### 9.1 Error Handling Layers

**Transport Layer Error Handling**:
```python
async def send_message(self, user_id: str, message: str) -> bool:
    try:
        await self._bot.send_message(chat_id=int(user_id), text=message)
        return True
    except Exception as e:
        logger.error(f"Failed to send message to {user_id}: {e}")
        # Fallback: Try to send error message
        try:
            await self._bot.send_message(chat_id=int(user_id), text=self.error_message)
        except:
            pass  # Ultimate fallback: silent failure
        return False
```

**Business Logic Error Handling**:
```python
async def create_appointment(self, patient_name: str, phone: str, date: str, 
                           time: str, service: str, dentist: Optional[str] = None) -> Optional[str]:
    try:
        # Attempt appointment creation
        appointment_id = self._create_appointment_internal(...)
        return appointment_id
    except GoogleCalendarError as e:
        logger.error(f"Calendar error: {e}")
        # Fallback to mock system or return error
        return None
    except Exception as e:
        logger.error(f"Unexpected error creating appointment: {e}")
        return None
```

**Session Management Error Handling**:
```python
async def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
    try:
        if not await self.is_session_active(session_id):
            return None
        return self.sessions.get(session_id, {}).copy()
    except Exception as e:
        logger.error(f"Failed to get session data for {session_id}: {e}")
        # Create new session as fallback
        return None
```

### 9.2 Resilience Patterns

**Circuit Breaker Pattern** (for external services):
```python
class AppointmentSystemWithCircuitBreaker:
    def __init__(self, appointment_system, failure_threshold=5):
        self.appointment_system = appointment_system
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.last_failure_time = None
        self.circuit_open = False
    
    async def create_appointment(self, *args, **kwargs):
        if self.circuit_open:
            if datetime.now() - self.last_failure_time > timedelta(minutes=5):
                self.circuit_open = False  # Try again
            else:
                raise ServiceUnavailableError("Appointment system temporarily unavailable")
        
        try:
            result = await self.appointment_system.create_appointment(*args, **kwargs)
            self.failure_count = 0  # Reset on success
            return result
        except Exception as e:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.circuit_open = True
                self.last_failure_time = datetime.now()
            raise
```

**Graceful Degradation**:
```python
# If Google Calendar fails, fall back to mock system
try:
    appointment_system = GoogleCalendarAppointmentSystem(...)
except Exception as e:
    logger.warning(f"Google Calendar unavailable, using mock system: {e}")
    appointment_system = MockAppointmentSystem()
```

### 9.3 Recovery Mechanisms

**Session Recovery**:
```python
async def recover_session(self, user_id: str, platform: str) -> str:
    """Attempt to recover a lost session."""
    # Try to load from persistent storage
    session_id = await self.load_session_from_backup(user_id, platform)
    
    if session_id:
        # Validate and reactivate
        if await self.validate_session(session_id):
            self.session_timestamps[session_id] = datetime.now()
            return session_id
    
    # Create new session if recovery fails
    return await self.create_session(user_id, platform)
```

**Conversation State Recovery**:
```python
# If conversation state is lost, start fresh with helpful context
def reset_conversation_with_context(self):
    """Reset conversation but preserve helpful context."""
    previous_appointments = self.conversation_state.found_appointment
    
    # Reset state
    self.conversation_state.reset()
    
    # Preserve useful information
    if previous_appointments:
        self.conversation_state.found_appointment = previous_appointments
        
    # Return to main menu with context
    return self.create_initial_node_with_context()
```

---

## 10. Extension Points

### 10.1 Adding New Chat Platforms

**Step-by-Step Extension Process**:

1. **Implement ChatPlatformInterface**:
   ```python
   class WhatsAppBot(ChatPlatformInterface):
       def __init__(self, config: Dict[str, Any]):
           super().__init__(config)
           self.whatsapp_client = WhatsAppClient(config["api_key"])
       
       async def send_message(self, user_id: str, message: str, **kwargs) -> bool:
           return await self.whatsapp_client.send_text(user_id, message)
       
       async def send_typing_action(self, user_id: str) -> None:
           await self.whatsapp_client.send_typing_indicator(user_id)
       
       # ... implement all required methods
   ```

2. **Create Platform Entry Point**:
   ```python
   # whatsapp_main.py
   class WhatsAppDentalAssistant(TelegramDentalAssistant):
       def __init__(self, config: Optional[Dict[str, Any]] = None):
           super().__init__(config)
           # Replace Telegram bot with WhatsApp bot
           whatsapp_config = self.config.get("whatsapp", {})
           self.whatsapp_bot = WhatsAppBot(whatsapp_config)
           
           # Update transport to use WhatsApp bot
           self.transport = ChatTransport(ChatTransportParams(
               platform=self.whatsapp_bot,
               session_manager=self.session_manager
           ))
   ```

3. **Update Configuration**:
   ```python
   # Add WhatsApp-specific configuration
   "whatsapp": {
       "api_key": os.getenv("WHATSAPP_API_KEY"),
       "webhook_token": os.getenv("WHATSAPP_WEBHOOK_TOKEN"),
       "welcome_message": "WhatsApp-specific welcome message"
   }
   ```

### 10.2 Adding New Appointment Systems

**Extension Example**:
```python
class OutlookCalendarAppointmentSystem(AppointmentSystemInterface):
    def __init__(self, client_id: str, client_secret: str, tenant_id: str):
        self.graph_client = GraphServiceClient(...)
    
    async def create_appointment(self, patient_name: str, phone: str, 
                               date: str, time: str, service: str, 
                               dentist: Optional[str] = None) -> Optional[str]:
        # Microsoft Graph API implementation
        event = Event(
            subject=f"{service} - {patient_name}",
            start=DateTimeTimeZone(...),
            end=DateTimeTimeZone(...),
            body=ItemBody(content=f"Patient: {patient_name}\nPhone: {phone}")
        )
        
        created_event = await self.graph_client.me.events.post(event)
        return created_event.id
    
    # ... implement other required methods

# Register in factory
class AppointmentSystemFactory:
    @staticmethod
    def create_system(system_type: str = "mock", **kwargs) -> AppointmentSystemInterface:
        if system_type == "mock":
            return MockAppointmentSystem()
        elif system_type == "google_calendar":
            return GoogleCalendarAppointmentSystem(**kwargs)
        elif system_type == "outlook":
            return OutlookCalendarAppointmentSystem(**kwargs)
        else:
            raise ValueError(f"Unknown appointment system type: {system_type}")
```

### 10.3 Adding New Business Logic

**Service Extension Example**:
```python
# Add teeth whitening consultation to ClinicInfo
def add_whitening_consultation_service(self):
    self._info["services"]["whitening_consultation"] = {
        "name": "Consultație Albire Dentară",
        "description": "Evaluare pentru tratament de albire, inclusiv analiza culorii",
        "duration": 30,
        "price": "150 RON",
        "prerequisites": ["recent_cleaning"],
        "follow_up_services": ["teeth_whitening"]
    }

# Add handler method
class ConversationHandlers:
    async def schedule_whitening_consultation(self, flow_manager: FlowManager) -> Tuple[None, NodeConfig]:
        """Handle whitening consultation scheduling with prerequisites."""
        # Check if patient has recent cleaning
        if not await self._check_recent_cleaning():
            functions = [self.schedule_cleaning_first, self.back_to_main]
            return None, self.node_factory.create_prerequisite_node(
                "teeth_cleaning", "whitening_consultation", functions
            )
        
        # Continue with normal scheduling
        functions = [self.provide_patient_info, self.back_to_main]
        return None, self.node_factory.create_whitening_consultation_node(functions)

# Add flow node
class FlowNodeFactory:
    def create_prerequisite_node(self, required_service: str, desired_service: str, functions: List) -> NodeConfig:
        required_info = self.clinic_info.get_service(required_service)
        desired_info = self.clinic_info.get_service(desired_service)
        
        system_prompt = f"""
        Pentru {desired_info["name"]}, este necesară mai întâi o {required_info["name"]}.
        
        Explicați pacientului că:
        1. {desired_info["name"]} necesită {required_info["name"]} în ultimele 6 luni
        2. Putem programa mai întâi {required_info["name"]}
        3. Oferă opțiunea de programare pentru serviciul necesar
        
        Serviciu necesar: {required_info["name"]} - {required_info["price"]}
        Serviciu dorit: {desired_info["name"]} - {desired_info["price"]}
        """
        
        return NodeConfig(
            system_prompt=system_prompt,
            tools=self._build_tools(functions)
        )
```

### 10.4 System Monitoring Extensions

**Metrics Collection Extension**:
```python
class MetricsCollector:
    def __init__(self):
        self.conversation_metrics = defaultdict(int)
        self.appointment_metrics = defaultdict(int)
        self.error_metrics = defaultdict(int)
    
    def track_conversation_start(self, platform: str):
        self.conversation_metrics[f"{platform}_conversations_started"] += 1
    
    def track_appointment_created(self, service: str):
        self.appointment_metrics[f"appointments_{service}"] += 1
    
    def track_error(self, component: str, error_type: str):
        self.error_metrics[f"{component}_{error_type}"] += 1

# Integration example
class ConversationHandlers:
    def __init__(self, clinic_info, appointment_system, node_factory, 
                 conversation_state, metrics_collector=None):
        # ... existing init
        self.metrics = metrics_collector or MetricsCollector()
    
    async def create_appointment(self, *args, **kwargs):
        try:
            result = await self._create_appointment_internal(*args, **kwargs)
            self.metrics.track_appointment_created(kwargs.get("service", "unknown"))
            return result
        except Exception as e:
            self.metrics.track_error("appointment_system", type(e).__name__)
            raise
```

---

## 📋 Summary

This system architecture provides:

**Scalability**: Modular design allows independent scaling of components
**Maintainability**: Clear separation of concerns and well-defined interfaces
**Extensibility**: Multiple extension points for new platforms and features
**Resilience**: Comprehensive error handling and recovery mechanisms
**Testability**: Each component can be tested independently with clear contracts

**Key Architectural Decisions**:
1. **Layered Architecture**: Separation between UI, transport, processing, and business logic
2. **Interface-Based Design**: Abstract interfaces allow easy component replacement
3. **Factory Patterns**: Configuration-driven component creation
4. **Session Management**: Multi-user support with proper state isolation
5. **Unified Data Models**: Consistent data structures across different platforms

This architecture serves as the foundation for building robust, scalable AI assistants that can operate across multiple platforms while maintaining consistent business logic and user experience.