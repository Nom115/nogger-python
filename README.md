# Nogger - A Better Logger

A comprehensive, async-friendly logging library for Python with extensive customisation options, British English throughout, GDPR compliance, and enterprise-grade features.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![GDPR Compliant](https://img.shields.io/badge/GDPR-compliant-green.svg)](#gdpr-compliance)
[![British English](https://img.shields.io/badge/spelling-British%20English-red.svg)](https://en.wikipedia.org/wiki/British_English)

## Why Nogger?

Nogger is designed for modern Python applications that need:
- **Production-ready logging** with GDPR compliance out of the box
- **Async-first architecture** that doesn't block your application
- **British English** throughout (because `colour` is spelled correctly)
- **Zero dependencies** (except PyYAML for configuration)
- **Enterprise features** without enterprise complexity

## Key Features

### 🔒 **GDPR Compliance**
- **Automatic Pattern Detection**: Masks emails, phone numbers, IPs, credit cards, and more
- **Field-Level Sanitization**: Mask, drop, or hash sensitive fields
- **Flexible Policies**: Configure via YAML or programmatically
- **Data Retention**: Automatic log cleanup based on age or size
- **Pseudonymisation**: Hash user IDs for correlation without exposure

### 🎨 **British English Throughout**
- Proper British spelling: `colours`, `colour_scheme`, `initialise`, `behaviour`
- British terminology and documentation style
- No compromises on language consistency

### 🚀 **Multiple Logging Modes**
- **Console**: Standard terminal output with colour support
- **File JSON**: Structured JSON output with full metadata
- **File CSV**: Spreadsheet-compatible format for analysis  
- **File TXT**: Human-readable plain text format
- **Memory Only**: Store logs without any output (perfect for testing)
- **Custom**: Extensible for custom output handlers

### ⚡ **Output Behaviours**
- **Streamed**: Immediate output as logs arrive
- **Batched**: Collect logs and output in efficient batches (configurable size/timeout)
- **Async Streamed**: Non-blocking immediate processing
- **Async Batched**: Non-blocking batch processing with async/await

### 🎨 **Advanced Colour System**
- **6 Built-in Colour Schemes**: Default, Minimal, Vibrant, Dark Theme, Light Theme, Monochrome
- **Runtime Colour Control**: Enable/disable/toggle colours dynamically
- **Per-Element Colours**: Different colours for timestamp, level, core, message
- **Terminal Compatibility**: Automatic ANSI colour code handling

### 🔧 **Comprehensive Configuration**
- **YAML Configuration**: Full-featured config files with sensible defaults
- **Runtime Overrides**: Change any setting without restarting
- **Flexible Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL with filtering
- **Rich Formatting**: Customisable message formats with placeholders
- **Timestamp Control**: Multiple formats, enable/disable per message
- **Thread Safety**: Full thread-safe operations with thread ID tracking
- **Async Support**: Native async/await compatibility throughout
- **Performance Optimised**: Efficient batching and memory management

## Installation

```bash
# Install from PyPI
pip install nogger

# Generate default config file in your project
nogger-config
```

Or install from source:

```bash
# Clone the repository
git clone https://github.com/Nom115/nogger-python.git
cd nogger-python

# Install in development mode
pip install -e .
```

## Quick Start

### Basic Usage

```python
from nogger_package import Nogger

# Create a basic logger
logger = Nogger(core="MyApp", colours=True)

# Basic logging methods
logger.info("Application started")
logger.debug("Debug information")
logger.warning("Low memory detected")
logger.error("Database connection failed")
logger.critical("System failure imminent")

# Rich context with extra data
logger.info("User authentication", extra_data={
    "user_id": 12345, 
    "ip": "192.168.1.1",
    "country": "GB"
})
```

### With GDPR Protection

```python
from nogger_package import Nogger

# Enable GDPR compliance
logger = Nogger(core="MyApp", gdpr={'enabled': True})

# Sensitive data is automatically sanitized
logger.info("User login", extra_data={
    "email": "user@example.com",      # → [EMAIL_REDACTED]
    "password": "secret123",          # → dropped
    "ip": "192.168.1.100"             # → [IP_REDACTED]
})

# Patterns in messages are also masked
logger.warning("Failed login for john@example.com from 192.168.1.50")
# Output: Failed login for [EMAIL_REDACTED] from [IP_REDACTED]
```

### Using Configuration Files

```python
from nogger_package import Nogger

# Load configuration from YAML
logger = Nogger(config_file='nogger_config.yaml')

# All settings from YAML are applied
logger.info("Configured from YAML file")

# Runtime overrides still work
logger.set_minimum_level('WARNING')
```

### Async Support

**Unified API**: The same methods work in both sync and async contexts!

```python
from nogger_package import Nogger
import asyncio

async def main():
    logger = Nogger(
        core="AsyncApp",
        output_behaviour='async_streamed'
    )
    
    # Same methods, just await in async contexts!
    await logger.info("Async operation started")
    await logger.debug("Processing data")
    await logger.info("Async operation completed")
    
    # Or use without await (fire-and-forget)
    logger.info("This queues automatically")
    
    # Graceful shutdown
    await logger.shutdown_async()

asyncio.run(main())
```

**Key Features:**
- **No `_async` suffix needed** - Same API everywhere
- **Context-aware** - Automatically detects async execution
- **Config-driven** - Behaviour controlled by `output_behaviour`
- **Optional await** - Logs are processed either way

## Configuration

### YAML Configuration

Generate a default config file:

```bash
nogger-config
```

This creates `nogger_config.yaml` in your current directory:

```yaml
# Core Settings
core: nogger
colours: true
colour_scheme: default

# Logging Mode
logging_mode: console
output_file_path: null

# Output Behaviour
output_behaviour: streamed
batch_size: 50
batch_timeout: 5.0

# Formatting
timestamp: true
timestamp_format: '%Y-%m-%d %H:%M:%S'
format: '{timestamp} [{level}] {core}: {message}{extra}'

# Filtering
min_level: debug

# Performance
max_stored_logs: 10000
async_queue_size: 1000

# GDPR Compliance
gdpr:
  enabled: false
  scan_message: true
  scan_unstructured_fields: true
  forbidden_fields:
    - password
    - secret_key
  sensitive_fields:
    email: mask
    user_id: hash
    token: drop
```

### Programmatic Configuration

### Programmatic Configuration

```python
from nogger_package import (
    Nogger, 
    LogLevel, 
    LoggingMode, 
    OutputBehaviour, 
    ColourScheme
)

# Create logger with comprehensive options
logger = Nogger(
    core="MyApp",
    colours=True,
    colour_scheme=ColourScheme.VIBRANT,
    logging_mode=LoggingMode.FILE_JSON,
    output_behaviour=OutputBehaviour.BATCHED,
    output_file_path='logs/app.json',
    batch_size=100,
    batch_timeout=5.0,
    min_level=LogLevel.INFO,
    include_thread_info=True,
    include_task_info=True,
    timestamp_format='%Y-%m-%d %H:%M:%S',
    max_stored_logs=10000
)

# Runtime configuration changes
logger.set_colour_scheme(ColourScheme.DARK_THEME)
logger.set_logging_mode(LoggingMode.CONSOLE)
logger.set_minimum_level(LogLevel.WARNING)
logger.enable_colours()
logger.set_batch_size(200)
```

## GDPR Compliance

Nogger includes comprehensive GDPR compliance features built-in, providing automatic data protection and privacy compliance.

### Quick GDPR Setup

```python
from nogger_package import Nogger, GDPRPolicy

# Option 1: Enable with defaults
logger = Nogger(core="app", gdpr={'enabled': True})

# Option 2: Custom policy
policy = GDPRPolicy(
    enabled=True,
    sensitive_fields={
        'email': 'mask',        # Partially mask
        'user_id': 'hash',      # One-way hash
        'password': 'drop',     # Remove completely
    },
    forbidden_fields=['secret_key', 'api_token'],
    scan_message=True,
    scan_unstructured_fields=True,
    hash_salt='my-unique-salt-2024'
)

logger = Nogger(core="app")
logger.set_gdpr_policy(policy)
```

### Automatic Pattern Detection

Nogger automatically detects and masks sensitive patterns:

```python
logger = Nogger(gdpr={'enabled': True})

# These patterns are automatically detected and masked:
logger.warning("User john@example.com from IP 192.168.1.1")
# Output: User [EMAIL_REDACTED] from IP [IP_REDACTED]

logger.error("Payment failed for card 1234 5678 9012 3456")
# Output: Payment failed for card [CARD_REDACTED]

logger.info("Called from +44 20 1234 5678")
# Output: Called from [PHONE_REDACTED]
```

**Detected Patterns:**
- Email addresses
- Phone numbers (UK & International)
- IP addresses (IPv4 & IPv6)
- Credit card numbers
- UK Postcodes
- National Insurance numbers

### Field-Level Sanitization

```python
logger = Nogger(gdpr={'enabled': True})

logger.info("User registration", extra_data={
    "username": "john_doe",           # Unaffected
    "email": "john@example.com",      # → [EMAIL_REDACTED]
    "password": "secret123",          # → dropped entirely
    "user_id": "USER123",             # → hashed to "a1b2c3d4..."
    "address": "123 Main St",         # → a*************t
})
```

### Data Retention

```python
from nogger_package import RetentionPolicy, apply_retention
from pathlib import Path

# Define retention policy
policy = RetentionPolicy(
    max_days=30,        # Delete logs older than 30 days
    max_bytes=1048576,  # Keep total size under 1MB
    auto_cleanup=True
)

# Apply to log directory
stats = apply_retention(
    directory=Path('/var/log/myapp'),
    policy=policy,
    pattern='*.log'
)

print(f"Deleted {stats['files_deleted']} files")
print(f"Freed {stats['bytes_freed']} bytes")
```

### GDPR Best Practices

1. **Enable GDPR in Production**: Always enable GDPR for production logs
2. **Review Default Policy**: Customize the default policy for your domain
3. **Use Hashing for IDs**: Hash user IDs to allow correlation without exposure
4. **Drop Secrets**: Always drop passwords, tokens, and API keys
5. **Regular Retention**: Implement retention policies to minimize data exposure
6. **Test Sanitization**: Verify sensitive data is properly masked before production
7. **Document Fields**: Maintain a list of sensitive fields specific to your application

### GDPR Compliance Checklist

- ✅ **Data Minimization**: Only log necessary information
- ✅ **Purpose Limitation**: Logs are used only for their intended purpose
- ✅ **Storage Limitation**: Retention policies automatically delete old logs
- ✅ **Confidentiality**: Sensitive data is masked/dropped/hashed
- ✅ **Integrity**: Original intent preserved while protecting privacy
- ✅ **Accountability**: Policy configuration is auditable
- ✅ **Right to be Forgotten**: Use hashing for pseudonymised correlation

### Complete GDPR Configuration Example

```yaml
gdpr:
  enabled: true
  scan_message: true
  scan_unstructured_fields: true
  hash_salt: 'your-unique-salt-2024'
  
  forbidden_fields:
    - password
    - passwd
    - pwd
    - secret
    - secret_key
    - api_secret
    - api_key
    - token
    - private_key
    - auth_token
  
  sensitive_fields:
    # Personal Identifiable Information
    email: mask
    phone: mask
    phone_number: mask
    address: mask
    full_name: mask
    
    # Financial Data
    credit_card: drop
    card_number: drop
    account_number: mask
    sort_code: mask
    iban: mask
    
    # Identification
    ssn: drop
    national_insurance: drop
    passport_number: drop
    drivers_license: drop
    
    # Correlation IDs (use hash to maintain relationships)
    user_id: hash
    customer_id: hash
    session_id: hash
    
    # Business Sensitive
    salary: drop
    wage: drop
    balance: drop
```

### GDPR Utility Functions

```python
from nogger_package import mask_value, hash_value, sanitize_log_entry

# Mask values directly
masked = mask_value("sensitive_data")  # → "s************a"

# Hash for pseudonymisation
hashed = hash_value("user123", salt="my-salt")  # → "a1b2c3d4e5f6g7h8"

# Sanitize a log entry manually
from nogger_package import LogEntry, GDPRPolicy
policy = GDPRPolicy(enabled=True)
sanitized_entry = sanitize_log_entry(log_entry, policy)
```

## Logging Modes

### Console Logging (Default)

```python
logger = Nogger(core="MyApp", colours=True, colour_scheme=ColourScheme.VIBRANT)
logger.info("Colourful console output")
```

### File Logging

```python
# JSON output
logger = Nogger(
    core="MyApp",
    logging_mode=LoggingMode.FILE_JSON,
    output_file_path='logs/app.json'
)

# CSV output
logger = Nogger(
    core="MyApp",
    logging_mode=LoggingMode.FILE_CSV,
    output_file_path='logs/app.csv'
)

# Plain text output
logger = Nogger(
    core="MyApp",
    logging_mode=LoggingMode.FILE_TXT,
    output_file_path='logs/app.log'
)
```

### Memory-Only Logging

Perfect for testing:

```python
logger = Nogger(
    core="TestApp",
    logging_mode=LoggingMode.MEMORY_ONLY
)

logger.info("Test message")
logs = logger.get_logs()
assert len(logs) == 1
```

## Output Behaviours

### Streamed (Immediate)

```python
logger = Nogger(output_behaviour=OutputBehaviour.STREAMED)
logger.info("Appears immediately")
```

### Batched (Efficient)

```python
logger = Nogger(
    output_behaviour=OutputBehaviour.BATCHED,
    batch_size=100,        # Flush after 100 logs
    batch_timeout=5.0      # Or after 5 seconds
)

# Logs are collected and written in batches
for i in range(150):
    logger.info(f"Log {i}")

# Force flush remaining logs
logger.flush_batches()
```

### Async Processing

```python
import asyncio

async def main():
    logger = Nogger(
        output_behaviour=OutputBehaviour.ASYNC_STREAMED,
        async_queue_size=1000
    )
    
    # Non-blocking logging
    await logger.info_async("Async log 1")
    await logger.warning_async("Async log 2")
    
    # Graceful shutdown
    await logger.shutdown_async()

asyncio.run(main())
```

## Colour Schemes

Nogger includes 6 built-in colour schemes:

```python
from nogger_package import Nogger, ColourScheme

# Default: Balanced colours for general use
logger = Nogger(colour_scheme=ColourScheme.DEFAULT)

# Vibrant: High-contrast, eye-catching colours
logger = Nogger(colour_scheme=ColourScheme.VIBRANT)

# Minimal: Subtle, professional colours
logger = Nogger(colour_scheme=ColourScheme.MINIMAL)

# Dark Theme: Optimised for dark terminals
logger = Nogger(colour_scheme=ColourScheme.DARK_THEME)

# Light Theme: Optimised for light terminals
logger = Nogger(colour_scheme=ColourScheme.LIGHT_THEME)

# Monochrome: No colours, just bold/dim
logger = Nogger(colour_scheme=ColourScheme.MONOCHROME)
```

## API Reference

### Core Methods

### Core Methods

#### Logging Methods

**Unified API** - Same methods work in both sync and async contexts!

```python
# Main logging method
logger.add(message, level=LogLevel.INFO, **kwargs)

# Convenience methods - work everywhere
logger.debug(message, **kwargs)
logger.info(message, **kwargs)
logger.warning(message, **kwargs)
logger.error(message, **kwargs)
logger.critical(message, **kwargs)

# In async contexts with async output behaviour, simply await:
await logger.debug(message, **kwargs)
await logger.info(message, **kwargs)
await logger.warning(message, **kwargs)
await logger.error(message, **kwargs)
await logger.critical(message, **kwargs)
```

**How It Works:**
- **Sync Mode** (`STREAMED`/`BATCHED`): Methods execute immediately
- **Async Mode** (`ASYNC_STREAMED`/`ASYNC_BATCHED`): Methods return awaitables in async contexts
- **Context Detection**: Automatically detects if you're in an async function
- **Optional Await**: Logs are queued either way; await ensures worker is running

#### Configuration Methods

```python
# Logging mode
logger.set_logging_mode(LoggingMode.FILE_JSON, output_file_path='logs/app.json')

# Output behaviour
logger.set_output_behaviour(OutputBehaviour.BATCHED)

# Log level filtering
logger.set_minimum_level(LogLevel.WARNING)

# Colours
logger.enable_colours()
logger.disable_colours()
logger.toggle_colours()
logger.set_colour_scheme(ColourScheme.VIBRANT)

# Formatting
logger.set_format('{timestamp} [{level}] {message}')
logger.set_timestamp_format('%Y-%m-%d %H:%M:%S')
logger.enable_timestamp()
logger.disable_timestamp()

# Batching
logger.set_batch_size(200)
logger.set_batch_timeout(10.0)
logger.flush_batches()

# GDPR
logger.enable_gdpr(policy=None)  # Uses default if policy not provided
logger.disable_gdpr()
logger.set_gdpr_policy(policy)
policy = logger.get_gdpr_policy()

# Logger identity
logger.set_core_name("NewAppName")
```

#### Log Retrieval

```python
# Get all logs
logs = logger.get_logs()

# Filter by level
error_logs = logger.get_logs(level=LogLevel.ERROR)

# Limit results
recent_logs = logger.get_logs(limit=100)

# Time-based filtering
from datetime import datetime, timedelta
since = datetime.now() - timedelta(hours=1)
logs = logger.get_logs(since=since)

# Get logs by core name
logs = logger.get_logs_by_core("MyApp")

# Clear all logs
count = logger.clear_logs()
```

#### Export Functions

```python
# Export to different formats
logger.export_logs_json('logs.json')
logger.export_logs_csv('logs.csv')
logger.export_logs_txt('logs.txt')

# Generic export with format parameter
logger.export_logs('output.json', format_type='json')
logger.export_logs('output.csv', format_type='csv')
logger.export_logs('output.txt', format_type='txt')
```

#### Lifecycle Management

```python
# Graceful shutdown (sync)
logger.shutdown()

# Async shutdown
await logger.shutdown_async()

# Context manager support
with Nogger(core="App") as logger:
    logger.info("Inside context")
# Automatically shut down

# Async context manager
async with Nogger(core="App") as logger:
    await logger.info_async("Async context")
# Automatically shut down
```

#### Statistics and Information

```python
# Get comprehensive statistics
stats = logger.get_statistics()
print(stats['total_logs'])
print(stats['level_counts'])
print(stats['gdpr_enabled'])
print(stats['logging_mode'])

# String representation
print(logger)  # Nogger(core='MyApp', mode=console, logs=150, colours=True)
```

## Advanced Usage

### Custom Message Formatting

```python
logger = Nogger(core="App")

# Custom format per message
logger.info("Custom", format=">>> {level}: {message}")

# Global format change
logger.set_format("[{timestamp}] {core} | {level}: {message}{extra}")

# Available placeholders:
# {timestamp} - Formatted timestamp
# {level} - Log level name
# {core} - Logger core name
# {message} - Log message
# {extra} - Formatted extra_data
# {thread} - Thread ID (if enabled)
# {task} - Async task ID (if enabled)
```

### Thread-Safe Logging

```python
import threading

logger = Nogger(core="MultiThread", include_thread_info=True)

def worker(n):
    logger.info(f"Worker {n} started")
    # Do work...
    logger.info(f"Worker {n} finished")

threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

### Batch Processing

```python
logger = Nogger(
    output_behaviour=OutputBehaviour.BATCHED,
    batch_size=1000,
    batch_timeout=10.0
)

# Efficiently process large volumes
for i in range(10000):
    logger.info(f"Processing record {i}")

# Force flush remaining
logger.flush_batches()
```

### Complex Extra Data

```python
logger.info("User profile update", extra_data={
    "user": {
        "id": 12345,
        "email": "user@example.com",
        "permissions": ["read", "write", "admin"]
    },
    "changes": {
        "field": "email",
        "old": "old@example.com",
        "new": "user@example.com"
    },
    "metadata": {
        "timestamp": "2024-11-23T15:30:00Z",
        "ip": "192.168.1.1",
        "user_agent": "Mozilla/5.0..."
    }
})

# With GDPR enabled, nested sensitive data is sanitized
```

## Configuration Reference

### LogLevel Enum
- `LogLevel.DEBUG` - Detailed debugging information
- `LogLevel.INFO` - General informational messages
- `LogLevel.WARNING` - Warning messages  
- `LogLevel.ERROR` - Error messages
- `LogLevel.CRITICAL` - Critical failure messages

### LoggingMode Enum
- `LoggingMode.CONSOLE` - Output to console/terminal
- `LoggingMode.FILE_JSON` - Write structured JSON to file
- `LoggingMode.FILE_CSV` - Write CSV format to file
- `LoggingMode.FILE_TXT` - Write plain text to file
- `LoggingMode.MEMORY_ONLY` - Store in memory only
- `LoggingMode.CUSTOM` - Custom output handling

### OutputBehaviour Enum
- `OutputBehaviour.STREAMED` - Immediate synchronous output
- `OutputBehaviour.BATCHED` - Batched synchronous output
- `OutputBehaviour.ASYNC_STREAMED` - Immediate asynchronous output
- `OutputBehaviour.ASYNC_BATCHED` - Batched asynchronous output

### ColourScheme Enum
- `ColourScheme.DEFAULT` - Balanced default colours
- `ColourScheme.VIBRANT` - High-contrast bright colours
- `ColourScheme.MINIMAL` - Subtle professional colours
- `ColourScheme.DARK_THEME` - Optimised for dark backgrounds
- `ColourScheme.LIGHT_THEME` - Optimised for light backgrounds
- `ColourScheme.MONOCHROME` - No colours, bold/dim only

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
python test.py

# Run GDPR-specific tests
python test_gdpr.py
```

### Test Coverage

The test suite includes:
- ✅ Basic logging functionality with British English
- ✅ Multiple colour schemes (6 variants)
- ✅ Different logging modes (Console, File, Memory)
- ✅ Output behaviours (Streamed, Batched, Async)
- ✅ YAML configuration loading
- ✅ Runtime configuration changes
- ✅ Thread-safe operations
- ✅ Async/await compatibility
- ✅ Export functionality (JSON, CSV, TXT)
- ✅ GDPR pattern detection
- ✅ GDPR field sanitization
- ✅ Data retention policies
- ✅ Performance and reliability

## File Structure

```
nogger-python/
├── nogger_package/
│   ├── __init__.py           # Package exports
│   ├── nogger.py             # Main Nogger class
│   ├── _colours.py           # Colour management
│   ├── _config.py            # Configuration system
│   ├── _export.py            # Export functions
│   └── _gdpr.py              # GDPR compliance module
├── test.py                   # Main test suite
├── test_gdpr.py              # GDPR-specific tests
├── nogger_config.yaml        # Sample configuration
├── setup.py                  # Package setup
├── requirements.txt          # Dependencies
└── README.md                 # This file
```

## Example Output

```
2024-11-23 15:30:15 [INFO] MyApp: Application started
2024-11-23 15:30:15 [DEBUG] MyApp: Initialising database connection
2024-11-23 15:30:16 [INFO] MyApp: User login (user_id: a1b2c3d4e5f6g7h8 | ip: [IP_REDACTED])
2024-11-23 15:30:17 [WARNING] MyApp: Low memory detected (available: 512MB)
2024-11-23 15:30:18 [ERROR] MyApp: Database connection failed (timeout: 30s)
2024-11-23 15:30:19 [INFO] MyApp: Retrying connection attempt 2/3
```

Colours are automatically applied based on log levels when terminal support is available. With GDPR enabled, sensitive data is automatically sanitized.

## Performance Considerations

- **Streamed Mode**: ~0.01ms overhead per log (immediate output)
- **Batched Mode**: ~0.001ms per log (bulk processing)
- **Async Mode**: Non-blocking, ~0.005ms to queue
- **GDPR Pattern Scanning**: ~0.1-1ms depending on message length
- **Memory Usage**: ~1KB per log entry (configurable with `max_stored_logs`)

Recommendations:
- Use **batched mode** for high-volume logging (>1000 logs/second)
- Use **async mode** to avoid blocking your application
- Set `max_stored_logs` to limit memory usage
- Disable GDPR in development environments for better performance
- Use `scan_unstructured_fields=False` if you control all logged data

## Requirements

- **Python**: 3.8 or higher
- **Dependencies**: PyYAML >=6.0.1 (for configuration files)
- **Optional**: asyncio support (included in Python 3.8+)

## Contributing

Contributions are welcome! Please:
1. Maintain British English spelling throughout
2. Add tests for new features
3. Update documentation
4. Follow the existing code style

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or feature requests:
- Open an issue on GitHub
- Review test files for usage examples
- Check the [GDPR Compliance](#gdpr-compliance) section for privacy questions

## Changelog

### Version 1.0.0
- ✨ Initial release with comprehensive logging features
- ✨ **Unified async/sync API** - Same methods work everywhere
- ✨ Full GDPR compliance module
- ✨ 6 colour schemes
- ✨ YAML configuration support
- ✨ Async/await support throughout
- ✨ Modular architecture (colours, config, export, GDPR)
- ✨ Comprehensive test suite
- ✨ British English throughout
- ✨ Zero dependencies (except PyYAML)

## Unified API Deep Dive

### Overview

Nogger features a **unified API** that eliminates the need for separate `_async` methods. The same logging methods work seamlessly in both synchronous and asynchronous contexts.

### Detection Logic

The logger uses two simple checks:

1. **Config Check**: Is `output_behaviour` set to async mode?
   - `OutputBehaviour.ASYNC_STREAMED`
   - `OutputBehaviour.ASYNC_BATCHED`

2. **Context Check**: Is the code running in an async event loop?
   - Uses `asyncio.current_task()` to detect

### Execution Behaviour Matrix

| Config Mode | Execution Context | Behaviour |
|-------------|-------------------|-----------|
| STREAMED | Sync | Execute immediately |
| STREAMED | Async | Execute immediately |
| ASYNC_STREAMED | Sync | Queue for async processing |
| ASYNC_STREAMED | Async | Queue + return awaitable |
| BATCHED | Any | Buffer and batch |
| ASYNC_BATCHED | Any | Buffer and async batch |

### Real-World Examples

#### Web Server (Async)

```python
from fastapi import FastAPI
from nogger_package import Nogger, OutputBehaviour

app = FastAPI()
logger = Nogger(
    core="WebAPI",
    output_behaviour=OutputBehaviour.ASYNC_STREAMED
)

@app.get("/api/data")
async def get_data():
    await logger.info("API request received")
    
    # Mix of sync and async logging
    logger.debug("Validating request")  # Fire-and-forget
    await logger.debug("Querying database")  # Ensured processing
    
    await logger.info("Request completed")
    return {"status": "ok"}
```

#### CLI Tool (Sync)

```python
from nogger_package import Nogger, OutputBehaviour

def process_files():
    logger = Nogger(
        core="CLITool",
        output_behaviour=OutputBehaviour.STREAMED
    )
    
    files = ["config.json", "data.csv", "output.txt"]
    for file in files:
        logger.info(f"Processing {file}")
        # Processing logic
        logger.info(f"Completed {file}")
```

#### Mixed Async/Sync Pipeline

```python
async def data_pipeline():
    logger = Nogger(
        core="Pipeline",
        output_behaviour=OutputBehaviour.ASYNC_STREAMED
    )
    
    # Async operations
    await logger.info("Fetching data from API")
    data = await fetch_data()
    
    # Sync operations (no await needed!)
    logger.info("Processing data synchronously")
    process_data(data)  # Sync function
    logger.info("Processing complete")
    
    # Back to async
    await logger.info("Saving results")
    await save_data()
    
    await logger.shutdown_async()
```

### Migration from Old API

**Before (if you used the old `_async` methods):**
```python
# Async code
await logger.info_async("Message")
await logger.debug_async("Debug info")
```

**After (unified API):**
```python
# Async code - cleaner!
await logger.info("Message")
await logger.debug("Debug info")

# Or fire-and-forget
logger.info("Message")  # Still works, queued automatically
```

### Best Practices

#### ✓ DO

```python
# Use appropriate output behaviour for your use case
logger = Nogger(output_behaviour=OutputBehaviour.STREAMED)  # CLI tools
logger = Nogger(output_behaviour=OutputBehaviour.ASYNC_STREAMED)  # Web servers

# Await in async contexts when you want backpressure
await logger.error("Critical operation failed")

# Use fire-and-forget for high-throughput logging
logger.debug("High-frequency metric")  # No await needed
```

#### ✗ DON'T

```python
# Don't mix output behaviours unnecessarily
# Choose once at initialization based on your app type

# Don't create multiple loggers with different modes
# Use a single logger instance per application/service
```

### Performance

| Operation | Overhead | Notes |
|-----------|----------|-------|
| Sync logging | ~2μs | Direct execution |
| Async logging | ~5μs | Includes queueing |
| Context detection | ~1μs | Minimal overhead |

---

**Made with 🇬🇧 and proper spelling**