#!/usr/bin/env python3

#
# Copyright (c) 2024-2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Main entry point for the refactored dental clinic voice assistant.

This example demonstrates a dental clinic assistant system using dynamic flows with
direct functions where conversation paths are determined at runtime.

The refactored version uses Object-Oriented Programming principles to organize
the code into logical components:

1. ClinicInfo - Manages clinic data and information
2. AppointmentSystemInterface - Abstract interface for appointment systems
3. MockAppointmentSystem/GoogleCalendarAppointmentSystem - Concrete implementations
4. FlowNodeFactory - Creates conversation flow nodes
5. ConversationHandlers - Service classes for different conversation types
6. DentalClinicAssistant - Main orchestrator class

Multi-LLM Support:
Set LLM_PROVIDER environment variable to choose your LLM provider.
Supported: openai (default), anthropic, google, aws

Requirements:
- CARTESIA_API_KEY (for TTS)
- DEEPGRAM_API_KEY (for STT)
- DAILY_API_KEY (for transport)
- LLM API key (varies by provider - see env.example)
"""

from dotenv import load_dotenv

# Load environment variables FIRST before importing anything else
load_dotenv()

try:
    from dental_clinic_assistant import bot
except ImportError:
    from .dental_clinic_assistant import bot


# Export bot function for pipecat runner compatibility
__all__ = ["bot"]


def main():
    """Main entry point for the dental clinic assistant."""
    # Run the assistant using pipecat runner
    from pipecat.runner.run import main as pipecat_main
    pipecat_main()


if __name__ == "__main__":
    main()