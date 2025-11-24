"""
Nogger - A Better Logger

A comprehensive, async-friendly logging library with British English throughout.
"""

from .nogger import (
    Nogger,
    LogEntry,
)

from ._config import (
    LogLevel,
    LoggingMode,
    OutputBehaviour,
    LoggerConfiguration,
    create_default_config_file,
    load_config_from_yaml
)

from ._colours import (
    ColourCodes,
    ColourScheme,
    ColourManager
)

from ._gdpr import (
    GDPRPolicy,
    RetentionPolicy,
    SensitiveAction,
    create_default_gdpr_policy,
    load_gdpr_policy_from_dict,
    sanitize_log_entry,
    mask_value,
    hash_value,
)


# Global logger instance for get_logger()
_global_logger = None


def get_logger(name: str = None, **kwargs) -> Nogger:
    """
    Get or create a logger instance.
    
    On first call, creates a global logger with the provided configuration.
    Subsequent calls return the same logger instance (singleton pattern).
    
    Args:
        name: Optional logger name (overrides 'core' if provided)
        **kwargs: Configuration options passed to Nogger constructor
                  (only used on first call)
    
    Returns:
        Nogger instance
        
    Example:
        # First call creates the logger
        logger = get_logger("MyApp", colours=True, output_behaviour='async_streamed')
        
        # Subsequent calls return the same instance
        logger2 = get_logger()  # Same as logger
        
        # Use module name as context
        logger = get_logger(__name__)
    """
    global _global_logger
    
    if _global_logger is None:
        # First call - create logger with configuration
        if name:
            kwargs['core'] = name
        _global_logger = Nogger(**kwargs)
    
    return _global_logger


def reset_logger():
    """
    Reset the global logger instance.
    
    Useful for testing or when you need to reconfigure the logger.
    Performs graceful shutdown before resetting.
    """
    global _global_logger
    
    if _global_logger:
        _global_logger.shutdown()
        _global_logger = None


__version__ = "1.0.0"
__author__ = "Nogger Development Team"
__description__ = "A comprehensive, async-friendly logging library with British English"

__all__ = [
    'Nogger',
    'LogLevel', 
    'LoggingMode',
    'OutputBehaviour',
    'LogEntry',
    'LoggerConfiguration',
    'ColourCodes',
    'ColourScheme',
    'ColourManager',
    'create_default_config_file',
    'load_config_from_yaml',
    'GDPRPolicy',
    'RetentionPolicy',
    'SensitiveAction',
    'create_default_gdpr_policy',
    'load_gdpr_policy_from_dict',
    'sanitize_log_entry',
    'mask_value',
    'hash_value',
    'get_logger',
    'reset_logger',
]