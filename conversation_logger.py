"""Conversation logger for capturing and saving bot conversations."""

import os
from datetime import datetime
from typing import Optional, Dict, Any

from loguru import logger
from pipecat.frames.frames import (
    BotStartedSpeakingFrame,
    BotStoppedSpeakingFrame,
    EndFrame,
    FunctionCallInProgressFrame,
    FunctionCallResultFrame,
    LLMFullResponseEndFrame,
    LLMFullResponseStartFrame,
    LLMMessagesAppendFrame,
    LLMMessagesUpdateFrame,
    LLMTextFrame,
    StartFrame,
    TranscriptionFrame,
    TTSTextFrame,
    UserStartedSpeakingFrame,
    UserStoppedSpeakingFrame,
)
from pipecat.observers.base_observer import BaseObserver, FramePushed
from pipecat.processors.frame_processor import FrameDirection


class ConversationLogger(BaseObserver):
    """Observer that logs full conversations to individual text files."""

    def __init__(self, conversations_dir: str = "conversations"):
        """Initialize the conversation logger.

        Args:
            conversations_dir: Directory where conversation files will be saved.
        """
        super().__init__()
        self._conversations_dir = conversations_dir
        self._current_conversation: Optional[Dict[str, Any]] = None
        self._processed_frames = set()

        # Text buffering for streaming responses
        self._llm_response_buffer = ""
        self._tts_response_buffer = ""
        self._is_llm_streaming = False
        self._is_tts_streaming = False

        # Flow state tracking
        self._current_node = None
        self._function_calls = []

        # Ensure conversations directory exists
        os.makedirs(conversations_dir, exist_ok=True)
        logger.info(f"💬 Conversation logger initialized, saving to: {conversations_dir}")

    async def on_push_frame(self, data: FramePushed):
        """Process frames and log conversation data.

        Args:
            data: Frame push event containing the frame and direction information.
        """
        # Only process downstream frames
        if data.direction != FrameDirection.DOWNSTREAM:
            return

        # Skip already processed frames
        if data.frame.id in self._processed_frames:
            return

        self._processed_frames.add(data.frame.id)

        # Handle conversation start
        if isinstance(data.frame, StartFrame):
            await self._start_conversation()

        # Handle conversation end
        elif isinstance(data.frame, EndFrame):
            await self._end_conversation()

        # Handle user speech events
        elif isinstance(data.frame, UserStartedSpeakingFrame):
            await self._log_event("USER_STARTED_SPEAKING")

        elif isinstance(data.frame, UserStoppedSpeakingFrame):
            await self._log_event("USER_STOPPED_SPEAKING")

        # Handle bot speech events
        elif isinstance(data.frame, BotStartedSpeakingFrame):
            await self._log_event("BOT_STARTED_SPEAKING")
            await self._start_tts_response()

        elif isinstance(data.frame, BotStoppedSpeakingFrame):
            await self._log_event("BOT_STOPPED_SPEAKING")
            await self._end_tts_response()

        # Handle transcriptions (user input)
        elif isinstance(data.frame, TranscriptionFrame):
            await self._log_transcription(data.frame.text)

        # Handle LLM response streaming
        elif isinstance(data.frame, LLMFullResponseStartFrame):
            await self._start_llm_response()

        elif isinstance(data.frame, LLMTextFrame):
            await self._buffer_llm_response(data.frame.text)

        elif isinstance(data.frame, LLMFullResponseEndFrame):
            await self._end_llm_response()

        # Handle TTS text (bot output) - buffer streaming words
        elif isinstance(data.frame, TTSTextFrame):
            await self._buffer_tts_text(data.frame.text)

        # Handle function calls
        elif isinstance(data.frame, FunctionCallInProgressFrame):
            await self._log_function_call(data.frame)

        elif isinstance(data.frame, FunctionCallResultFrame):
            await self._log_function_result(data.frame)

        # Handle LLM context updates (node transitions)
        elif isinstance(data.frame, (LLMMessagesAppendFrame, LLMMessagesUpdateFrame)):
            await self._log_context_update(data.frame)

    async def _start_conversation(self):
        """Start a new conversation log."""
        timestamp = datetime.now()
        conversation_id = timestamp.strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
        filename = f"conversation_{conversation_id}.txt"
        filepath = os.path.join(self._conversations_dir, filename)

        self._current_conversation = {
            "id": conversation_id,
            "filepath": filepath,
            "start_time": timestamp,
            "events": []
        }

        # Write conversation header
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"DENTAL CLINIC ASSISTANT CONVERSATION LOG\n")
            f.write("=" * 80 + "\n")
            f.write(f"Conversation ID: {conversation_id}\n")
            f.write(f"Start Time: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")

        logger.info(f"📝 Started new conversation log: {filename}")

    async def _end_conversation(self):
        """End the current conversation log."""
        if not self._current_conversation:
            return

        # Flush any remaining TTS buffer before ending
        if self._tts_response_buffer.strip():
            complete_response = self._tts_response_buffer.strip()
            await self._log_event("BOT_SPEECH", complete_response)
            with open(self._current_conversation["filepath"], 'a', encoding='utf-8') as f:
                f.write(f"🤖 ASSISTANT: {complete_response}\n\n")
            self._tts_response_buffer = ""
            self._is_tts_streaming = False

        end_time = datetime.now()
        duration = end_time - self._current_conversation["start_time"]

        # Write conversation summary
        with open(self._current_conversation["filepath"], 'a', encoding='utf-8') as f:
            f.write("\n" + "=" * 80 + "\n")
            f.write("CONVERSATION SUMMARY\n")
            f.write("=" * 80 + "\n")
            f.write(f"End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Duration: {duration}\n")
            f.write(f"Total Events: {len(self._current_conversation['events'])}\n")

            # Count different event types
            event_counts = {}
            for event in self._current_conversation['events']:
                event_type = event.get('type', 'UNKNOWN')
                event_counts[event_type] = event_counts.get(event_type, 0) + 1

            f.write("\nEvent Breakdown:\n")
            for event_type, count in sorted(event_counts.items()):
                f.write(f"  - {event_type}: {count}\n")

            f.write("=" * 80 + "\n")

        logger.info(f"✅ Completed conversation log: {os.path.basename(self._current_conversation['filepath'])}")
        logger.info(f"   Duration: {duration}, Events: {len(self._current_conversation['events'])}")

        self._current_conversation = None

    async def _log_event(self, event_type: str, content: str = ""):
        """Log a general conversation event.

        Args:
            event_type: Type of event (e.g., USER_STARTED_SPEAKING).
            content: Optional event content.
        """
        if not self._current_conversation:
            return

        timestamp = datetime.now()
        event = {
            "type": event_type,
            "timestamp": timestamp,
            "content": content
        }

        self._current_conversation['events'].append(event)

        # Write to file
        with open(self._current_conversation["filepath"], 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp.strftime('%H:%M:%S.%f')[:-3]}] {event_type}")
            if content:
                f.write(f": {content}")
            f.write("\n")

    async def _log_transcription(self, text: str):
        """Log user speech transcription.

        Args:
            text: Transcribed user speech.
        """
        if not self._current_conversation or not text.strip():
            return

        await self._log_event("USER_SPEECH", text.strip())

        # Also write formatted user input
        with open(self._current_conversation["filepath"], 'a', encoding='utf-8') as f:
            f.write(f"\n👤 USER: {text.strip()}\n")

    async def _start_llm_response(self):
        """Start buffering a new LLM response."""
        self._llm_response_buffer = ""
        self._is_llm_streaming = True

    async def _buffer_llm_response(self, text: str):
        """Buffer LLM response text chunks.

        Args:
            text: LLM text chunk to buffer.
        """
        if self._is_llm_streaming:
            self._llm_response_buffer += text

    async def _end_llm_response(self):
        """End LLM response buffering and log the complete response."""
        if not self._current_conversation or not self._is_llm_streaming:
            return

        self._is_llm_streaming = False
        complete_response = self._llm_response_buffer.strip()

        if complete_response:
            await self._log_event("LLM_RESPONSE", complete_response)

            # Also write formatted LLM thinking for analysis
            with open(self._current_conversation["filepath"], 'a', encoding='utf-8') as f:
                f.write(f"🧠 LLM THINKING: {complete_response}\n\n")

        self._llm_response_buffer = ""

    async def _start_tts_response(self):
        """Start buffering a new TTS response."""
        self._tts_response_buffer = ""
        self._is_tts_streaming = True

    async def _buffer_tts_text(self, text: str):
        """Buffer TTS text chunks.

        Args:
            text: TTS text chunk to buffer.
        """
        if self._is_tts_streaming:
            # Add space between words if buffer is not empty and doesn't end with space/punctuation
            if self._tts_response_buffer and not self._tts_response_buffer.endswith((' ', '\n', '.', '!', '?', ',')):
                self._tts_response_buffer += " "
            self._tts_response_buffer += text

    async def _end_tts_response(self):
        """End TTS response buffering and log the complete response."""
        if not self._current_conversation or not self._is_tts_streaming:
            return

        self._is_tts_streaming = False
        complete_response = self._tts_response_buffer.strip()

        if complete_response:
            await self._log_event("BOT_SPEECH", complete_response)

            # Also write formatted bot response
            with open(self._current_conversation["filepath"], 'a', encoding='utf-8') as f:
                f.write(f"🤖 ASSISTANT: {complete_response}\n\n")

        self._tts_response_buffer = ""

    def get_conversations_dir(self) -> str:
        """Get the conversations directory path.

        Returns:
            Path to the conversations directory.
        """
        return self._conversations_dir

    def get_current_conversation_id(self) -> Optional[str]:
        """Get the current conversation ID.

        Returns:
            Current conversation ID if active, None otherwise.
        """
        return self._current_conversation['id'] if self._current_conversation else None

    async def _log_function_call(self, frame: FunctionCallInProgressFrame):
        """Log function call in progress.

        Args:
            frame: Function call frame.
        """
        if not self._current_conversation:
            return

        timestamp = datetime.now()
        function_name = frame.function_name
        arguments = frame.arguments if hasattr(frame, 'arguments') else {}

        # Parse arguments if they're a string
        if isinstance(arguments, str):
            try:
                import json
                arguments = json.loads(arguments) if arguments else {}
            except:
                arguments = {"raw": arguments}

        # Format arguments for display
        args_str = ", ".join([f"{k}={v}" for k, v in arguments.items()]) if arguments else "no args"

        event = {
            "type": "FUNCTION_CALL",
            "timestamp": timestamp,
            "function": function_name,
            "arguments": arguments
        }

        self._current_conversation['events'].append(event)
        self._function_calls.append(event)

        # Write to file with clear visual separator
        with open(self._current_conversation["filepath"], 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp.strftime('%H:%M:%S.%f')[:-3]}] 📞 FUNCTION CALL: {function_name}({args_str})\n")

    async def _log_function_result(self, frame: FunctionCallResultFrame):
        """Log function call result.

        Args:
            frame: Function result frame.
        """
        if not self._current_conversation:
            return

        timestamp = datetime.now()
        function_name = frame.function_name
        result = frame.result if hasattr(frame, 'result') else None

        # Try to extract node name from result if it's a NodeConfig
        node_name = None
        try:
            if result and hasattr(result, '__iter__'):
                if len(result) == 2:
                    # Result is (None, NodeConfig) tuple
                    _, node_config = result
                    if hasattr(node_config, 'name'):
                        node_name = node_config.name
                elif hasattr(result, 'name'):
                    # Result might be just a NodeConfig
                    node_name = result.name
        except:
            pass  # Couldn't extract node name

        event = {
            "type": "FUNCTION_RESULT",
            "timestamp": timestamp,
            "function": function_name,
            "node": node_name
        }

        self._current_conversation['events'].append(event)

        # Write to file
        with open(self._current_conversation["filepath"], 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp.strftime('%H:%M:%S.%f')[:-3]}] ✅ FUNCTION RESULT: {function_name}")
            if node_name:
                f.write(f" → transitioning to node: {node_name}")
            f.write("\n")

        # Update current node if we got a new one
        if node_name:
            await self._log_node_transition(node_name)

    async def _log_node_transition(self, node_name: str):
        """Log a node transition.

        Args:
            node_name: Name of the new node.
        """
        if not self._current_conversation:
            return

        if self._current_node == node_name:
            return  # No transition

        old_node = self._current_node
        self._current_node = node_name

        timestamp = datetime.now()

        # Write to file with visual indicator
        with open(self._current_conversation["filepath"], 'a', encoding='utf-8') as f:
            if old_node:
                f.write(f"\n{'='*80}\n")
                f.write(f"🔄 NODE TRANSITION: {old_node} → {node_name}\n")
                f.write(f"{'='*80}\n\n")
            else:
                f.write(f"\n{'='*80}\n")
                f.write(f"🎯 INITIAL NODE: {node_name}\n")
                f.write(f"{'='*80}\n\n")

    async def _log_context_update(self, frame):
        """Log LLM context update (indicates possible node change).

        Args:
            frame: LLMMessagesAppendFrame or LLMMessagesUpdateFrame.
        """
        if not self._current_conversation:
            return

        # These frames often indicate a node change in pipecat-flows
        # We'll log them for debugging
        timestamp = datetime.now()
        frame_type = "CONTEXT_UPDATE"

        with open(self._current_conversation["filepath"], 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp.strftime('%H:%M:%S.%f')[:-3]}] 🔄 {frame_type}\n")
