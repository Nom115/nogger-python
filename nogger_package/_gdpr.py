"""
GDPR Compliance Module for Nogger
Handles data sanitization, masking, and retention policies for privacy compliance.
"""

import re
import hashlib
import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Callable, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum

if TYPE_CHECKING:
    from .nogger import LogEntry


# ============================================================================
# GDPR POLICIES AND CONFIGURATION
# ============================================================================

class SensitiveAction(Enum):
    """Actions to take on sensitive fields"""
    MASK = "mask"
    DROP = "drop"
    HASH = "hash"


@dataclass
class GDPRPolicy:
    """
    GDPR compliance policy configuration.
    
    Attributes:
        enabled: Whether GDPR processing is enabled
        sensitive_fields: Dict mapping field names to actions (mask/drop/hash)
        forbidden_fields: List of field names to always drop
        scan_message: Whether to scan the main message for sensitive patterns
        scan_unstructured_fields: Whether to scan unstructured data for patterns
        hash_salt: Salt for hashing operations (pseudonymisation)
    """
    enabled: bool = False
    sensitive_fields: Dict[str, str] = field(default_factory=dict)
    forbidden_fields: List[str] = field(default_factory=list)
    scan_message: bool = True
    scan_unstructured_fields: bool = True
    hash_salt: str = "nogger-gdpr-salt"
    
    def __post_init__(self):
        """Validate and normalise policy configuration"""
        # Normalise sensitive field actions to lowercase
        self.sensitive_fields = {
            k: v.lower() for k, v in self.sensitive_fields.items()
        }
        
        # Validate actions
        valid_actions = {action.value for action in SensitiveAction}
        for field_name, action in self.sensitive_fields.items():
            if action not in valid_actions:
                raise ValueError(
                    f"Invalid action '{action}' for field '{field_name}'. "
                    f"Must be one of: {', '.join(valid_actions)}"
                )


@dataclass
class RetentionPolicy:
    """
    Data retention policy configuration.
    
    Attributes:
        max_days: Maximum age of logs in days (None = unlimited)
        max_bytes: Maximum total size in bytes (None = unlimited)
        auto_cleanup: Whether to automatically apply retention rules
    """
    max_days: Optional[int] = 30
    max_bytes: Optional[int] = None
    auto_cleanup: bool = False


# ============================================================================
# REGEX PATTERNS FOR SENSITIVE DATA DETECTION
# ============================================================================

# Email pattern - matches most common email formats
EMAIL_RE = re.compile(
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
)

# Phone patterns - UK and international formats  
PHONE_UK_RE = re.compile(
    r'\b(?:\+44\s?|0)(?:\d{2}\s?\d{4}\s?\d{4}|\d{3}\s?\d{3}\s?\d{4})\b'
)
PHONE_INTERNATIONAL_RE = re.compile(
    r'\+\d{1,3}[\s-]?\(?\d{2,4}\)?[\s-]?\d{3,4}[\s-]?\d{4}\b'
)

# IP addresses - IPv4 and IPv6 (more specific to avoid false positives)
IP_V4_RE = re.compile(
    r'\b(?:(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\.){3}(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\b'
)
IP_V6_RE = re.compile(
    r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b'
)

# UK Postcode pattern
POSTCODE_UK_RE = re.compile(
    r'\b[A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2}\b',
    re.IGNORECASE
)

# Credit card pattern (basic detection)
CREDIT_CARD_RE = re.compile(
    r'\b(?:\d{4}[\s-]?){3}\d{4}\b'
)

# National Insurance Number (UK)
NI_NUMBER_RE = re.compile(
    r'\b[A-Z]{2}\d{6}[A-Z]\b',
    re.IGNORECASE
)

# Patterns dictionary with (regex, replacement) tuples
PATTERNS = {
    "email": (EMAIL_RE, "[EMAIL_REDACTED]"),
    "phone_uk": (PHONE_UK_RE, "[PHONE_REDACTED]"),
    "phone": (PHONE_INTERNATIONAL_RE, "[PHONE_REDACTED]"),
    "ipv4": (IP_V4_RE, "[IP_REDACTED]"),
    "ipv6": (IP_V6_RE, "[IP_REDACTED]"),
    "postcode": (POSTCODE_UK_RE, "[POSTCODE_REDACTED]"),
    "credit_card": (CREDIT_CARD_RE, "[CARD_REDACTED]"),
    "ni_number": (NI_NUMBER_RE, "[NI_REDACTED]"),
}


def mask_with_patterns(text: str, patterns: Optional[Dict[str, Tuple]] = None) -> str:
    """
    Scan text and mask sensitive patterns with replacements.
    
    Args:
        text: Text to scan and mask
        patterns: Optional custom patterns dict (defaults to PATTERNS)
    
    Returns:
        Text with sensitive patterns masked
    """
    if not isinstance(text, str):
        return text
    
    if patterns is None:
        patterns = PATTERNS
    
    masked_text = text
    for name, (pattern, replacement) in patterns.items():
        masked_text = pattern.sub(replacement, masked_text)
    
    return masked_text


# ============================================================================
# FIELD-LEVEL SANITIZATION
# ============================================================================

def mask_value(value: Any, mask_char: str = "*") -> str:
    """
    Mask a value while preserving length information.
    
    Args:
        value: Value to mask
        mask_char: Character to use for masking
    
    Returns:
        Masked string representation
    """
    str_value = str(value)
    length = len(str_value)
    
    if length <= 2:
        return mask_char * length
    
    # Show first and last character for context
    return str_value[0] + (mask_char * (length - 2)) + str_value[-1]


def hash_value(value: Any, salt: str = "nogger-gdpr") -> str:
    """
    Hash a value for pseudonymisation (one-way transformation).
    
    Args:
        value: Value to hash
        salt: Salt for hashing
    
    Returns:
        Hashed value as hex string
    """
    str_value = str(value)
    salted = f"{salt}{str_value}".encode('utf-8')
    return hashlib.sha256(salted).hexdigest()[:16]


def sanitize_fields(event_dict: Dict[str, Any], policy: GDPRPolicy) -> Dict[str, Any]:
    """
    Sanitize fields in an event dictionary according to GDPR policy.
    
    This handles field-level operations:
    - Drop forbidden fields
    - Mask/drop/hash sensitive fields
    
    Args:
        event_dict: Event data as dictionary
        policy: GDPR policy to apply
    
    Returns:
        Sanitized event dictionary
    """
    if not policy.enabled:
        return event_dict
    
    sanitized = event_dict.copy()
    
    # Drop forbidden fields
    for field_name in policy.forbidden_fields:
        if field_name in sanitized:
            del sanitized[field_name]
    
    # Handle sensitive fields
    for field_name, action in policy.sensitive_fields.items():
        if field_name not in sanitized:
            continue
        
        if action == SensitiveAction.DROP.value:
            del sanitized[field_name]
        
        elif action == SensitiveAction.MASK.value:
            sanitized[field_name] = mask_value(sanitized[field_name])
        
        elif action == SensitiveAction.HASH.value:
            sanitized[field_name] = hash_value(
                sanitized[field_name], 
                policy.hash_salt
            )
    
    return sanitized


def sanitize_nested_dict(data: Dict[str, Any], policy: GDPRPolicy) -> Dict[str, Any]:
    """
    Recursively sanitize nested dictionaries.
    
    Args:
        data: Nested dictionary to sanitize
        policy: GDPR policy to apply
    
    Returns:
        Sanitized nested dictionary
    """
    if not policy.enabled:
        return data
    
    sanitized = {}
    
    for key, value in data.items():
        # Skip forbidden fields
        if key in policy.forbidden_fields:
            continue
        
        # Handle sensitive fields
        if key in policy.sensitive_fields:
            action = policy.sensitive_fields[key]
            
            if action == SensitiveAction.DROP.value:
                continue
            elif action == SensitiveAction.MASK.value:
                sanitized[key] = mask_value(value)
                continue
            elif action == SensitiveAction.HASH.value:
                sanitized[key] = hash_value(value, policy.hash_salt)
                continue
        
        # Recursively handle nested structures
        if isinstance(value, dict):
            sanitized[key] = sanitize_nested_dict(value, policy)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_nested_dict(item, policy) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            sanitized[key] = value
    
    return sanitized


# ============================================================================
# EVENT-LEVEL SANITIZATION
# ============================================================================

def sanitize_log_entry(log_entry: "LogEntry", policy: GDPRPolicy) -> "LogEntry":
    """
    Sanitize a LogEntry object according to GDPR policy.
    
    This is the main entry point for GDPR processing. It:
    1. Sanitizes field-level data
    2. Scans message content for sensitive patterns
    3. Scans unstructured fields for patterns
    
    Args:
        log_entry: LogEntry to sanitize
        policy: GDPR policy to apply
    
    Returns:
        New sanitized LogEntry
    """
    if not policy.enabled:
        return log_entry
    
    # Convert to dict for processing
    from .nogger import LogEntry
    
    # Create a copy to avoid modifying original
    sanitized_entry = LogEntry(
        timestamp=log_entry.timestamp,
        level=log_entry.level,
        core=log_entry.core,
        message=log_entry.message,
        extra_data=log_entry.extra_data.copy() if log_entry.extra_data else {},
        thread_id=log_entry.thread_id,
        task_id=log_entry.task_id
    )
    
    # Step 1: Scan and mask message if enabled
    if policy.scan_message and sanitized_entry.message:
        sanitized_entry.message = mask_with_patterns(sanitized_entry.message)
    
    # Step 2: Sanitize extra_data fields
    if sanitized_entry.extra_data:
        sanitized_entry.extra_data = sanitize_nested_dict(
            sanitized_entry.extra_data, 
            policy
        )
        
        # Step 3: Scan unstructured fields if enabled
        if policy.scan_unstructured_fields:
            sanitized_entry.extra_data = _scan_unstructured_fields(
                sanitized_entry.extra_data,
                policy
            )
    
    return sanitized_entry


def _scan_unstructured_fields(data: Dict[str, Any], policy: GDPRPolicy) -> Dict[str, Any]:
    """
    Scan unstructured string fields for sensitive patterns.
    
    Args:
        data: Dictionary to scan
        policy: GDPR policy
    
    Returns:
        Dictionary with masked sensitive patterns
    """
    scanned = {}
    
    for key, value in data.items():
        # Skip fields already marked as sensitive (they're handled separately)
        if key in policy.sensitive_fields or key in policy.forbidden_fields:
            scanned[key] = value
            continue
        
        if isinstance(value, str):
            # Scan string values for patterns
            scanned[key] = mask_with_patterns(value)
        elif isinstance(value, dict):
            # Recursively scan nested dicts
            scanned[key] = _scan_unstructured_fields(value, policy)
        elif isinstance(value, list):
            # Scan list items
            scanned[key] = [
                _scan_unstructured_fields(item, policy) if isinstance(item, dict)
                else mask_with_patterns(item) if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            scanned[key] = value
    
    return scanned


def sanitize_event_dict(event_dict: Dict[str, Any], policy: GDPRPolicy) -> Dict[str, Any]:
    """
    Sanitize a raw event dictionary (for external integrations).
    
    Args:
        event_dict: Event as dictionary
        policy: GDPR policy to apply
    
    Returns:
        Sanitized event dictionary
    """
    if not policy.enabled:
        return event_dict
    
    sanitized = event_dict.copy()
    
    # Sanitize field-level data
    sanitized = sanitize_fields(sanitized, policy)
    
    # Scan message if present
    if policy.scan_message and 'message' in sanitized:
        sanitized['message'] = mask_with_patterns(sanitized['message'])
    
    # Scan unstructured fields
    if policy.scan_unstructured_fields and 'extra_data' in sanitized:
        sanitized['extra_data'] = _scan_unstructured_fields(
            sanitized['extra_data'],
            policy
        )
    
    return sanitized


# ============================================================================
# RETENTION POLICY HELPERS
# ============================================================================

def should_delete_file(file_path: Path, policy: RetentionPolicy) -> bool:
    """
    Check if a file should be deleted according to retention policy.
    
    Args:
        file_path: Path to file to check
        policy: Retention policy to apply
    
    Returns:
        True if file should be deleted, False otherwise
    """
    if not file_path.exists():
        return False
    
    # Check age-based retention
    if policy.max_days is not None:
        file_age = datetime.datetime.now() - datetime.datetime.fromtimestamp(
            file_path.stat().st_mtime
        )
        if file_age.days > policy.max_days:
            return True
    
    return False


def apply_retention(directory: Path, policy: RetentionPolicy, pattern: str = "*.log") -> Dict[str, Any]:
    """
    Apply retention policy to files in a directory.
    
    Args:
        directory: Directory to scan
        policy: Retention policy to apply
        pattern: File pattern to match (e.g., "*.log", "*.json")
    
    Returns:
        Dictionary with retention statistics:
        - files_checked: Number of files examined
        - files_deleted: Number of files deleted
        - bytes_freed: Bytes freed by deletion
    """
    if not directory.exists() or not directory.is_dir():
        return {
            'files_checked': 0,
            'files_deleted': 0,
            'bytes_freed': 0
        }
    
    stats = {
        'files_checked': 0,
        'files_deleted': 0,
        'bytes_freed': 0
    }
    
    files_to_delete = []
    total_size = 0
    
    # Scan directory for matching files
    for file_path in directory.glob(pattern):
        if not file_path.is_file():
            continue
        
        stats['files_checked'] += 1
        file_size = file_path.stat().st_size
        total_size += file_size
        
        # Check if file should be deleted based on age
        if should_delete_file(file_path, policy):
            files_to_delete.append((file_path, file_size))
    
    # Check size-based retention
    if policy.max_bytes is not None and total_size > policy.max_bytes:
        # Sort by modification time (oldest first)
        all_files = sorted(
            directory.glob(pattern),
            key=lambda p: p.stat().st_mtime
        )
        
        current_size = total_size
        for file_path in all_files:
            if current_size <= policy.max_bytes:
                break
            
            file_size = file_path.stat().st_size
            if (file_path, file_size) not in files_to_delete:
                files_to_delete.append((file_path, file_size))
                current_size -= file_size
    
    # Delete files if auto_cleanup is enabled
    if policy.auto_cleanup:
        for file_path, file_size in files_to_delete:
            try:
                file_path.unlink()
                stats['files_deleted'] += 1
                stats['bytes_freed'] += file_size
            except Exception as e:
                # Log error but continue
                print(f"Error deleting {file_path}: {e}")
    
    return stats


def cleanup_old_logs(
    log_directory: Path,
    max_days: int,
    dry_run: bool = False,
    pattern: str = "*.log"
) -> List[Path]:
    """
    Convenience function to clean up old log files.
    
    Args:
        log_directory: Directory containing log files
        max_days: Maximum age in days
        dry_run: If True, only return files that would be deleted
        pattern: File pattern to match
    
    Returns:
        List of file paths that were (or would be) deleted
    """
    policy = RetentionPolicy(
        max_days=max_days,
        auto_cleanup=not dry_run
    )
    
    deleted_files = []
    
    for file_path in log_directory.glob(pattern):
        if not file_path.is_file():
            continue
        
        if should_delete_file(file_path, policy):
            deleted_files.append(file_path)
            
            if not dry_run:
                try:
                    file_path.unlink()
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")
    
    return deleted_files


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_default_gdpr_policy() -> GDPRPolicy:
    """
    Create a default GDPR policy with common sensitive fields.
    
    Returns:
        Default GDPRPolicy instance
    """
    return GDPRPolicy(
        enabled=False,
        sensitive_fields={
            'password': 'drop',
            'token': 'drop',
            'api_key': 'drop',
            'secret': 'drop',
            'email': 'mask',
            'phone': 'mask',
            'address': 'mask',
            'ssn': 'drop',
            'credit_card': 'drop',
            'user_id': 'hash',
            'username': 'hash',
        },
        forbidden_fields=[
            'password',
            'passwd',
            'pwd',
            'secret_key',
            'api_secret',
            'private_key',
        ],
        scan_message=True,
        scan_unstructured_fields=True
    )


def load_gdpr_policy_from_dict(config: Dict[str, Any]) -> GDPRPolicy:
    """
    Load GDPR policy from configuration dictionary.
    
    Args:
        config: Configuration dictionary from YAML or other source
    
    Returns:
        GDPRPolicy instance
    """
    return GDPRPolicy(
        enabled=config.get('enabled', False),
        sensitive_fields=config.get('sensitive_fields', {}),
        forbidden_fields=config.get('forbidden_fields', []),
        scan_message=config.get('scan_message', True),
        scan_unstructured_fields=config.get('scan_unstructured_fields', True),
        hash_salt=config.get('hash_salt', 'nogger-gdpr-salt')
    )


def validate_gdpr_compliance(event_dict: Dict[str, Any], policy: GDPRPolicy) -> List[str]:
    """
    Validate an event against GDPR policy and return list of violations.
    
    Args:
        event_dict: Event to validate
        policy: GDPR policy to check against
    
    Returns:
        List of violation messages (empty if compliant)
    """
    violations = []
    
    if not policy.enabled:
        return violations
    
    # Check for forbidden fields
    for field in policy.forbidden_fields:
        if field in event_dict:
            violations.append(f"Forbidden field present: {field}")
        
        # Check nested in extra_data
        if 'extra_data' in event_dict and isinstance(event_dict['extra_data'], dict):
            if field in event_dict['extra_data']:
                violations.append(f"Forbidden field in extra_data: {field}")
    
    # Check for unsanitized patterns in message
    if policy.scan_message and 'message' in event_dict:
        message = event_dict['message']
        for pattern_name, (pattern, _) in PATTERNS.items():
            if pattern.search(message):
                violations.append(f"Sensitive pattern in message: {pattern_name}")
    
    return violations
