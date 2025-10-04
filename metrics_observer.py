"""Custom metrics observer that logs metrics to a file."""

import json
from datetime import datetime

from loguru import logger
from pipecat.frames.frames import MetricsFrame
from pipecat.observers.base_observer import BaseObserver, FramePushed
from pipecat.processors.frame_processor import FrameDirection
from pipecat.metrics.metrics import (
    LLMUsageMetricsData,
    ProcessingMetricsData,
    TTFBMetricsData,
    TTSUsageMetricsData,
)


class MetricsFileObserver(BaseObserver):
    """Observer that logs metrics to a file instead of console."""

    def __init__(self, log_file_path: str = "metrics.log"):
        """Initialize the metrics file observer.

        Args:
            log_file_path: Path to the file where metrics will be logged.
        """
        super().__init__()
        self._log_file_path = log_file_path
        self._processed_frames = set()
        logger.info(f"📊 Metrics file observer initialized, logging to: {log_file_path}")

    async def on_push_frame(self, data: FramePushed):
        """Process MetricsFrame and log to file.

        Args:
            data: Frame push event containing the frame and direction information.
        """
        # Only process downstream MetricsFrames
        if data.direction != FrameDirection.DOWNSTREAM:
            return

        if not isinstance(data.frame, MetricsFrame):
            return

        # Skip already processed frames
        if data.frame.id in self._processed_frames:
            return

        self._processed_frames.add(data.frame.id)

        # Log metrics to file
        await self._log_metrics_to_file(data.frame)

    async def _log_metrics_to_file(self, frame: MetricsFrame):
        """Log metrics data to the specified file.

        Args:
            frame: MetricsFrame containing the metrics data to log.
        """
        timestamp = datetime.now().isoformat()

        for metric_data in frame.data:
            log_entry = {
                "timestamp": timestamp,
                "frame_id": frame.id,
                "metric_type": type(metric_data).__name__,
                "processor": getattr(metric_data, 'processor', 'unknown'),
                "model": getattr(metric_data, 'model', None),
            }

            if isinstance(metric_data, TTFBMetricsData):
                log_entry.update({
                    "ttfb_seconds": metric_data.value,
                    "metric_category": "timing"
                })
            elif isinstance(metric_data, ProcessingMetricsData):
                log_entry.update({
                    "processing_seconds": metric_data.value,
                    "metric_category": "timing"
                })
            elif isinstance(metric_data, LLMUsageMetricsData):
                log_entry.update({
                    "prompt_tokens": metric_data.value.prompt_tokens,
                    "completion_tokens": metric_data.value.completion_tokens,
                    "cache_read_input_tokens": getattr(metric_data.value, 'cache_read_input_tokens', None),
                    "reasoning_tokens": getattr(metric_data.value, 'reasoning_tokens', None),
                    "metric_category": "usage"
                })
            elif isinstance(metric_data, TTSUsageMetricsData):
                log_entry.update({
                    "characters": metric_data.value,
                    "metric_category": "usage"
                })
            else:
                log_entry.update({
                    "value": str(metric_data.value) if hasattr(metric_data, 'value') else None,
                    "metric_category": "other"
                })

            # Write to file (append mode)
            try:
                with open(self._log_file_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(log_entry) + '\n')
            except Exception as e:
                logger.error(f"Failed to write metrics to file {self._log_file_path}: {e}")
