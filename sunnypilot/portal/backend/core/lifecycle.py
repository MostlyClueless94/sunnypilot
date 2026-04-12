#!/usr/bin/env python3
"""
SubiPilot Backend Lifecycle Management
Server lifecycle functions including crash tracking and dependency management
"""

import os
import sys
import time
import logging
import threading

logger = logging.getLogger(__name__)

# Global flags to track restart state
_restart_pending = False      # True when dependencies installed and restart needed
_restart_triggered = False    # True when restart has been initiated (prevents double-trigger)
_restart_lock = threading.Lock()


def record_crash(params):
    """
    Record a server crash for monitoring (but don't disable server)

    Args:
        params: Params instance for storing crash tracking data
    """
    try:
        current_time = int(time.monotonic())

        # Get crash count - handle both real and mock params
        try:
            crash_count_str = params.get("SubiPilotPortalCrashCount")
            crash_count = int(crash_count_str) if crash_count_str else 0
        except (AttributeError, TypeError):
            # Mock params or other error
            crash_count = 0

        # Get last crash time - handle both real and mock params
        try:
            last_crash_str = params.get("SubiPilotPortalLastCrash")
            last_crash = int(last_crash_str) if last_crash_str else 0
        except (AttributeError, TypeError):
            # Mock params or other error
            last_crash = 0

        # Check if this is a recent consecutive crash
        if current_time - last_crash <= 30:  # Within 30 seconds
            crash_count += 1
        else:
            # Reset crash count if more than 30 seconds have passed
            crash_count = 1

        # Update crash tracking parameters for monitoring only
        try:
            params.put("SubiPilotPortalCrashCount", min(crash_count, 10))  # Cap at 10
            params.put("SubiPilotPortalLastCrash", current_time)
        except AttributeError:
            # Mock params object doesn't have put methods, skip
            pass

        logger.warning(f"Server error occurred ({crash_count} recent errors) - continuing operation")

    except Exception as e:
        logger.error(f"Error recording crash: {e}")


def check_and_handle_crashes(params):
    """
    Check server status but never disable it automatically

    Args:
        params: Params instance for checking crash tracking data

    Returns:
        bool: Always returns True (server always allowed to start)
    """
    try:
        # Get crash count for monitoring only - don't disable server
        try:
            crash_count_str = params.get("SubiPilotPortalCrashCount")
            crash_count = int(crash_count_str) if crash_count_str else 0
        except (AttributeError, TypeError):
            crash_count = 0

        # Get last crash time for monitoring only
        try:
            last_crash_str = params.get("SubiPilotPortalLastCrash")
            last_crash = int(last_crash_str) if last_crash_str else 0
        except (AttributeError, TypeError):
            last_crash = 0

        current_time = int(time.monotonic())

        # Log crash statistics for monitoring but don't disable server
        if crash_count > 0:
            logger.info(f"Server has experienced {crash_count} errors recently - continuing operation")

        # Reset crash count if server has been running stably for 10 minutes
        if crash_count > 0 and current_time - last_crash > 600:  # 10 minutes
            logger.info("Server running stably for 10 minutes, resetting error count")
            try:
                params.put("SubiPilotPortalCrashCount", 0)
                params.put("SubiPilotPortalLastCrash", 0)
            except AttributeError:
                # Mock params object doesn't have put methods, skip
                pass

        return True  # Always allow server to start

    except Exception as e:
        logger.error(f"Error checking crash status: {e}")
        return True  # Default to allowing server start


def check_dependencies():
    """
    Check if all required dependencies are available (without installing).

    Returns:
        bool: True if all dependencies are available, False if some are missing
    """
    try:
        import websockets  # noqa: F401
        return True
    except ImportError:
        return False
    except Exception as e:
        # Handle any other import errors (corrupted package, etc.)
        logger.warning(f"Unexpected error checking websockets dependency: {e}")
        return False


def is_restart_pending():
    """Check if a restart is pending due to dependency installation."""
    global _restart_pending
    with _restart_lock:
        return _restart_pending


def trigger_restart():
    """
    Trigger a server restart by re-executing the current process.

    This function should only be called when is_restart_pending() returns True.
    It includes protection against being called multiple times.
    """
    global _restart_pending, _restart_triggered

    with _restart_lock:
        # Check if restart has already been triggered (prevents double-trigger)
        if _restart_triggered:
            logger.info("Restart already triggered, skipping duplicate call")
            return

        # Check if restart is actually needed
        if not _restart_pending:
            logger.warning("trigger_restart called but no restart is pending")
            return

        # Mark restart as triggered to prevent concurrent calls
        _restart_triggered = True

    logger.info("Triggering server restart to load newly installed packages...")
    logger.info("Waiting 2 seconds before restart...")
    time.sleep(2)

    # Re-execute the current process
    logger.info("Restarting server process...")
    try:
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        # If execv fails, reset the triggered flag so it can be retried
        logger.error(f"Failed to restart server: {e}")
        with _restart_lock:
            _restart_triggered = False
        raise


def install_dependencies_background(on_complete_callback=None):
    """
    Compatibility shim for the imported portal.

    SubiPilot declares portal dependencies in pyproject.toml. The device should not
    mutate its Python environment from the portal process at runtime.
    """
    logger.info("Dependency auto-install disabled; HTTP polling remains available if websockets is missing")
    if on_complete_callback:
        on_complete_callback(False)
    return None


def ensure_dependencies():
    """
    Check if all required dependencies are available.

    Deprecated compatibility shim; SubiPilot does not install Python packages at runtime.

    Returns:
        bool: Always False because this function never schedules a restart.
    """
    try:
        import websockets  # noqa: F401
    except Exception as e:
        logger.warning(f"websockets unavailable; HTTP polling will be used: {e}")
    return False
