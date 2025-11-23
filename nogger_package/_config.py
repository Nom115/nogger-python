"""
Configuration management for Nogger logging system.
Handles loading configuration from YAML files and runtime configuration.

The OutputBehaviour setting controls the unified async/sync API behaviour:
- STREAMED: Synchronous immediate output
- BATCHED: Synchronous batched output
- ASYNC_STREAMED: Asynchronous immediate output (unified API detects async context)
- ASYNC_BATCHED: Asynchronous batched output (unified API detects async context)

With unified API, the same methods (info, debug, etc.) work in both sync and async
contexts - no need for separate _async methods!
"""

import yaml
from pathlib import Path
from typing import Any, Dict, Optional, TextIO, Union, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from ._gdpr import GDPRPolicy


class LogLevel(Enum):
    """Log severity levels in order of importance"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LoggingMode(Enum):
    """Different logging output modes"""
    CONSOLE = "console"
    FILE_JSON = "file_json"
    FILE_CSV = "file_csv"
    FILE_TXT = "file_txt"
    MEMORY_ONLY = "memory_only"
    CUSTOM = "custom"


class OutputBehaviour(Enum):
    """
    How logs are written to output.
    
    Controls the unified async/sync API behaviour:
    - STREAMED: Immediate synchronous output
    - BATCHED: Buffered synchronous output (batch_size/timeout controlled)
    - ASYNC_STREAMED: Immediate async output (methods return awaitables in async contexts)
    - ASYNC_BATCHED: Buffered async output (methods return awaitables in async contexts)
    
    With ASYNC modes, the same logging methods (info, debug, etc.) automatically
    detect async contexts and return awaitables that can be awaited or ignored.
    """
    STREAMED = "streamed"
    BATCHED = "batched"
    ASYNC_STREAMED = "async_streamed"
    ASYNC_BATCHED = "async_batched"


class LoggerConfiguration:
    """Centralised configuration management for Nogger"""
    
    def __init__(self, config_file: Optional[Union[str, Path]] = None, **kwargs):
        """
        Initialise configuration from YAML file and/or kwargs.
        
        Args:
            config_file: Path to YAML configuration file (optional)
            **kwargs: Runtime configuration overrides
        """
        # Load from YAML file if provided
        file_config = {}
        if config_file:
            file_config = self._load_yaml_config(config_file)
        
        # Merge configurations: YAML < kwargs (kwargs take precedence)
        config = {**file_config, **kwargs}
        
        # Core settings
        self.core_name: str = config.get('core', 'nogger')
        self.colours_enabled: bool = config.get('colours', True)
        
        # Parse colour scheme
        colour_scheme_value = config.get('colour_scheme', 'default')
        if isinstance(colour_scheme_value, str):
            # Import here to avoid circular dependency
            from ._colours import ColourScheme
            try:
                self.colour_scheme = ColourScheme(colour_scheme_value.lower())
            except ValueError:
                self.colour_scheme = ColourScheme.DEFAULT
        else:
            self.colour_scheme = colour_scheme_value
        
        # Parse logging mode
        logging_mode_value = config.get('logging_mode', 'console')
        if isinstance(logging_mode_value, str):
            try:
                self.logging_mode = LoggingMode(logging_mode_value.lower())
            except ValueError:
                self.logging_mode = LoggingMode.CONSOLE
        else:
            self.logging_mode = logging_mode_value
        
        # Parse output behaviour
        output_behaviour_value = config.get('output_behaviour', 'streamed')
        if isinstance(output_behaviour_value, str):
            try:
                self.output_behaviour = OutputBehaviour(output_behaviour_value.lower())
            except ValueError:
                self.output_behaviour = OutputBehaviour.STREAMED
        else:
            self.output_behaviour = output_behaviour_value
        
        # Output configuration
        output_file_path = config.get('output_file_path')
        self.output_file_path: Optional[Path] = Path(output_file_path) if output_file_path else None
        self.custom_output_stream: Optional[TextIO] = config.get('custom_output_stream')
        
        # Formatting settings
        self.include_timestamp: bool = config.get('timestamp', True)
        self.timestamp_format: str = config.get('timestamp_format', '%Y-%m-%d %H:%M:%S')
        self.message_format: str = config.get('format', '{timestamp} [{level}] {core}: {message}{extra}')
        
        # Parse minimum level
        min_level_value = config.get('min_level', 'debug')
        if isinstance(min_level_value, str):
            try:
                self.minimum_level = LogLevel(min_level_value.upper())
            except ValueError:
                self.minimum_level = LogLevel.DEBUG
        else:
            self.minimum_level = min_level_value
        
        # Filtering and behaviour
        self.include_thread_info: bool = config.get('include_thread_info', False)
        self.include_task_info: bool = config.get('include_task_info', False)
        
        # Batching settings
        self.batch_size: int = config.get('batch_size', 50)
        self.batch_timeout_seconds: float = config.get('batch_timeout', 5.0)
        
        # Performance settings
        self.max_stored_logs: Optional[int] = config.get('max_stored_logs', 10000)
        self.async_queue_size: int = config.get('async_queue_size', 1000)
        
        # GDPR settings
        self.gdpr_policy: Optional['GDPRPolicy'] = None
        if 'gdpr' in config:
            from ._gdpr import load_gdpr_policy_from_dict
            self.gdpr_policy = load_gdpr_policy_from_dict(config['gdpr'])
    
    def _load_yaml_config(self, config_file: Union[str, Path]) -> Dict[str, Any]:
        """
        Load configuration from YAML file.
        
        Args:
            config_file: Path to YAML configuration file
            
        Returns:
            Dictionary of configuration values
        """
        config_path = Path(config_file)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse YAML configuration: {e}")
        except Exception as e:
            raise RuntimeError(f"Error loading configuration file: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary format.
        
        Returns:
            Dictionary representation of the configuration
        """
        return {
            'core': self.core_name,
            'colours': self.colours_enabled,
            'colour_scheme': self.colour_scheme.value if hasattr(self.colour_scheme, 'value') else str(self.colour_scheme),
            'logging_mode': self.logging_mode.value,
            'output_behaviour': self.output_behaviour.value,
            'output_file_path': str(self.output_file_path) if self.output_file_path else None,
            'timestamp': self.include_timestamp,
            'timestamp_format': self.timestamp_format,
            'format': self.message_format,
            'min_level': self.minimum_level.value,
            'include_thread_info': self.include_thread_info,
            'include_task_info': self.include_task_info,
            'batch_size': self.batch_size,
            'batch_timeout': self.batch_timeout_seconds,
            'max_stored_logs': self.max_stored_logs,
            'async_queue_size': self.async_queue_size,
        }
    
    def save_to_yaml(self, output_file: Union[str, Path]) -> None:
        """
        Save current configuration to YAML file.
        
        Args:
            output_file: Path where YAML configuration should be saved
        """
        config_dict = self.to_dict()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
    
    @classmethod
    def from_yaml(cls, config_file: Union[str, Path]) -> 'LoggerConfiguration':
        """
        Create configuration instance from YAML file.
        
        Args:
            config_file: Path to YAML configuration file
            
        Returns:
            LoggerConfiguration instance
        """
        return cls(config_file=config_file)


def create_default_config_file(output_file: Union[str, Path] = 'nogger_config.yaml') -> None:
    """
    Create a default configuration file with documentation.
    
    Args:
        output_file: Path where the default config should be created
    """
    default_config = """# Nogger Configuration File
# All settings are optional - defaults will be used if not specified

# Core Settings
core: nogger                    # Logger name/identifier
colours: true                   # Enable colour output
colour_scheme: default          # Options: default, minimal, vibrant, monochrome, dark_theme, light_theme

# Logging Mode
logging_mode: console           # Options: console, file_json, file_csv, file_txt, memory_only, custom
output_file_path: null          # Path for file-based modes (auto-generated if not specified)

# Output Behaviour
output_behaviour: streamed      # Options: streamed, batched, async_streamed, async_batched
batch_size: 50                  # Number of logs to batch (for batched modes)
batch_timeout: 5.0              # Timeout in seconds for batch processing

# Formatting
timestamp: true                 # Include timestamp in logs
timestamp_format: '%Y-%m-%d %H:%M:%S'  # Python strftime format
format: '{timestamp} [{level}] {core}: {message}{extra}'  # Message format template

# Filtering
min_level: debug                # Minimum log level: debug, info, warning, error, critical

# Additional Information
include_thread_info: false      # Include thread ID in logs
include_task_info: false        # Include async task ID in logs

# Performance
max_stored_logs: 10000          # Maximum logs to keep in memory (null for unlimited)
async_queue_size: 1000          # Size of async processing queue

# GDPR Compliance Settings
gdpr:
  enabled: false                # Enable GDPR data sanitization
  scan_message: true            # Scan log messages for sensitive patterns
  scan_unstructured_fields: true # Scan unstructured data for patterns
  hash_salt: 'nogger-gdpr-salt' # Salt for pseudonymisation
  
  # Fields to always drop (never log)
  forbidden_fields:
    - password
    - passwd
    - pwd
    - secret_key
    - api_secret
    - private_key
  
  # Sensitive fields with actions: mask, drop, or hash
  sensitive_fields:
    password: drop
    token: drop
    api_key: drop
    secret: drop
    email: mask
    phone: mask
    address: mask
    ssn: drop
    credit_card: drop
    user_id: hash
    username: hash
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(default_config)


def cli_create_config() -> None:
    """
    CLI entry point for creating a default config file.
    Used by the nogger-config command after installation.
    """
    import sys
    import os
    from pathlib import Path
    
    # Determine output location - use current directory by default
    if len(sys.argv) > 1:
        output_file = Path(sys.argv[1])
    else:
        # Use current working directory
        output_file = Path.cwd() / 'nogger_config.yaml'
    
    # Create config file
    create_default_config_file(output_file)
    
    print(f"✓ Created default Nogger configuration at: {output_file}")
    print(f"  Edit this file to customise your logging settings.")


def load_config_from_yaml(config_file: Union[str, Path]) -> LoggerConfiguration:
    """
    Convenience function to load configuration from YAML file.
    
    Args:
        config_file: Path to YAML configuration file
        
    Returns:
        LoggerConfiguration instance
    """
    return LoggerConfiguration.from_yaml(config_file)
