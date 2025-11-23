"""
Export functionality for Nogger logging system.
Handles exporting logs to various formats (JSON, CSV, TXT).
"""

import json
import csv
from pathlib import Path
from typing import List, Union


def export_logs_json(logs: List, filename: Union[str, Path]) -> None:
    """
    Export logs to JSON format.
    
    Args:
        logs: List of LogEntry objects to export
        filename: Output filename
    """
    serialisable_logs = [log.to_dict() for log in logs]
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(serialisable_logs, f, indent=2, ensure_ascii=False)


def export_logs_csv(logs: List, filename: Union[str, Path]) -> None:
    """
    Export logs to CSV format.
    
    Args:
        logs: List of LogEntry objects to export
        filename: Output filename
    """
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'level', 'core', 'message', 'extra_data', 'thread_id', 'task_id'])
        
        for log in logs:
            writer.writerow([
                log.timestamp.isoformat(),
                log.level.value,
                log.core,
                log.message,
                json.dumps(log.extra_data) if log.extra_data else '',
                log.thread_id or '',
                log.task_id or ''
            ])


def export_logs_txt(logs: List, filename: Union[str, Path], formatter_func) -> None:
    """
    Export logs to plain text format.
    
    Args:
        logs: List of LogEntry objects to export
        filename: Output filename
        formatter_func: Function to format log entries (receives log entry and colours=False)
    """
    with open(filename, 'w', encoding='utf-8') as f:
        for log in logs:
            # Use the formatter to maintain consistent output
            formatted = formatter_func(log, colours=False)
            f.write(formatted + '\n')


def export_logs(logs: List, filename: Union[str, Path], format_type: str, formatter_func=None) -> None:
    """
    Export logs to file in specified format.
    
    Args:
        logs: List of LogEntry objects to export
        filename: Output filename
        format_type: 'json', 'csv', or 'txt'
        formatter_func: Function to format log entries (required for 'txt' format)
    
    Raises:
        ValueError: If format_type is not supported
    """
    format_type = format_type.lower()
    
    if format_type == 'json':
        export_logs_json(logs, filename)
    elif format_type == 'csv':
        export_logs_csv(logs, filename)
    elif format_type == 'txt':
        if formatter_func is None:
            raise ValueError("formatter_func is required for 'txt' format")
        export_logs_txt(logs, filename, formatter_func)
    else:
        raise ValueError(f"Unsupported format type: {format_type}. Use 'json', 'csv', or 'txt'.")
