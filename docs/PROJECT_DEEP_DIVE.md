# Dental Clinic Assistant: A Deep Dive

This document provides a comprehensive overview of the Dental Clinic Assistant project, built with the `pipecat` framework. It covers everything from the high-level architecture to the low-level implementation details, guiding you on how to use, customize, and integrate the assistant into your own applications.

## 1. Project Overview

### What is the Dental Clinic Assistant?
The Dental Clinic Assistant is a sophisticated, AI-powered virtual assistant designed to handle the administrative and customer service tasks of a dental clinic. It can communicate with patients through both voice and text, answer questions about the clinic, and manage appointments.

Built on the `pipecat` real-time AI framework, it serves as an advanced example of how to create modular, extensible, and production-ready conversational applications. The project is intentionally designed with clear, separated components to demonstrate best practices in software engineering for AI systems.

### Key Features
- **Conversational AI**: Engages in natural, human-like conversations using voice or text.
- **Appointment Management**: Allows patients to schedule, reschedule, and cancel appointments.
- **Symptom Triage**: Intelligently recommends dental services based on user-described symptoms.
- **Clinic Information Provider**: Answers questions about clinic services, dentists, hours, and location.
- **Modular & Extensible**: Designed to be easily customized and extended with new features, appointment systems, or communication platforms.
- **Multi-Backend Support**: Includes a mock appointment system for easy testing and a full-featured Google Calendar integration for production use.

---

## 2. System Architecture

### High-Level Diagram
The system is designed with a modular architecture, separating concerns to make it maintainable and extensible. The diagram below shows the key components and their interactions:

```
[User (Voice/Text)] <--> [Transport (Daily, WebSocket)] <--> [Pipecat Pipeline]
                                                                    |
+-------------------------------------------------------------------+
| Pipecat Pipeline                                                  |
|                                                                   |
|  [STT Service] -> [LLM Service] -> [TTS Service]                  |
|       ^               |                ^                          |
|       |               v                |                          |
|       +-------[Flow Manager]-----------+                          |
|                       |                                           |
+-----------------------|-------------------------------------------+
                        |
                        v
+-----------------------+-------------------------------------------+
| Application Logic                                                 |
|                                                                   |
|  [ConversationHandlers] <-> [FlowNodeFactory]                     |
|         |                                                         |
|         +------------> [AppointmentSystem] (Mock or Google)       |
|         |                                                         |
|         +------------> [ClinicInfo]                               |
|                                                                   |
+-------------------------------------------------------------------+
```

### Core Components
- **`dental_clinic_assistant.py`**: This is the main orchestrator. It initializes all other components, configures the `pipecat` pipeline, and sets up the event handlers for the conversation.
- **`clinic_info.py`**: Acts as a centralized database for all static clinic information. It holds data about services, dentists, business hours, and contact details, making it easy to update this information without changing the core logic.
- **`appointment_systems.py`**: Defines a common `AppointmentSystemInterface` for appointment management and provides two implementations:
    - `MockAppointmentSystem`: An in-memory system for easy testing and development without external dependencies.
    - `GoogleCalendarAppointmentSystem`: A production-ready system that connects to the Google Calendar API to manage real appointments.
- **`conversation_handlers.py`**: This is the brain of the assistant. It contains all the business logic for handling different conversational paths, such as providing information, scheduling an appointment, or managing an existing one. It also manages the `ConversationState`.
- **`flow_nodes.py`**: This component is responsible for creating the prompts and defining the functions available to the LLM at each step of the conversation. It ensures the LLM has the right context and tools to respond appropriately.
- **`pipecat` Framework**: The engine that powers the real-time communication. It handles the complex tasks of audio input/output, streaming data between services (STT, LLM, TTS), and managing the overall pipeline.

---

## 3. How It Works: The Pipecat Flow

### What is Pipecat?
`pipecat` is a framework for building real-time, multimodal, and conversational AI applications. It simplifies the process of streaming audio, video, and other data between different services, such as speech-to-text, large language models, and text-to-speech. Its pipeline-based architecture is ideal for creating responsive voice bots like the Dental Clinic Assistant.

### The Pipeline
The core of the assistant's real-time functionality is its `pipecat` pipeline, defined in `dental_clinic_assistant.py`. The pipeline defines the journey of data from the user to the AI and back again.

```python
pipeline = Pipeline([
    transport.input(),
    stt,
    context_aggregator.user(),
    llm,
    tts,
    transport.output(),
    context_aggregator.assistant(),
])
```

1.  **`transport.input()`**: This is the entry point for the user's audio. The transport (e.g., Daily for WebRTC, or a WebSocket) receives the audio stream from the user's microphone.
2.  **`stt` (Speech-to-Text)**: The raw audio data is streamed to an STT service (like Soniox), which transcribes it into text in real-time.
3.  **`context_aggregator.user()`**: The transcribed text is added to the conversation history as a user message.
4.  **`llm` (Large Language Model)**: The updated conversation context is sent to an LLM (like OpenAI's GPT-4o). The LLM processes the user's request based on the prompt provided by the current `FlowNode`.
5.  **`tts` (Text-to-Speech)**: The LLM's text response is streamed to a TTS service (like ElevenLabs), which converts it into audio.
6.  **`transport.output()`**: The generated audio is sent back to the user through the transport, so they can hear the assistant's response.
7.  **`context_aggregator.assistant()`**: The assistant's response is also added to the conversation history, keeping the context up-to-date for the next turn.

### The Flow Manager
While `pipecat` manages the data pipeline, the `pipecat-flows` extension manages the *logic* of the conversation. The `FlowManager` is the key component that connects the `pipecat` pipeline to the application's business logic.

-   **Stateful Conversations**: The `FlowManager` allows the conversation to move between different states, called "nodes." Each node has its own specific prompt and a set of functions that the LLM can call.
-   **`NodeConfig`**: Each node is defined by a `NodeConfig` object, created by the `FlowNodeFactory`. This object contains the system prompt and the list of Python functions that are available to be called from that node.
-   **Function-Based Routing**: Instead of relying on the LLM to guess the next step, the `FlowManager` uses function calls to drive the conversation forward. When the LLM calls a function (e.g., `schedule_appointment`), the corresponding Python function in `ConversationHandlers` is executed. This function then returns the next `NodeConfig`, effectively transitioning the conversation to a new state.

This combination of a real-time data pipeline and a stateful flow manager allows the Dental Clinic Assistant to have dynamic, context-aware, and reliable conversations.

---

## 4. Core Components Explained

### `dental_clinic_assistant.py`
This file contains the `DentalClinicAssistant` class, which acts as the central hub of the application. Its primary responsibilities are:
- **Initialization**: In its `__init__` method, it creates instances of all the core components: `ClinicInfo`, `ConversationState`, `AppointmentSystem`, `FlowNodeFactory`, and `ConversationHandlers`. This dependency injection makes the system modular and easy to test.
- **Pipeline Configuration**: The `run_bot` method is where the `pipecat` pipeline is defined. It specifies which STT, LLM, and TTS services to use and wires them together with a transport.
- **Flow Management**: It initializes the `FlowManager` and sets up the event handlers (e.g., `on_client_connected`) that kick off the conversation. When a user connects, it uses the `ConversationHandlers` to get the initial set of functions and the `FlowNodeFactory` to create the first conversational node.
- **Environment-Based Configuration**: The file includes logic to create the assistant instance based on environment variables. This allows you to switch between the `mock` and `google_calendar` appointment systems by simply changing the `APPOINTMENT_SYSTEM_TYPE` variable.

### `clinic_info.py`
The `ClinicInfo` class is a simple but crucial component that acts as a centralized data repository for the clinic.
- **Single Source of Truth**: It holds all the static information about the clinic—name, address, phone number, hours, services, and dentist profiles. This separation of data from logic means you can update clinic details without touching any other part of the code.
- **Helper Methods**: It provides convenient helper methods like `get_services_text()` and `get_dentists_text()` to format the data for display, ensuring a consistent presentation.
- **Symptom-to-Service Mapping**: A key feature is the `symptom_mapping` dictionary, which allows the assistant to perform intelligent triage. It maps keywords related to patient symptoms (e.g., "pain," "cavity") to the appropriate dental service, enabling the assistant to make helpful recommendations.

### `appointment_systems.py`
This file defines the logic for managing appointments. It uses an interface-based design to support multiple backends.
- **`AppointmentSystemInterface`**: This abstract base class defines the contract for any appointment system. It declares methods like `check_availability`, `create_appointment`, and `find_appointment`, ensuring that any new backend will be compatible with the existing logic.
- **`MockAppointmentSystem`**: This is a simple, in-memory implementation of the interface. It doesn't connect to any external services and is perfect for development and testing, as it allows you to run the assistant without needing API keys or internet access.
- **`GoogleCalendarAppointmentSystem`**: This is a production-ready implementation that integrates with the Google Calendar API. It can check for busy times on a real calendar, create new events for appointments, and find existing appointments, making the assistant truly functional for a real clinic.

### `conversation_handlers.py`
This is where the core business logic of the assistant resides. The `ConversationHandlers` class orchestrates the flow of the conversation.
- **State Management**: It works closely with the `ConversationState` class to keep track of important information during the conversation, such as the patient's name, their selected service, and any available appointment slots.
- **Function-Based Logic**: Each public method in this class represents a specific action the user might take (e.g., `get_services_info`, `schedule_appointment`, `confirm_appointment`). These are the functions that the LLM can call.
- **Routing the Conversation**: When a function is called, it performs its business logic (e.g., checking for available slots) and then returns the next `NodeConfig` to the `FlowManager`. This is how the conversation transitions from one state to the next. For example, after `provide_patient_info` is successfully executed, it returns the `service_selection` node.

### `flow_nodes.py`
The `FlowNodeFactory` is responsible for crafting the prompts that are sent to the LLM at each step of the conversation.
- **Dynamic Prompt Generation**: Each method in this class (e.g., `create_initial_node`, `create_appointment_confirmation_node`) creates a `NodeConfig` object. This object contains a carefully crafted system prompt that gives the LLM its instructions for that specific conversational state.
- **Contextual Information**: The prompts are dynamic and include relevant context from the `ConversationState`. For example, the `create_appointment_confirmation_node` includes the patient's name and selected time in its prompt, so the LLM can ask for confirmation.
- **Defining Available Actions**: Crucially, each `NodeConfig` also includes the list of functions from `ConversationHandlers` that the LLM is allowed to call from that state. This constrains the LLM's behavior and ensures that the conversation follows a logical path. For instance, from the confirmation node, the LLM can either call `confirm_appointment` or `modify_appointment_details`.

---

## 5. Getting Started

This section will guide you through setting up and running the Dental Clinic Assistant on your local machine.

### Prerequisites
To run the full voice-enabled assistant, you will need to sign up for accounts with the following services and obtain API keys:
- **OpenAI**: For the LLM (GPT-4o).
- **ElevenLabs**: For the TTS service.
- **Soniox**: For the STT service.

You will also need a local installation of Python (version 3.9 or higher).

### Installation
1.  **Clone the Repository**: If you haven't already, clone the `pipecat-python` repository to your local machine.
2.  **Navigate to the Project Directory**: Open your terminal and navigate to the `examples/dental_clinic` directory.
3.  **Create a Virtual Environment**: It is highly recommended to use a virtual environment to manage dependencies.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```
4.  **Install Dependencies**: Install all the required Python packages using pip.
    ```bash
    pip install -r requirements.txt
    ```
5.  **Set Up Environment Variables**: Create a `.env` file in the project directory by copying the example file.
    ```bash
    cp .env.example .env
    ```
    Now, open the `.env` file and add your API keys:
    ```
    OPENAI_API_KEY="sk-..."
    ELEVENLABS_API_KEY="..."
    SONIOX_API_KEY="..."
    ```

### Running the Assistant
Once the installation is complete, you can run the assistant from your terminal.

1.  **Ensure your virtual environment is active.**
2.  **Run the `main.py` script**:
    ```bash
    python main.py
    ```
    This will start the `pipecat` runner and make the assistant available to connect to. By default, it will use the `MockAppointmentSystem`.

### Configuration Options
You can customize the assistant's behavior using environment variables in your `.env` file:

-   **`APPOINTMENT_SYSTEM_TYPE`**: Controls which appointment system to use.
    -   `mock` (default): Uses the in-memory `MockAppointmentSystem`.
    -   `google_calendar`: Uses the `GoogleCalendarAppointmentSystem`.
-   **`GOOGLE_SERVICE_ACCOUNT_FILE`**: If using `google_calendar`, this should be the path to your Google Cloud service account credentials JSON file (defaults to `service-account-credentials.json`).
-   **`GOOGLE_DOCTOR_CALENDAR_ID`**: The ID of the Google Calendar to use for appointments.

To run with Google Calendar, your `.env` file might look like this:
```
#... (other API keys)
APPOINTMENT_SYSTEM_TYPE="google_calendar"
GOOGLE_SERVICE_ACCOUNT_FILE="path/to/your/credentials.json"
GOOGLE_DOCTOR_CALENDAR_ID="your_calendar_id@group.calendar.google.com"
```

---

## 6. How to Customize and Extend

The modular design of the Dental Clinic Assistant makes it easy to customize and extend. Here are a few common scenarios:

### Changing Clinic Information
To adapt the assistant for a different clinic, you only need to modify one file: `clinic_info.py`.

1.  **Open `clinic_info.py`**.
2.  **Update the `_info` dictionary**: Change the values for `name`, `address`, `phone`, `email`, and `hours` to match the new clinic's details.
3.  **Modify Services**: Update the `services` dictionary with the new clinic's services, including their descriptions, durations, and prices.
4.  **Update Dentists**: Edit the `dentists` list to reflect the new clinic's staff.
5.  **Adjust Symptom Mapping**: Review and update the `symptom_mapping` dictionary to align with the new services and common patient inquiries.

### Adding a New Service
Let's say you want to add a new service, "Dental Implants." Here's how you would do it:

1.  **Update `clinic_info.py`**: Add the new service to the `services` dictionary.
    ```python
    "implants": {
        "name": "Implanturi Dentare",
        "description": "Soluții de lungă durată pentru înlocuirea dinților lipsă",
        "duration": 120,
        "price": "8000-12000 RON"
    }
    ```
2.  **Update Symptom Mapping (Optional)**: If relevant, add keywords for the new service to the `symptom_mapping` in `clinic_info.py`.
    ```python
    "implants": {
        "keywords": ["implant", "înlocuire dinte", "dinte lipsă"],
        "service": "implants",
        "priority": "medium",
        "message": "Pentru înlocuirea dinților lipsă, vă recomand o consultație pentru implanturi dentare."
    }
    ```
3.  **That's it!** The system is designed to automatically pick up the new service from `ClinicInfo`. The `get_services_info` handler will include it in the list of services, and the `select_service` function will be able to handle it without any changes.

### Integrating a Different Calendar System
To use a different calendar system (e.g., Microsoft Outlook), you can create a new appointment system class.

1.  **Create a New Class**: In `appointment_systems.py`, create a new class called `OutlookCalendarAppointmentSystem` that inherits from `AppointmentSystemInterface`.
    ```python
    class OutlookCalendarAppointmentSystem(AppointmentSystemInterface):
        # ...
    ```
2.  **Implement the Interface Methods**: You must implement all the abstract methods defined in the interface: `check_availability`, `get_available_slots`, `create_appointment`, `cancel_appointment`, `update_appointment`, and `find_appointment`. The logic inside these methods will be specific to the Microsoft Graph API (for Outlook).
3.  **Update the Factory**: In the `AppointmentSystemFactory`, add a new condition to create an instance of your new class.
    ```python
    class AppointmentSystemFactory:
        @staticmethod
        def create_system(system_type: str = "mock", **kwargs) -> AppointmentSystemInterface:
            if system_type == "mock":
                return MockAppointmentSystem()
            elif system_type == "google_calendar":
                return GoogleCalendarAppointmentSystem(**kwargs)
            elif system_type == "outlook": # Add this
                return OutlookCalendarAppointmentSystem(**kwargs)
            else:
                raise ValueError(f"Unknown appointment system type: {system_type}")
    ```
4.  **Update Configuration**: Set the `APPOINTMENT_SYSTEM_TYPE` environment variable in your `.env` file to `"outlook"`.

---

## 7. Web Application Integration

You can integrate the Dental Clinic Assistant into a web application to provide a seamless user experience. This typically involves connecting a frontend (built with HTML, CSS, and JavaScript) to the running `pipecat` assistant via WebSockets.

### Connecting to the Assistant
When you run the assistant with `python main.py`, it starts a WebSocket server (by default on `localhost:8000`). A web application can connect to this server to stream the user's microphone audio to the assistant and receive the assistant's audio response.

The `pipecat` framework handles the complexities of the WebSocket communication and the audio streaming. On the frontend, you would use JavaScript to:
1.  Request microphone access from the user.
2.  Establish a WebSocket connection to the `pipecat` server.
3.  Stream the raw audio data from the microphone over the WebSocket.
4.  Receive the assistant's audio response from the WebSocket and play it through the user's speakers.

### Frontend Example
Here is a conceptual example of a simple HTML and JavaScript client that could connect to the assistant.

**HTML (`index.html`)**
```html
<!DOCTYPE html>
<html>
<head>
    <title>Dental Clinic Assistant</title>
</head>
<body>
    <h1>Dental Clinic Assistant</h1>
    <button id="startButton">Start Conversation</button>
    <button id="stopButton" disabled>Stop Conversation</button>
    <div id="status">Status: Disconnected</div>
</body>
<script src="app.js"></script>
</html>
```

**JavaScript (`app.js`)**
```javascript
const startButton = document.getElementById('startButton');
const stopButton = document.getElementById('stopButton');
const statusDiv = document.getElementById('status');

let socket;
let mediaRecorder;

startButton.onclick = async () => {
    // 1. Get user media (microphone)
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    // 2. Create a WebSocket connection
    socket = new WebSocket('ws://localhost:8000/websocket');

    socket.onopen = () => {
        statusDiv.textContent = 'Status: Connected';
        startButton.disabled = true;
        stopButton.disabled = false;

        // 3. Start recording and sending audio
        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                socket.send(event.data);
            }
        };
        mediaRecorder.start(250); // Send data every 250ms
    };

    socket.onmessage = (event) => {
        // 4. Receive audio from server and play it
        const audioBlob = new Blob([event.data], { type: 'audio/mpeg' });
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        audio.play();
    };

    socket.onclose = () => {
        statusDiv.textContent = 'Status: Disconnected';
        startButton.disabled = false;
        stopButton.disabled = true;
    };
};

stopButton.onclick = () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
    }
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.close();
    }
};
```

### Best Practices
-   **Manage State**: Keep track of the connection state on the frontend (e.g., "connecting," "connected," "disconnected") to provide clear feedback to the user.
-   **Handle Errors**: Implement error handling for cases where microphone access is denied or the WebSocket connection fails.
-   **Use a Robust Client**: For production applications, consider using a more robust WebSocket client library that can handle automatic reconnections.
-   **User Interface**: Design a user interface that clearly indicates when the assistant is listening and when it is speaking. This can be done by changing the color or style of a button or displaying a message.
-   **Transcription Display**: For a richer user experience, you can configure the `pipecat` pipeline to send back text transcriptions of both the user's and the assistant's speech, which you can then display on the screen.