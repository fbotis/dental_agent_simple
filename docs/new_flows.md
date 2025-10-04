# Pipecat Flows Documentation

This document explains the core components and conversation flow of a `pipecat-flows` bot. Understanding this architecture will help you design more effective prompts and build robust conversational AI.

## Core Components

The bot's architecture is built around three main components: `FlowManager`, `ActionManager`, and `LLMAdapter`.

### 1. `FlowManager`

The `FlowManager` is the central orchestrator of the conversation. It manages the state of the conversation, transitions between different nodes (states), and coordinates all interactions with the LLM.

**Key Responsibilities:**

- **State Management:** Maintains a shared state dictionary (`flow_manager.state`) that persists across different nodes, allowing you to store and retrieve data throughout the conversation.
- **Node Transitions:** Manages the flow of the conversation by transitioning between different nodes. Each node represents a specific state in the conversation and has its own set of prompts, functions, and actions.
- **Function Registration:** Registers and manages functions that can be called by the LLM. These functions can be used to perform specific tasks, such as fetching data from an API or interacting with a database.
- **Context Management:** Manages the conversation context that is sent to the LLM. It supports different strategies for updating the context, such as appending new messages, resetting the context, or summarizing the conversation.

### 2. `ActionManager`

The `ActionManager` is responsible for executing actions that have side effects, such as sending a text-to-speech (TTS) message, ending the conversation, or calling a custom function. Actions are defined within a node and can be executed either before (`pre_actions`) or after (`post_actions`) the LLM is called.

**Key Responsibilities:**

- **Action Execution:** Executes a list of actions in a specific order.
- **Built-in Actions:** Provides built-in actions for common tasks, such as `tts_say` and `end_conversation`.
- **Custom Actions:** Allows you to register and execute custom actions to perform specific tasks.

### 3. `LLMAdapter`

The `LLMAdapter` is responsible for normalizing the differences between various LLM providers (e.g., OpenAI, Anthropic, Gemini). It ensures that the `FlowManager` can work with different LLMs without changing its core logic.

**Key Responsibilities:**

- **Function Formatting:** Formats function definitions into the specific format required by each LLM provider.
- **Message Formatting:** Formats messages (e.g., system prompts, user messages) into the correct format for each provider.
- **Summary Generation:** Provides a consistent way to generate conversation summaries across different LLMs.

## Conversation Flow

The conversation flow is a sequence of steps that are executed for each turn of the conversation. Here's a step-by-step breakdown:

1.  **Initialization:** The `FlowManager` is initialized with a specific configuration, which can be either a static flow with predefined nodes or a dynamic flow where nodes are determined at runtime.

2.  **Node Setup:** The conversation starts at an initial node. When a new node is set, the `FlowManager` performs the following steps:
    *   **Execute `pre_actions`:** Any actions defined in the `pre_actions` list of the node are executed.
    *   **Register Functions:** The functions defined in the node are registered with the LLM.
    *   **Update LLM Context:** The LLM context is updated with the new role and task messages from the node.
    *   **Trigger LLM:** The `FlowManager` sends the updated context to the LLM to get a response.
    *   **Execute `post_actions`:** Any actions defined in the `post_actions` list are executed after the LLM response is received.

3.  **LLM Interaction:** The LLM processes the context and can either return a text response or call one of the registered functions.

4.  **Function Execution:** If the LLM calls a function, the `FlowManager` executes the corresponding function handler. The handler can perform a specific task and optionally return a result to the LLM.

5.  **Node Transition:** Based on the LLM's response or the result of a function call, the `FlowManager` can transition to a new node. This is done by calling `flow_manager.set_node()` with the configuration of the new node.

6.  **State Updates:** Throughout the flow, you can use `flow_manager.state` to store and retrieve data that needs to be persisted across different nodes.

## Prompts and Functions

Prompts and functions are the key to designing effective conversations.

-   **Prompts:** Each node has `role_messages` and `task_messages` that define the context for the LLM.
    -   `role_messages`: These are typically system prompts that define the persona and high-level instructions for the bot.
    -   `task_messages`: These are prompts that define the specific task for the current node.
-   **Functions:** Functions allow the LLM to perform specific actions. They are defined in each node and can be used to:
    -   Fetch data from external sources.
    -   Interact with databases or other services.
    -   Transition the conversation to a new node.

By carefully designing your prompts and functions for each node, you can create a flexible and powerful conversational AI that can handle a wide range of user interactions.

## Example Analysis: `food_ordering.py`

To make this more concrete, let's analyze the `food_ordering.py` example. This bot guides a user through ordering either pizza or sushi.

### Conversation Flow Diagram

```
[Initial Node] --choose_pizza--> [Pizza Node] --select_pizza_order--> [Confirmation Node] --complete_order--> [End Node]
      |                                                                       ^
      |                                                                       |
      '--choose_sushi--> [Sushi Node] --select_sushi_order--------------------'
                                                                              |
                                                                              |
      '<--revise_order--------------------------------------------------------'
```

### Node-by-Node Breakdown

1.  **Initial Node (`initial`)**
    *   **Purpose:** Greets the user and asks them to choose between pizza and sushi.
    *   **Prompts:** The `role_messages` set the bot's persona as a friendly phone assistant, while the `task_messages` instruct it to ask for the user's choice.
    *   **Actions:** Before the conversation starts, a `pre_action` (`check_kitchen_status`) is run to log a message.
    *   **Functions & Transitions:**
        *   `choose_pizza`: If the user wants pizza, the LLM calls this function. The function's handler returns a new `NodeConfig` created by `create_pizza_node()`, transitioning the flow.
        *   `choose_sushi`: Similarly, this function transitions the flow to the sushi ordering node created by `create_sushi_node()`.

2.  **Pizza Node (`choose_pizza`)**
    *   **Purpose:** Collects the specifics of the pizza order (size and type).
    *   **Prompts:** The `task_messages` guide the LLM to ask for the size and type of pizza and provide pricing information.
    *   **Functions & Transitions:**
        *   `select_pizza_order`: This function is called when the user provides the size and type. The handler calculates the price, stores the complete order details in `flow_manager.state`, and transitions the flow to the `create_confirmation_node()`.

3.  **Sushi Node (`choose_sushi`)**
    *   **Purpose:** Collects the specifics of the sushi order (count and type).
    *   **Prompts:** The `task_messages` guide the LLM to ask for the number of rolls and the type, providing the price per roll.
    *   **Functions & Transitions:**
        *   `select_sushi_order`: Similar to the pizza node, this function's handler processes the user's choice, stores it in `flow_manager.state`, and transitions to the `create_confirmation_node()`.

4.  **Confirmation Node (`confirm`)**
    *   **Purpose:** Confirms the final order with the user.
    *   **Prompts:** The `task_messages` instruct the LLM to read back the order details (which it can access from the context) and ask for confirmation.
    *   **Functions & Transitions:**
        *   `complete_order`: If the user confirms, this function is called, and its handler transitions the flow to the `create_end_node()`.
        *   `revise_order`: If the user wants to change their order, this function's handler transitions the flow back to the `create_initial_node()`, restarting the process.

5.  **End Node (`end`)**
    *   **Purpose:** Politely ends the conversation.
    *   **Prompts:** The `task_messages` instruct the LLM to thank the user and say goodbye.
    *   **Actions:** A `post_action` of type `end_conversation` is executed, which gracefully terminates the pipeline.