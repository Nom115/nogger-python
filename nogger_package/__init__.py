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
]