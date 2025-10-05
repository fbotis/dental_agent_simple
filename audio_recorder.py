"""Audio recording for debugging purposes using Pipecat's AudioBufferProcessor."""

import os
import wave
from datetime import datetime
from typing import Optional

from loguru import logger
from pipecat.processors.audio.audio_buffer_processor import AudioBufferProcessor


class AudioRecorder:
    """Audio recorder that uses Pipecat's AudioBufferProcessor for reliable recording.

    Records entire conversations (user + bot audio mixed) to WAV files for debugging.
    Based on: https://github.com/pipecat-ai/pipecat/blob/main/examples/foundational/34-audio-recording.py
    """

    def __init__(
        self,
        recordings_dir: str = "recordings",
        enabled: bool = True,
        sample_rate: int = 16000,
        num_channels: int = 1,
    ):
        """Initialize the audio recorder.

        Args:
            recordings_dir: Directory where audio files will be saved
            enabled: Whether recording is enabled (can be disabled via env var)
            sample_rate: Audio sample rate in Hz
            num_channels: Number of audio channels (1=mono, 2=stereo)
        """
        self._recordings_dir = recordings_dir
        self._enabled = enabled
        self._sample_rate = sample_rate
        self._num_channels = num_channels

        # Current recording session
        self._audio_buffer_processor: Optional[AudioBufferProcessor] = None

        # Ensure recordings directory exists
        if self._enabled:
            os.makedirs(recordings_dir, exist_ok=True)
            logger.info(f"🎙️  Audio recorder initialized, saving to: {recordings_dir}")
        else:
            logger.info(f"🎙️  Audio recorder disabled")

    def create_processor(self) -> Optional[AudioBufferProcessor]:
        """Create and return the AudioBufferProcessor to add to pipeline.

        Returns:
            AudioBufferProcessor instance if enabled, None otherwise
        """
        if not self._enabled:
            return None

        # Create the audio buffer processor
        # Note: buffer_size is NOT set, using defaults
        self._audio_buffer_processor = AudioBufferProcessor(
            sample_rate=self._sample_rate,
            num_channels=self._num_channels,
        )

        # Register event handler for merged audio (user + bot together)
        # Signature: (buffer, audio, sample_rate, num_channels)
        @self._audio_buffer_processor.event_handler("on_audio_data")
        async def on_audio_data(buffer, audio: bytes, sample_rate: int, num_channels: int):
            """Handle merged audio data from the buffer processor."""
            if len(audio) > 0:
                await self._save_audio_chunk(audio, sample_rate, num_channels)

        logger.info(f"🎙️  Created AudioBufferProcessor with event handler")
        return self._audio_buffer_processor

    async def _save_audio_chunk(self, audio: bytes, sample_rate: int, num_channels: int):
        """Save audio chunk to WAV file.

        Args:
            audio: Raw audio bytes
            sample_rate: Sample rate of the audio
            num_channels: Number of channels
        """
        try:
            # Create timestamped filename for this chunk
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = f"{self._recordings_dir}/recording_{timestamp}.wav"

            # Write WAV file
            with wave.open(filename, 'wb') as wf:
                wf.setsampwidth(2)  # 16-bit audio
                wf.setnchannels(num_channels)
                wf.setframerate(sample_rate)
                wf.writeframes(audio)

            file_size = os.path.getsize(filename)
            duration_sec = len(audio) / (sample_rate * num_channels * 2)  # 2 bytes per sample

            logger.info(
                f"🎙️  Saved audio chunk: {os.path.basename(filename)} "
                f"({file_size / 1024:.1f} KB, {duration_sec:.1f}s)"
            )

        except Exception as e:
            logger.error(f"🎙️  Error saving audio chunk: {e}", exc_info=True)

    def is_enabled(self) -> bool:
        """Check if recording is enabled.

        Returns:
            True if recording is enabled
        """
        return self._enabled
