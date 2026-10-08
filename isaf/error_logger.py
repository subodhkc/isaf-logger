"""
ISAF Error Logger - Compliance-Grade Error Tracking

Provides error logging with alerting for ISAF Logger failures.
Critical for EU AI Act Article 12 compliance (record-keeping requirement).
"""

import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
from collections import deque


class ISAFErrorLogger:
    """
    Error logger for ISAF with alerting capabilities.
    
    Tracks errors and alerts when failure threshold is exceeded.
    """
    
    def __init__(self, log_file: str = 'isaf_errors.log', alert_threshold: int = 3):
        """
        Initialize error logger.
        
        Args:
            log_file: Path to error log file
            alert_threshold: Number of errors in 5 minutes before alerting
        """
        self.log_file = Path(log_file)
        self.alert_threshold = alert_threshold
        self.recent_errors = deque(maxlen=100)  # Keep last 100 errors in memory
        
        # Set up file logger
        self.logger = logging.getLogger('isaf.errors')
        self.logger.setLevel(logging.ERROR)
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # File handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.ERROR)
        
        # Formatter with detailed context
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        
        # Console handler for critical errors
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.CRITICAL)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def log_error(
        self, 
        context: str, 
        error: Exception,
        additional_info: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log an error with context.
        
        Args:
            context: Where the error occurred (e.g., 'log_objective', 'backend_storage')
            error: The exception that occurred
            additional_info: Additional context information
        """
        error_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'context': context,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'additional_info': additional_info or {}
        }
        
        # Add to recent errors
        self.recent_errors.append(error_entry)
        
        # Log to file
        log_message = f"[{context}] {type(error).__name__}: {str(error)}"
        if additional_info:
            log_message += f" | Additional info: {json.dumps(additional_info)}"
        
        self.logger.error(log_message, exc_info=True)
        
        # Check if we should alert
        if self._should_alert():
            self._trigger_alert()
    
    def _should_alert(self) -> bool:
        """
        Check if error threshold exceeded in last 5 minutes.
        
        Returns:
            True if should alert, False otherwise
        """
        if len(self.recent_errors) < self.alert_threshold:
            return False
        
        # Check errors in last 5 minutes
        five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
        recent_count = sum(
            1 for error in self.recent_errors
            if datetime.fromisoformat(error['timestamp']) > five_minutes_ago
        )
        
        return recent_count >= self.alert_threshold
    
    def _trigger_alert(self) -> None:
        """
        Trigger alert for repeated failures.
        
        Prints warning to console. In production, this would integrate
        with PagerDuty, Slack, or other alerting systems.
        """
        alert_message = (
            f"\n{'='*80}\n"
            f"⚠️  ISAF LOGGER ALERT: {self.alert_threshold}+ errors in last 5 minutes\n"
            f"{'='*80}\n"
            f"Check error log: {self.log_file.absolute()}\n"
            f"Recent errors:\n"
        )
        
        # Show last 5 errors
        for error in list(self.recent_errors)[-5:]:
            alert_message += (
                f"  - [{error['timestamp']}] {error['context']}: "
                f"{error['error_type']} - {error['error_message']}\n"
            )
        
        alert_message += f"{'='*80}\n"
        
        # Log as CRITICAL so it goes to console
        self.logger.critical(alert_message)
    
    def get_error_count(self, minutes: int = 5) -> int:
        """
        Get count of errors in last N minutes.
        
        Args:
            minutes: Time window in minutes
            
        Returns:
            Number of errors in time window
        """
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        return sum(
            1 for error in self.recent_errors
            if datetime.fromisoformat(error['timestamp']) > cutoff
        )
    
    def get_recent_errors(self, limit: int = 10) -> list:
        """
        Get recent errors.
        
        Args:
            limit: Maximum number of errors to return
            
        Returns:
            List of recent error entries
        """
        return list(self.recent_errors)[-limit:]
    
    def clear_errors(self) -> None:
        """Clear error history (for testing)."""
        self.recent_errors.clear()


# Global error logger instance
_global_error_logger: Optional[ISAFErrorLogger] = None


def get_error_logger() -> ISAFErrorLogger:
    """
    Get or create global error logger instance.
    
    Returns:
        Global ISAFErrorLogger instance
    """
    global _global_error_logger
    if _global_error_logger is None:
        _global_error_logger = ISAFErrorLogger()
    return _global_error_logger
