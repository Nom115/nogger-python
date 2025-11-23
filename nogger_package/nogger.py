"""
Nogger - A Better Logger
A robust, async-friendly logging library with extensive customisation options.
"""

import asyncio
import datetime
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, TextIO, TYPE_CHECKING
from enum import Enum
from dataclasses import dataclass, asdict

if TYPE_CHECKING:
    from ._gdpr import GDPRPolicy

from ._colours import ColourManager, ColourScheme, ColourCodes
from ._export import (
    export_logs_json as _export_logs_json,
    export_logs_csv as _export_logs_csv,
    export_logs_txt as _export_logs_txt,
    export_logs as _export_logs
)
from ._config import LoggerConfiguration, LogLevel, LoggingMode, OutputBehaviour


@dataclass
class LogEntry:
    """Represents a single log entry with all metadata"""
    timestamp: datetime.datetime
    level: LogLevel
    core: str
    message: str
    extra_data: Dict[str, Any]
    thread_id: Optional[int] = None
    task_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialisation"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['level'] = self.level.value
        return data


class Nogger:
    """
    A comprehensive, async-friendly logging system with extensive customisation options.
    
    Supports multiple output modes, batching, streaming, and rich formatting with colours.
    Thread-safe and designed for high-performance applications.
    """
    
    def __init__(self, **kwargs):
        """
        Initialise Nogger with comprehensive configuration options.
        
        Args:
            core: Logger name/identifier (default: 'nogger')
            colours: Enable colour output (default: True)
            colour_scheme: ColourScheme enum value (default: ColourScheme.DEFAULT)
            logging_mode: LoggingMode enum value (default: LoggingMode.CONSOLE)
            output_behaviour: OutputBehaviour enum value (default: OutputBehaviour.STREAMED)
            **kwargs: Additional configuration options (see LoggerConfiguration)
        """
        # Core configuration
        self._config = LoggerConfiguration(**kwargs)
        
        # Colour management
        self._colour_manager = ColourManager(
            colours_enabled=self._config.colours_enabled,
            scheme=self._config.colour_scheme
        )
        
        # Log storage (thread-safe)
        self._logs: List[LogEntry] = []
        self._logs_lock = threading.RLock()
        
        # Async support
        self._async_queue: Optional[asyncio.Queue] = None
        self._async_worker_task: Optional[asyncio.Task] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        
        # Batching support
        self._batch_buffer: List[LogEntry] = []
        self._batch_lock = threading.Lock()
        self._batch_timer: Optional[threading.Timer] = None
        
        # File handling
        self._output_file: Optional[TextIO] = None
        self._initialise_output_file()
        
        # Performance tracking
        self._level_priorities = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.WARNING: 2,
            LogLevel.ERROR: 3,
            LogLevel.CRITICAL: 4
        }
        
        # GDPR compliance
        self._gdpr_enabled = self._config.gdpr_policy is not None and self._config.gdpr_policy.enabled
    
    def _initialise_output_file(self) -> None:
        """Initialise output file if needed for file-based logging modes"""
        if self._config.logging_mode in [LoggingMode.FILE_JSON, LoggingMode.FILE_CSV, LoggingMode.FILE_TXT]:
            if not self._config.output_file_path:
                # Auto-generate filename based on mode
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                extension = {
                    LoggingMode.FILE_JSON: 'json',
                    LoggingMode.FILE_CSV: 'csv', 
                    LoggingMode.FILE_TXT: 'txt'
                }[self._config.logging_mode]
                self._config.output_file_path = Path(f"nogger_log_{timestamp}.{extension}")
            
            # Ensure directory exists
            self._config.output_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # ============================================================================
    # MAIN LOGGING METHODS
    # ============================================================================
    
    def add(self, message: str, level: Union[LogLevel, str] = LogLevel.INFO, **kwargs) -> None:
        """
        Add a log entry with comprehensive options and async support.
        
        Args:
            message: The log message to record
            level: Log level (LogLevel enum or string like 'INFO', 'ERROR', etc.)
            **kwargs: Advanced options for this specific log entry:
                - extra_data: Dict of additional contextual data
                - colours: Override global colour setting for this message
                - timestamp: Override timestamp inclusion for this message  
                - format: Custom format string for this message
                - output_stream: Custom output stream for this message
                - force_sync: Force synchronous processing even in async mode
        """
        # Normalise and validate log level
        if isinstance(level, str):
            try:
                level = LogLevel(level.upper())
            except ValueError:
                level = LogLevel.INFO
        
        # Check if this log level meets minimum threshold
        if not self._should_log_level(level):
            return
        
        # Create comprehensive log entry
        log_entry = self._create_log_entry(message, level, kwargs.get('extra_data', {}))
        
        # Apply GDPR sanitization if enabled
        if self._gdpr_enabled and self._config.gdpr_policy:
            from ._gdpr import sanitize_log_entry
            log_entry = sanitize_log_entry(log_entry, self._config.gdpr_policy)
        
        # Store in memory (thread-safe)
        self._store_log_entry(log_entry)
        
        # Handle output based on configuration
        if self._config.output_behaviour == OutputBehaviour.STREAMED:
            self._process_log_immediately(log_entry, **kwargs)
        elif self._config.output_behaviour == OutputBehaviour.BATCHED:
            self._add_to_batch(log_entry, **kwargs)
        elif self._config.output_behaviour == OutputBehaviour.ASYNC_STREAMED:
            self._schedule_async_processing(log_entry, **kwargs)
        elif self._config.output_behaviour == OutputBehaviour.ASYNC_BATCHED:
            self._add_to_batch(log_entry, **kwargs)
    
    def _should_log_level(self, level: LogLevel) -> bool:
        """Check if the log level meets the minimum threshold"""
        return self._level_priorities[level] >= self._level_priorities[self._config.minimum_level]
    
    def _create_log_entry(self, message: str, level: LogLevel, extra_data: Dict[str, Any]) -> LogEntry:
        """Create a comprehensive log entry with all metadata"""
        return LogEntry(
            timestamp=datetime.datetime.now(),
            level=level,
            core=self._config.core_name,
            message=message,
            extra_data=extra_data or {},
            thread_id=threading.get_ident() if self._config.include_thread_info else None,
            task_id=self._get_current_task_id() if self._config.include_task_info else None
        )
    
    def _get_current_task_id(self) -> Optional[str]:
        """Get current asyncio task ID if available"""
        try:
            task = asyncio.current_task()
            return f"task-{id(task)}" if task else None
        except RuntimeError:
            return None
    
    def _store_log_entry(self, log_entry: LogEntry) -> None:
        """Thread-safe storage of log entry with optional size limiting"""
        with self._logs_lock:
            self._logs.append(log_entry)
            
            # Enforce maximum stored logs limit
            if (self._config.max_stored_logs and 
                len(self._logs) > self._config.max_stored_logs):
                # Remove oldest logs
                excess = len(self._logs) - self._config.max_stored_logs
                self._logs = self._logs[excess:]
    
    # ============================================================================
    # LOG PROCESSING METHODS
    # ============================================================================
    
    def _process_log_immediately(self, log_entry: LogEntry, **kwargs) -> None:
        """Process a log entry immediately (streamed mode)"""
        formatted_message = self._format_log_entry(log_entry, **kwargs)
        self._output_formatted_message(formatted_message, **kwargs)
    
    def _add_to_batch(self, log_entry: LogEntry, **kwargs) -> None:
        """Add log entry to batch buffer for later processing"""
        should_process_immediately = False
        
        with self._batch_lock:
            self._batch_buffer.append((log_entry, kwargs))
            
            # Check if batch is full
            if len(self._batch_buffer) >= self._config.batch_size:
                should_process_immediately = True
            else:
                # Reset/start batch timer (outside of lock to avoid deadlock)
                if self._batch_timer:
                    self._batch_timer.cancel()
                    self._batch_timer = None
        
        # Process immediately if batch is full (outside of lock)
        if should_process_immediately:
            self._process_batch()
        else:
            # Start new timer outside of lock
            self._batch_timer = threading.Timer(
                self._config.batch_timeout_seconds, 
                self._process_batch
            )
            self._batch_timer.start()
    
    def _process_batch(self) -> None:
        """Process all entries in the current batch"""
        batch_to_process = []
        
        with self._batch_lock:
            if not self._batch_buffer:
                return
            
            batch_to_process = self._batch_buffer.copy()
            self._batch_buffer.clear()
            
            if self._batch_timer:
                try:
                    self._batch_timer.cancel()
                except:
                    pass  # Timer might already be cancelled
                self._batch_timer = None
        
        # Process batch entries outside of lock to avoid deadlock
        try:
            for log_entry, kwargs in batch_to_process:
                formatted_message = self._format_log_entry(log_entry, **kwargs)
                self._output_formatted_message(formatted_message, **kwargs)
        except Exception as e:
            # Don't let batch processing errors crash the system
            print(f"Error processing batch: {e}", file=None)
    
    def _schedule_async_processing(self, log_entry: LogEntry, **kwargs) -> None:
        """Schedule log entry for async processing"""
        if self._async_queue is None:
            self._initialise_async_processing()
        
        try:
            self._async_queue.put_nowait((log_entry, kwargs))
        except asyncio.QueueFull:
            # Fallback to immediate processing if queue is full
            self._process_log_immediately(log_entry, **kwargs)
    
    def _add_to_async_batch(self, log_entry: LogEntry, **kwargs) -> None:
        """Add log entry to async batch processing"""
        # For now, use sync batching - can be enhanced with async batch processing
        self._add_to_batch(log_entry, **kwargs)
    
    async def _ensure_async_worker_running(self) -> None:
        """Ensure the async worker task is running"""
        if self._async_worker_task is None or self._async_worker_task.done():
            self._loop = asyncio.get_event_loop()
            if self._async_queue is None:
                self._initialise_async_processing()
            self._async_worker_task = asyncio.create_task(self._async_worker())
    
    def _initialise_async_processing(self) -> None:
        """Initialise async processing components"""
        self._async_queue = asyncio.Queue(maxsize=self._config.async_queue_size)
    
    async def _async_worker(self) -> None:
        """Async worker that processes log entries from the queue"""
        while True:
            try:
                log_entry, kwargs = await self._async_queue.get()
                formatted_message = self._format_log_entry(log_entry, **kwargs)
                self._output_formatted_message(formatted_message, **kwargs)
                self._async_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log processing shouldn't crash the worker
                print(f"Error in async log worker: {e}", file=self._config.custom_output_stream or None)
    
    # ============================================================================
    # FORMATTING AND OUTPUT METHODS
    # ============================================================================
    
    def _format_log_entry(self, log_entry: LogEntry, **kwargs) -> str:
        """Format a log entry according to configuration and options"""
        # Override settings from kwargs
        use_timestamp = kwargs.get('timestamp', self._config.include_timestamp)
        use_colours = kwargs.get('colours', self._config.colours_enabled)
        custom_format = kwargs.get('format', self._config.message_format)
        
        # Build format data dictionary
        format_data = {
            'timestamp': self._format_timestamp(log_entry.timestamp) if use_timestamp else '',
            'level': log_entry.level.value,
            'core': log_entry.core,
            'message': log_entry.message,
        }
        
        # Add extra data formatting
        if log_entry.extra_data:
            extra_items = [f"{k}: {v}" for k, v in log_entry.extra_data.items()]
            format_data['extra'] = f" ({' | '.join(extra_items)})"
        else:
            format_data['extra'] = ""
        
        # Add thread/task info if enabled
        if self._config.include_thread_info and log_entry.thread_id:
            format_data['thread'] = f" [thread:{log_entry.thread_id}]"
        else:
            format_data['thread'] = ""
            
        if self._config.include_task_info and log_entry.task_id:
            format_data['task'] = f" [task:{log_entry.task_id}]"
        else:
            format_data['task'] = ""
        
        # Apply colours if enabled
        if use_colours and self._colour_manager.colours_enabled:
            level_colour = self._colour_manager.get_colour_for_level(log_entry.level.value)
            core_colour = self._colour_manager.get_colour_for_element('core')
            timestamp_colour = self._colour_manager.get_colour_for_element('timestamp')
            
            format_data['level'] = self._colour_manager.apply_colour(format_data['level'], level_colour)
            format_data['core'] = self._colour_manager.apply_colour(format_data['core'], core_colour)
            if format_data['timestamp']:
                format_data['timestamp'] = self._colour_manager.apply_colour(format_data['timestamp'], timestamp_colour)
        
        # Format the complete message
        try:
            return custom_format.format(**format_data)
        except KeyError:
            # Fallback to basic format if custom format has issues
            return f"{format_data['timestamp']} [{format_data['level']}] {format_data['core']}: {format_data['message']}{format_data['extra']}"
    
    def _format_timestamp(self, timestamp: datetime.datetime) -> str:
        """Format timestamp according to configuration"""
        return timestamp.strftime(self._config.timestamp_format)
    
    def _output_formatted_message(self, formatted_message: str, **kwargs) -> None:
        """Output formatted message according to logging mode"""
        custom_output = kwargs.get('output_stream')
        
        if custom_output:
            print(formatted_message, file=custom_output)
            return
        
        if self._config.logging_mode == LoggingMode.CONSOLE:
            print(formatted_message, file=self._config.custom_output_stream or None)
        
        elif self._config.logging_mode == LoggingMode.MEMORY_ONLY:
            pass  # Already stored in memory, nothing to output
        
        elif self._config.logging_mode in [LoggingMode.FILE_JSON, LoggingMode.FILE_CSV, LoggingMode.FILE_TXT]:
            # File output is handled by export methods
            pass
        
        elif self._config.logging_mode == LoggingMode.CUSTOM:
            # Custom handling would be implemented here
            pass
    
    # ============================================================================
    # CONVENIENCE METHODS
    # ============================================================================
    
    def _is_async_mode(self) -> bool:
        """Check if async output behaviour is configured"""
        return self._config.output_behaviour in [
            OutputBehaviour.ASYNC_STREAMED, 
            OutputBehaviour.ASYNC_BATCHED
        ]
    
    def _in_async_context(self) -> bool:
        """Check if currently running in an async event loop"""
        try:
            asyncio.current_task()
            return True
        except RuntimeError:
            return False
    
    def debug(self, message: str, **kwargs):
        """
        Log a debug message with DEBUG level.
        
        Works seamlessly in both sync and async contexts. The log is always
        processed immediately; awaiting is optional and only ensures the async
        worker is running when in async output mode.
        
        Usage:
            # Synchronous
            logger.debug("Debug message")
            
            # Asynchronous - await is optional
            await logger.debug("Debug message")  # Ensures worker running
            logger.debug("Also works")           # Fire-and-forget
        """
        return self._log(message, LogLevel.DEBUG, **kwargs)
    
    def info(self, message: str, **kwargs):
        """
        Log an informational message with INFO level.
        
        Works in both sync and async contexts.
        """
        return self._log(message, LogLevel.INFO, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """
        Log a warning message with WARNING level.
        
        Works in both sync and async contexts.
        """
        return self._log(message, LogLevel.WARNING, **kwargs)
    
    def error(self, message: str, **kwargs):
        """
        Log an error message with ERROR level.
        
        Works in both sync and async contexts.
        """
        return self._log(message, LogLevel.ERROR, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """
        Log a critical message with CRITICAL level.
        
        Works in both sync and async contexts.
        """
        return self._log(message, LogLevel.CRITICAL, **kwargs)
    
    def _log(self, message: str, level: LogLevel, **kwargs):
        """
        Unified logging method that adapts to context and configuration.
        
        Always executes synchronously. In async mode, schedules async worker
        but doesn't force the caller to await.
        """
        # Always execute synchronously - this is key for flexibility
        self.add(message, level, **kwargs)
        
        # If we're in async mode AND async context, return awaitable for worker management
        # But the log is already queued, so awaiting is optional
        if self._is_async_mode() and self._in_async_context():
            return self._ensure_async_worker_running()
        
        return None
    
    async def _log_async(self, message: str, level: LogLevel, **kwargs):
        """
        Internal async logging wrapper.
        
        Ensures proper async processing and worker management.
        """
        self.add(message, level, **kwargs)
        await self._ensure_async_worker_running()
    
    # ============================================================================
    # CONFIGURATION AND MANAGEMENT METHODS
    # ============================================================================
    
    def set_logging_mode(self, mode: LoggingMode, **kwargs) -> None:
        """
        Change the logging mode with optional additional configuration.
        
        Args:
            mode: New LoggingMode to use
            **kwargs: Additional configuration for the new mode
                - output_file_path: Path for file-based modes
                - batch_size: Size for batched modes
                - etc.
        """
        self._config.logging_mode = mode
        
        # Update configuration from kwargs
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
        
        # Reinitialise output file if needed
        if mode in [LoggingMode.FILE_JSON, LoggingMode.FILE_CSV, LoggingMode.FILE_TXT]:
            self._initialise_output_file()
    
    def set_output_behaviour(self, behaviour: OutputBehaviour) -> None:
        """Change the output behaviour (streaming vs batching)"""
        self._config.output_behaviour = behaviour
    
    def set_minimum_level(self, level: Union[LogLevel, str]) -> None:
        """Set the minimum log level to process"""
        if isinstance(level, str):
            level = LogLevel(level.upper())
        self._config.minimum_level = level
    
    def set_colour_scheme(self, scheme: ColourScheme) -> None:
        """Change the colour scheme"""
        self._colour_manager.set_scheme(scheme)
    
    def enable_colours(self) -> None:
        """Enable coloured output"""
        self._config.colours_enabled = True
        self._colour_manager.enable_colours()
    
    def disable_colours(self) -> None:
        """Disable coloured output"""
        self._config.colours_enabled = False
        self._colour_manager.disable_colours()
    
    def toggle_colours(self) -> bool:
        """Toggle coloured output and return new state"""
        self._config.colours_enabled = not self._config.colours_enabled
        return self._colour_manager.toggle_colours()
    
    def set_core_name(self, name: str) -> None:
        """Change the core logger name"""
        self._config.core_name = name
    
    def set_format(self, format_string: str) -> None:
        """Change the message format template"""
        self._config.message_format = format_string
    
    def set_timestamp_format(self, format_string: str) -> None:
        """Change the timestamp format"""
        self._config.timestamp_format = format_string
    
    def enable_timestamp(self) -> None:
        """Enable timestamp in log messages"""
        self._config.include_timestamp = True
    
    def disable_timestamp(self) -> None:
        """Disable timestamp in log messages"""
        self._config.include_timestamp = False
    
    def set_batch_size(self, size: int) -> None:
        """Set the batch size for batched output modes"""
        self._config.batch_size = size
    
    def set_batch_timeout(self, timeout_seconds: float) -> None:
        """Set the batch timeout for batched output modes"""
        self._config.batch_timeout_seconds = timeout_seconds
    
    # ============================================================================
    # LOG RETRIEVAL AND EXPORT METHODS
    # ============================================================================
    
    def get_logs(self, 
                 level: Optional[Union[LogLevel, str]] = None,
                 limit: Optional[int] = None,
                 since: Optional[datetime.datetime] = None,
                 until: Optional[datetime.datetime] = None) -> List[LogEntry]:
        """
        Retrieve stored log entries with comprehensive filtering options.
        
        Args:
            level: Filter by specific log level
            limit: Maximum number of logs to return (most recent first)
            since: Only return logs after this timestamp
            until: Only return logs before this timestamp
        
        Returns:
            List of LogEntry objects matching the criteria
        """
        with self._logs_lock:
            logs = self._logs.copy()
        
        # Apply level filter
        if level:
            if isinstance(level, str):
                level = LogLevel(level.upper())
            logs = [log for log in logs if log.level == level]
        
        # Apply time filters
        if since:
            logs = [log for log in logs if log.timestamp >= since]
        if until:
            logs = [log for log in logs if log.timestamp <= until]
        
        # Apply limit (most recent first)
        if limit:
            logs = logs[-limit:]
        
        return logs
    
    def get_logs_by_core(self, core_name: str, **kwargs) -> List[LogEntry]:
        """Get logs filtered by core name"""
        with self._logs_lock:
            logs = [log for log in self._logs if log.core == core_name]
        
        return self._apply_log_filters(logs, **kwargs)
    
    def _apply_log_filters(self, logs: List[LogEntry], **kwargs) -> List[LogEntry]:
        """Apply common filtering logic to a list of logs"""
        # This method can be extended with additional filtering logic
        if kwargs.get('limit'):
            logs = logs[-kwargs['limit']:]
        return logs
    
    def clear_logs(self) -> int:
        """
        Clear all stored log entries.
        
        Returns:
            Number of logs that were cleared
        """
        with self._logs_lock:
            count = len(self._logs)
            self._logs.clear()
            return count
    
    def export_logs_json(self, filename: Union[str, Path]) -> None:
        """Export logs to JSON format"""
        with self._logs_lock:
            logs = self._logs.copy()
        
        _export_logs_json(logs, filename)
    
    def export_logs_csv(self, filename: Union[str, Path]) -> None:
        """Export logs to CSV format"""
        with self._logs_lock:
            logs = self._logs.copy()
        
        _export_logs_csv(logs, filename)
    
    def export_logs_txt(self, filename: Union[str, Path]) -> None:
        """Export logs to plain text format"""
        with self._logs_lock:
            logs = self._logs.copy()
        
        _export_logs_txt(logs, filename, self._format_log_entry)
    
    def export_logs(self, filename: Union[str, Path], format_type: str = 'json') -> None:
        """
        Export logs to file in specified format.
        
        Args:
            filename: Output filename
            format_type: 'json', 'csv', or 'txt'
        """
        with self._logs_lock:
            logs = self._logs.copy()
        
        _export_logs(logs, filename, format_type, self._format_log_entry)
    
    # ============================================================================
    # LIFECYCLE AND CLEANUP METHODS
    # ============================================================================
    
    def flush_batches(self) -> None:
        """Force processing of any pending batched logs"""
        if self._config.output_behaviour in [OutputBehaviour.BATCHED, OutputBehaviour.ASYNC_BATCHED]:
            self._process_batch()
    
    async def shutdown_async(self) -> None:
        """Gracefully shutdown async processing"""
        # Process any remaining items in async queue
        if self._async_queue:
            await self._async_queue.join()
        
        # Cancel async worker
        if self._async_worker_task:
            self._async_worker_task.cancel()
            try:
                await self._async_worker_task
            except asyncio.CancelledError:
                pass
    
    def shutdown(self) -> None:
        """Gracefully shutdown the logger"""
        # Flush any pending batches
        self.flush_batches()
        
        # Cancel any batch timers
        if self._batch_timer:
            self._batch_timer.cancel()
        
        # Close output file if opened
        if self._output_file:
            self._output_file.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup"""
        self.shutdown()
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with cleanup"""
        await self.shutdown_async()
    
    # ============================================================================
    # INFORMATION AND STATISTICS METHODS
    # ============================================================================
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the logger"""
        with self._logs_lock:
            total_logs = len(self._logs)
            level_counts = {}
            
            for level in LogLevel:
                level_counts[level.value] = sum(1 for log in self._logs if log.level == level)
        
        return {
            'total_logs': total_logs,
            'level_counts': level_counts,
            'core_name': self._config.core_name,
            'logging_mode': self._config.logging_mode.value,
            'output_behaviour': self._config.output_behaviour.value,
            'colours_enabled': self._config.colours_enabled,
            'minimum_level': self._config.minimum_level.value,
            'batch_size': self._config.batch_size,
            'max_stored_logs': self._config.max_stored_logs,
            'gdpr_enabled': self._gdpr_enabled,
        }
    
    # ============================================================================
    # GDPR METHODS
    # ============================================================================
    
    def enable_gdpr(self, policy: Optional['GDPRPolicy'] = None) -> None:
        """
        Enable GDPR compliance with optional custom policy.
        
        Args:
            policy: Optional GDPRPolicy instance (uses default if not provided)
        """
        if policy is None:
            from ._gdpr import create_default_gdpr_policy
            policy = create_default_gdpr_policy()
            policy.enabled = True
        
        self._config.gdpr_policy = policy
        self._gdpr_enabled = True
    
    def disable_gdpr(self) -> None:
        """Disable GDPR compliance"""
        self._gdpr_enabled = False
        if self._config.gdpr_policy:
            self._config.gdpr_policy.enabled = False
    
    def set_gdpr_policy(self, policy: 'GDPRPolicy') -> None:
        """
        Set a custom GDPR policy.
        
        Args:
            policy: GDPRPolicy instance to use
        """
        self._config.gdpr_policy = policy
        self._gdpr_enabled = policy.enabled
    
    def get_gdpr_policy(self) -> Optional['GDPRPolicy']:
        """Get the current GDPR policy"""
        return self._config.gdpr_policy
    
    def __repr__(self) -> str:
        stats = self.get_statistics()
        return (f"Nogger(core='{stats['core_name']}', "
                f"mode={stats['logging_mode']}, "
                f"logs={stats['total_logs']}, "
                f"colours={stats['colours_enabled']})")
    
    def __str__(self) -> str:
        return self.__repr__()

