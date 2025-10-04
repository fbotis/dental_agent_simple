"""Audio recording for debugging purposes - simple direct-to-file approach."""

import os
import wave
from datetime import datetime
from typing import Optional

from loguru import logger
from pipecat.frames.frames import (
    AudioRawFrame,
    EndFrame,
    StartFrame,
)
from pipecat.observers.base_observer import BaseObserver, FramePushed


class AudioRecorder(BaseObserver):
    """Observer that records all audio frames to a single WAV file for debugging.

    Records everything (user + bot audio) mixed together in chronological order.
    Uses direct file writing for simplicity and reliability.
    """

    def __init__(
        self,
        recordings_dir: str = "recordings",
        enabled: bool = True,
        sample_rate: int = 16000,
        channels: int = 1,
        sample_width: int = 2  # 16-bit audio
    ):
        """Initialize the audio recorder.

        Args:
            recordings_dir: Directory where audio files will be saved
            enabled: Whether recording is enabled (can be disabled via env var)
            sample_rate: Audio sample rate in Hz
            channels: Number of audio channels (1=mono, 2=stereo)
            sample_width: Sample width in bytes (2 for 16-bit audio)
        """
        super().__init__()
        self._recordings_dir = recordings_dir
        self._enabled = enabled
        self._sample_rate = sample_rate
        self._channels = channels
        self._sample_width = sample_width

        # Current recording session
        self._session_id: Optional[str] = None
        self._wav_file: Optional[wave.Wave_write] = None
        self._filepath: Optional[str] = None
        self._frame_count = 0

        # Ensure recordings directory exists
        if self._enabled:
            os.makedirs(recordings_dir, exist_ok=True)
            logger.info(f"🎙️  Audio recorder initialized, saving to: {recordings_dir}")
        else:
            logger.info(f"🎙️  Audio recorder disabled")

    async def on_push_frame(self, data: FramePushed):
        """Process frames and record audio data.

        Args:
            data: Frame push event containing the frame and direction information
        """
        if not self._enabled:
            return

        try:
            # Handle conversation start
            if isinstance(data.frame, StartFrame):
                self._start_recording()

            # Handle conversation end
            elif isinstance(data.frame, EndFrame):
                self._end_recording()

            # Handle audio frames - record ALL audio regardless of direction
            elif isinstance(data.frame, AudioRawFrame):
                self._record_audio_frame(data.frame)

        except Exception as e:
            logger.error(f"🎙️  Error in audio recorder: {e}")

    def _start_recording(self):
        """Start a new recording session."""
        try:
            # Close any existing file
            if self._wav_file:
                self._wav_file.close()
                self._wav_file = None

            # Create new session
            timestamp = datetime.now()
            self._session_id = timestamp.strftime("%Y%m%d_%H%M%S_%f")[:-3]
            self._filepath = os.path.join(
                self._recordings_dir,
                f"{self._session_id}.wav"
            )
            self._frame_count = 0

            # Open WAV file for writing
            self._wav_file = wave.open(self._filepath, 'wb')
            self._wav_file.setnchannels(self._channels)
            self._wav_file.setsampwidth(self._sample_width)
            self._wav_file.setframerate(self._sample_rate)

            logger.info(f"🎙️  Started recording: {self._filepath}")

        except Exception as e:
            logger.error(f"🎙️  Error starting recording: {e}")
            self._wav_file = None

    def _record_audio_frame(self, frame: AudioRawFrame):
        """Record an audio frame to the WAV file.

        Args:
            frame: Audio frame to record
        """
        if not self._wav_file or not self._session_id:
            return

        try:
            # Write audio data directly to file
            self._wav_file.writeframes(frame.audio)
            self._frame_count += 1

            # Log every 100 frames to track progress without spamming
            if self._frame_count % 100 == 0:
                logger.debug(f"🎙️  Recorded {self._frame_count} frames")

        except Exception as e:
            logger.error(f"🎙️  Error recording audio frame: {e}")

    def _end_recording(self):
        """End the current recording session."""
        if not self._wav_file or not self._session_id:
            return

        try:
            # Close the WAV file
            self._wav_file.close()
            self._wav_file = None

            # Get file size for logging
            if self._filepath and os.path.exists(self._filepath):
                file_size = os.path.getsize(self._filepath)
                file_size_mb = file_size / (1024 * 1024)
                duration_sec = self._frame_count * (1 / self._sample_rate) if self._frame_count > 0 else 0

                logger.info(
                    f"✅ Saved recording: {os.path.basename(self._filepath)} "
                    f"({file_size_mb:.2f} MB, {duration_sec:.1f}s, {self._frame_count} frames)"
                )
            else:
                logger.info(f"✅ Ended recording: {self._session_id}")

        except Exception as e:
            logger.error(f"🎙️  Error ending recording: {e}")
        finally:
            # Reset session
            self._session_id = None
            self._filepath = None
            self._frame_count = 0

    def get_recordings_dir(self) -> str:
        """Get the recordings directory path.

        Returns:
            Path to the recordings directory
        """
        return self._recordings_dir

    def is_enabled(self) -> bool:
        """Check if recording is enabled.

        Returns:
            True if recording is enabled
        """
        return self._enabled

    def __del__(self):
        """Cleanup on deletion."""
        if self._wav_file:
            try:
                self._wav_file.close()
            except:
                pass
