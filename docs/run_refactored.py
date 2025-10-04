#!/usr/bin/env python3

#
# Copyright (c) 2024-2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Run the refactored dental clinic assistant.

This script ensures you're running the new OOP-based refactored version
rather than the original monolithic version.
"""

import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the refactored bot function
try:
    from dental_clinic_assistant import bot
    print("✅ Successfully loaded refactored dental clinic assistant")
except ImportError as e:
    print(f"❌ Failed to import refactored assistant: {e}")
    sys.exit(1)

# Export for pipecat runner
__all__ = ["bot"]

if __name__ == "__main__":
    print("🦷 Starting Refactored Dental Clinic Assistant...")
    print("📚 Using Object-Oriented Architecture")
    print("🔗 Components: ClinicInfo, AppointmentSystem, ConversationHandlers, FlowNodeFactory")
    print()
    
    # Run using pipecat runner
    from pipecat.runner.run import main
    main()