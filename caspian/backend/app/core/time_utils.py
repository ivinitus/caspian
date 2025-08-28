import asyncio
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import logging
import socket
import struct
import os
import threading

logger = logging.getLogger("time_utils")

# Default timezone
DEFAULT_TIMEZONE = "Asia/Kolkata"

# NTP server configurations
NTP_SERVERS = [
    "time.google.com",
    "pool.ntp.org",
    "time.windows.com",
    "time.nist.gov"
]

# Store the time offset once calculated
_time_offset = None
_last_sync_time = 0
_sync_interval = 3600  # Resync every hour
_drift_rate = 0  # Estimated drift rate in seconds per hour
_sync_lock = asyncio.Lock()
_tz_cache = {}


def get_timezone():
    """Get the application's default timezone."""
    return DEFAULT_TIMEZONE


def get_timezone_object(timezone=None):
    """Get the ZoneInfo object for a timezone with caching for better performance."""
    tz_name = timezone or DEFAULT_TIMEZONE
    if tz_name not in _tz_cache:
        _tz_cache[tz_name] = ZoneInfo(tz_name)
    return _tz_cache[tz_name]


async def sync_time():
    """
    Synchronize system time with an NTP server.
    Updates the global _time_offset variable.
    Returns True if sync was successful, False otherwise.
    """
    global _time_offset, _last_sync_time, _drift_rate
    
    # Use a lock to prevent multiple concurrent sync attempts
    async with _sync_lock:
        # If we've synced recently, don't do it again unless forced
        current_time = time.time()
        if _time_offset is not None and current_time - _last_sync_time < _sync_interval:
            return True
        
        old_offset = _time_offset
        sync_success = False
        
        for server in NTP_SERVERS:
            try:
                logger.info(f"Attempting to sync time with {server}...")
                # NTP protocol operates on port 123
                client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                client.settimeout(5.0)
                
                # NTP request format (48 bytes)
                # LI, VN, Mode, Stratum, Poll, Precision, Root Delay, Root Dispersion, Reference ID, Reference Timestamp, 
                # Originate Timestamp, Receive Timestamp, Transmit Timestamp
                ntp_request = b'\x1b' + 47 * b'\0'
                
                addr = socket.gethostbyname(server)
                client.sendto(ntp_request, (addr, 123))
                
                # NTP response format
                ntp_response, _ = client.recvfrom(1024)
                
                # Close the socket
                client.close()
                
                # Extract the transmit timestamp (bytes 40-48)
                transmit_time = struct.unpack('!12I', ntp_response)[10]
                # Convert to UNIX timestamp (seconds since Jan 1, 1900 to Jan 1, 1970)
                ntp_time = transmit_time - 2208988800
                
                # Calculate offset
                system_time = time.time()
                new_offset = ntp_time - system_time
                
                # Calculate drift rate if we had a previous offset
                if old_offset is not None and _last_sync_time > 0:
                    time_elapsed = (current_time - _last_sync_time) / 3600  # In hours
                    if time_elapsed > 0:
                        drift = new_offset - old_offset
                        _drift_rate = drift / time_elapsed
                        logger.info(f"Clock drift rate: {_drift_rate:.6f} seconds per hour")
                
                _time_offset = new_offset
                _last_sync_time = current_time
                
                logger.info(f"Time synchronized with {server}. Offset: {_time_offset:.3f} seconds")
                sync_success = True
                break
            except Exception as e:
                logger.warning(f"Failed to sync time with {server}: {str(e)}")
        
        if not sync_success:
            # If all servers fail, log it but don't crash
            logger.error("Failed to synchronize time with any NTP server.")
            return False
        
        return True


def get_current_time(timezone=None):
    """
    Get the current time, adjusted for NTP offset if available.
    Returns an aware datetime object in the specified timezone or default timezone.
    Accounts for estimated drift since last sync.
    """
    # Use NTP offset if available
    if _time_offset is not None:
        # Calculate additional drift since last sync
        hours_since_sync = max(0, (time.time() - _last_sync_time) / 3600)
        drift_adjustment = _drift_rate * hours_since_sync
        
        # Apply the offset and drift adjustment
        current_time = time.time() + _time_offset + drift_adjustment
        # Use fromtimestamp to create a datetime
        dt = datetime.fromtimestamp(current_time)
    else:
        dt = datetime.now()
    
    # Make timezone aware
    tz = ZoneInfo(timezone) if timezone else get_timezone_object()
    return dt.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)
    
    # Make timezone aware
    tz = ZoneInfo(timezone) if timezone else get_timezone_object()
    return dt.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)


def get_current_time_utc():
    """Get the current time in UTC, adjusted for NTP offset if available."""
    return get_current_time(timezone="UTC")


def format_time(dt, include_timezone=True):
    """Format a datetime object for display."""
    formatted = dt.strftime('%I:%M %p on %A, %B %d, %Y')
    if include_timezone:
        formatted += f" {dt.tzname()}"
    return formatted


def parse_time(time_str, default_time=None, timezone=None):
    """
    Parse a time string into a datetime object.
    If default_time is provided and time_str doesn't contain a date, 
    use default_time's date. Handles ambiguous date references intelligently.
    """
    from dateutil import parser
    import re
    
    try:
        # Get default time if not provided
        if default_time is None:
            default_time = get_current_time(timezone)
        
        # Check for special time references
        time_str_lower = time_str.lower()
        
        # Handle relative time durations (in X seconds/minutes/hours/days)
        seconds_match = re.search(r'in\s+(\d+)\s+seconds?', time_str_lower)
        minutes_match = re.search(r'in\s+(\d+)\s+minutes?', time_str_lower)
        hours_match = re.search(r'in\s+(\d+)\s+hours?', time_str_lower)
        days_match = re.search(r'in\s+(\d+)\s+days?', time_str_lower)
        
        if seconds_match:
            # Handle "in X seconds"
            seconds = int(seconds_match.group(1))
            result_time = default_time + timedelta(seconds=seconds)
            return result_time
        elif minutes_match:
            # Handle "in X minutes"
            minutes = int(minutes_match.group(1))
            return default_time + timedelta(minutes=minutes)
        elif hours_match:
            # Handle "in X hours"
            hours = int(hours_match.group(1))
            return default_time + timedelta(hours=hours)
        elif days_match:
            # Handle "in X days"
            days = int(days_match.group(1))
            return default_time + timedelta(days=days)
        
        # Handle "midnight" reference - common source of confusion
        if "midnight" in time_str_lower:
            # By convention, midnight refers to 00:00 of the next day
            # E.g., "midnight tonight" = 00:00 tomorrow
            if "tonight" in time_str_lower or "today" in time_str_lower:
                # Midnight tonight = 00:00 tomorrow
                date_part = (default_time + timedelta(days=1)).strftime('%Y-%m-%d')
                time_str = time_str.replace("midnight", "00:00")
                time_str = f"{date_part} {time_str}"
            elif "tomorrow" in time_str_lower:
                # Midnight tomorrow = 00:00 day after tomorrow
                date_part = (default_time + timedelta(days=2)).strftime('%Y-%m-%d')
                time_str = time_str.replace("midnight", "00:00")
                time_str = f"{date_part} {time_str}"
        
        # Parse the time string
        dt = parser.parse(time_str)
        # Ensure both dt and default_time are timezone-aware for comparison
        tz = ZoneInfo(timezone) if timezone else get_timezone_object()
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=tz)
        if default_time.tzinfo is None:
            default_time = default_time.replace(tzinfo=tz)
        # If parsed date is in the past but no specific date was mentioned,
        # use date disambiguation to determine the likely intended date
        if dt < default_time and not any(x in time_str_lower for x in 
                                        ["-", "/", "january", "february", "march", "april", "may", "june", 
                                         "july", "august", "september", "october", "november", "december",
                                         "tomorrow", "next"]):
            
            # Check if only a time was specified (no date)
            # Pattern to detect if there's a date part in the string
            date_pattern = r'\d{1,4}[-/]\d{1,2}([-/]\d{1,4})?'
            has_date_format = bool(re.search(date_pattern, time_str_lower))
            
            # Pattern to detect weekday mentions
            weekday_pattern = r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b'
            has_weekday = bool(re.search(weekday_pattern, time_str_lower))
            
            if not has_date_format and not has_weekday:
                # Only time was specified, no date
                
                # Case 1: If it's just a time of day (e.g. "3pm") and current time is past that,
                # assume they mean tomorrow
                if dt.date() == default_time.date() and dt.time() < default_time.time():
                    dt = dt.replace(year=default_time.year, month=default_time.month, day=default_time.day + 1)
                else:
                    # Default to today's date
                    dt = dt.replace(year=default_time.year, month=default_time.month, day=default_time.day)
            elif has_weekday and not has_date_format:
                # Weekday was mentioned but currently parsed date is in past
                # Add a week to move to next occurrence
                if dt < default_time:
                    dt += timedelta(days=7)
        
        # Handle explicit date references
        elif "tomorrow" in time_str_lower:
            tomorrow = default_time + timedelta(days=1)
            dt = dt.replace(year=tomorrow.year, month=tomorrow.month, day=tomorrow.day)
        elif "today" in time_str_lower:
            dt = dt.replace(year=default_time.year, month=default_time.month, day=default_time.day)
        
        # Make timezone aware
        tz = ZoneInfo(timezone) if timezone else get_timezone_object()
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=tz)
        else:
            dt = dt.astimezone(tz)
        
        # Final check - if still in the past and no explicit past reference, bump to future
        if dt < default_time and not any(x in time_str_lower for x in ["last", "previous", "ago"]):
            # If just the time was specified (same date), move to tomorrow
            if dt.date() == default_time.date():
                dt += timedelta(days=1)
            # If it's a specific day of month but in the past, try next month
            elif dt.day == default_time.day and dt.month < default_time.month:
                from dateutil.relativedelta import relativedelta
                dt += relativedelta(months=1)
        
        return dt
    except Exception as e:
        logger.error(f"Error parsing time string '{time_str}': {e}")
        raise


def convert_to_utc(dt):
    """
    Convert a datetime object to UTC timezone.
    Returns a timezone-aware datetime in UTC.
    """
    if dt.tzinfo is None:
        # If the datetime has no timezone, assume it's in the default timezone
        dt = dt.replace(tzinfo=get_timezone_object())
    
    # Convert to UTC
    return dt.astimezone(ZoneInfo("UTC"))


def convert_to_naive_utc(dt):
    """
    Convert a datetime object to UTC and strip timezone information.
    Returns a naive datetime in UTC, suitable for database storage.
    """
    # First convert to UTC timezone
    utc_dt = convert_to_utc(dt)
    
    # Then remove timezone info
    return utc_dt.replace(tzinfo=None)


def is_time_synced():
    """Check if the time has been synchronized with an NTP server."""
    return _time_offset is not None


def get_time_offset():
    """Get the current time offset in seconds."""
    if _time_offset is None:
        return 0
    
    # Calculate additional drift since last sync
    hours_since_sync = (time.time() - _last_sync_time) / 3600
    drift_adjustment = _drift_rate * hours_since_sync
    
    return _time_offset + drift_adjustment


def get_time_drift_rate():
    """Get the estimated drift rate in seconds per hour."""
    return _drift_rate


async def force_time_sync():
    """Force a time synchronization regardless of when the last sync occurred."""
    global _sync_interval, _last_sync_time
    
    # Reset the last sync time to force a new sync
    _last_sync_time = 0
    return await sync_time()


async def start_time_sync_task():
    """Start a background task to periodically sync time."""
    # Do an initial sync immediately
    initial_sync_attempts = 0
    max_initial_attempts = 5
    
    # Try initial sync multiple times if needed
    while initial_sync_attempts < max_initial_attempts:
        try:
            success = await sync_time()
            if success:
                logger.info("Initial time synchronization successful")
                break
            else:
                logger.warning(f"Initial time synchronization failed (attempt {initial_sync_attempts+1}/{max_initial_attempts}), retrying...")
        except Exception as e:
            logger.error(f"Error in initial time sync: {str(e)}")
        
        initial_sync_attempts += 1
        if initial_sync_attempts < max_initial_attempts:
            await asyncio.sleep(5)  # Short delay between initial attempts
    
    if initial_sync_attempts >= max_initial_attempts and _time_offset is None:
        logger.error(f"Failed to complete initial time sync after {max_initial_attempts} attempts")
        
    # Then continue periodic syncing
    consecutive_failures = 0
    while True:
        try:
            # Wait for the sync interval (shorter interval after failures)
            if consecutive_failures > 0:
                backoff = min(consecutive_failures * 60, 300)  # Up to 5 minutes
                wait_time = min(_sync_interval, backoff)
            else:
                wait_time = _sync_interval
                
            await asyncio.sleep(wait_time)
            
            # Try to sync time
            success = await sync_time()
            if success:
                consecutive_failures = 0
                logger.info(f"Time sync successful. Next sync in {_sync_interval} seconds.")
            else:
                consecutive_failures += 1
                logger.warning(f"Time sync failed. Consecutive failures: {consecutive_failures}")
        except Exception as e:
            consecutive_failures += 1
            logger.error(f"Error in time sync task: {str(e)}")
            # Wait a shorter time before retrying on error
            await asyncio.sleep(60)
