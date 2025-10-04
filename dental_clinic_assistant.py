#
# Copyright (c) 2024-2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Main dental clinic assistant orchestrator class."""

import os
from typing import Dict, List

from loguru import logger
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import create_transport
from pipecat.transcriptions.language import Language
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.services.soniox.stt import SonioxSTTService, SonioxInputParams
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.daily.transport import DailyParams
from pipecat.transports.websocket.fastapi import FastAPIWebsocketParams

from pipecat_flows import FlowManager

try:
    from .appointment_systems import AppointmentSystemFactory, AppointmentSystemInterface
    from .audio_recorder import AudioRecorder
    from .clinic_info import ClinicInfo
    from .conversation_handlers import ConversationState, ConversationHandlers
    from .conversation_logger import ConversationLogger
    from .flow_nodes import FlowNodeFactory
    from .metrics_observer import MetricsFileObserver
except ImportError:
    from appointment_systems import AppointmentSystemFactory, AppointmentSystemInterface
    from audio_recorder import AudioRecorder
    from clinic_info import ClinicInfo
    from conversation_handlers import ConversationState, ConversationHandlers
    from conversation_logger import ConversationLogger
    from flow_nodes import FlowNodeFactory
    from metrics_observer import MetricsFileObserver


class DentalClinicAssistant:
    """Main orchestrator class for the dental clinic voice assistant."""

    def __init__(self, appointment_system_type: str = "mock", **appointment_kwargs):
        """Initialize the dental clinic assistant."""
        logger.debug(f"🔧 Initializing DentalClinicAssistant components...")

        # Core components
        self.clinic_info = ClinicInfo()
        logger.debug(f"   ✓ ClinicInfo initialized: {self.clinic_info.name}")

        self.conversation_state = ConversationState()
        logger.debug(f"   ✓ ConversationState initialized")

        try:
            self.appointment_system = AppointmentSystemFactory.create_system(
                appointment_system_type, **appointment_kwargs
            )
            logger.debug(f"   ✓ Appointment system created: {appointment_system_type}")
        except Exception as e:
            logger.error(f"   ✗ Failed to create appointment system: {e}")
            raise

        # Factory and handlers
        self.node_factory = FlowNodeFactory(
            self.clinic_info, self.conversation_state.__dict__)
        logger.debug(f"   ✓ FlowNodeFactory initialized")

        self.conversation_handlers = ConversationHandlers(
            self.clinic_info, self.appointment_system,
            self.node_factory, self.conversation_state
        )
        logger.debug(f"   ✓ ConversationHandlers initialized")

        # Transport parameters
        self.transport_params = {
            "daily": lambda: DailyParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                vad_analyzer=SileroVADAnalyzer(),
            ),
            "webrtc": lambda: TransportParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                vad_analyzer=SileroVADAnalyzer(),
            ),
            "websocket": lambda: FastAPIWebsocketParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                vad_analyzer=SileroVADAnalyzer(),
            ),
        }

    async def run_bot(self, transport: BaseTransport, runner_args: RunnerArguments):
        """Run the dental clinic assistant bot."""
        # Initialize services

        sonioxParams = SonioxInputParams(language_hints=[Language.RO])

        stt = SonioxSTTService(api_key=os.getenv(
            "SONIOX_API_KEY"), params=sonioxParams)  # type: ignore
        tts = ElevenLabsTTSService(
            api_key=os.getenv("ELEVENLABS_API_KEY"),  # type: ignore
            voice_id=os.getenv("ELEVENLABS_VOICE_ID")  # type: ignore
        )
        llm = OpenAILLMService(api_key=os.getenv(
            "OPENAI_API_KEY"), model="gpt-4o")

        # Setup context and pipeline
        context = LLMContext()
        context_aggregator = LLMContextAggregatorPair(context)

        pipeline = Pipeline([
            transport.input(),
            stt,
            context_aggregator.user(),
            llm,
            tts,
            transport.output(),
            context_aggregator.assistant(),
        ])

        # Create observers
        metrics_observer = MetricsFileObserver("metrics.log")
        conversation_logger = ConversationLogger("conversations")

        # Audio recorder for debugging (controlled by env var)
        audio_recording_enabled = os.getenv("ENABLE_AUDIO_RECORDING", "false").lower() == "true"
        audio_recorder = AudioRecorder(
            recordings_dir="recordings",
            enabled=audio_recording_enabled
        )

        task = PipelineTask(
            pipeline,
            params=PipelineParams(
                allow_interruptions=True,
                enable_metrics=True,
                enable_usage_metrics=True
            ),
            observers=[metrics_observer, conversation_logger, audio_recorder]
        )

        # Initialize flow manager
        flow_manager = FlowManager(
            task=task,
            llm=llm,
            context_aggregator=context_aggregator,
            transport=transport,
        )

        @transport.event_handler("on_client_connected")
        async def on_client_connected(transport, client):
            logger.info("Client connected")
            # Get initial functions from conversation handlers
            initial_functions = [
                self.conversation_handlers.get_clinic_info,
                self.conversation_handlers.get_services_info,
                self.conversation_handlers.get_dentist_info,
                self.conversation_handlers.schedule_appointment,
                self.conversation_handlers.manage_existing_appointment
            ]
            await flow_manager.initialize(
                self.node_factory.create_initial_node(initial_functions)
            )

        @transport.event_handler("on_client_disconnected")
        async def on_client_disconnected(transport, client):
            logger.info("Client disconnected")
            await task.cancel()

        runner = PipelineRunner(handle_sigint=runner_args.handle_sigint)
        await runner.run(task)

    async def bot(self, runner_args: RunnerArguments):
        """Main bot entry point compatible with Pipecat Cloud."""
        transport = await create_transport(runner_args, self.transport_params)
        await self.run_bot(transport, runner_args)


# Create a global instance with environment-based configuration
def _create_dental_assistant():
    """Create dental assistant instance based on environment configuration."""
    appointment_type = os.getenv("APPOINTMENT_SYSTEM_TYPE", "mock")

    logger.info("=" * 60)
    logger.info("🦷 Initializing Dental Clinic Assistant")
    logger.info("=" * 60)
    logger.info(f"📋 Raw APPOINTMENT_SYSTEM_TYPE value: {repr(appointment_type)}")

    # Strip whitespace that might be in the env file
    appointment_type = appointment_type.strip() if appointment_type else "mock"
    logger.info(f"📋 Cleaned Appointment System Type: '{appointment_type}'")

    kwargs = {}

    if appointment_type == "google_calendar":
        service_account_file = os.getenv(
            "GOOGLE_SERVICE_ACCOUNT_FILE",
            "service-account-credentials.json"
        )

        # Get calendar configuration from environment or use default
        doctor_calendar = os.getenv(
            "GOOGLE_DOCTOR_CALENDAR_ID",
            "b521ff85c43bc6e250383db80a655b39091e4cb0df89b057912ee6665f95abac@group.calendar.google.com"
        )

        kwargs = {
            "service_account_file": service_account_file,
            "calendar_config": {
                "doctors": {
                    "Dr. Ana Popescu": doctor_calendar,
                }
            }
        }

        logger.info(f"📅 Google Calendar Configuration:")
        logger.info(f"   Service Account File: {service_account_file}")
        logger.info(f"   Doctor Calendar ID: {doctor_calendar}")
    else:
        logger.info(f"🔧 Using Mock Appointment System (in-memory)")

    try:
        assistant = DentalClinicAssistant(appointment_system_type=appointment_type, **kwargs)
        logger.success(f"✅ Dental Clinic Assistant initialized successfully")
        logger.info(f"   Appointment System: {appointment_type}")
        logger.info(f"   Clinic: {assistant.clinic_info.name}")
        logger.info("=" * 60)
        return assistant
    except Exception as e:
        logger.error(f"❌ Failed to initialize Dental Clinic Assistant: {e}")
        logger.error(f"   Falling back to mock appointment system")
        # Fallback to mock system
        return DentalClinicAssistant(appointment_system_type="mock")


_dental_assistant = _create_dental_assistant()

# Export the main bot function for compatibility


async def bot(runner_args: RunnerArguments):
    """Main bot entry point compatible with Pipecat Cloud."""
    await _dental_assistant.bot(runner_args)
