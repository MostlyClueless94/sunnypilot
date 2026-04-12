#!/usr/bin/env python3
"""
SubiPilot Logs Module

Log extraction and Cereal message processing for SubiPilot backend.
Handles parsing, filtering, and serialization of log files.
"""

from sunnypilot.portal.backend.logs.extraction import extract_log_messages
from sunnypilot.portal.backend.logs.cereal import extract_cereal_messages, serialize_cereal_object
from sunnypilot.portal.backend.logs.manager_logs import (
    parse_manager_log_line,
    read_recent_manager_logs,
)

__all__ = [
    'extract_log_messages',
    'extract_cereal_messages',
    'serialize_cereal_object',
    'parse_manager_log_line',
    'read_recent_manager_logs',
]
