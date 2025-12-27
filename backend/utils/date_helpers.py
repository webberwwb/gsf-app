"""
Date/Time helper utilities for EST timezone handling
All dates are normalized to EST timezone with proper start/end times
"""
from datetime import datetime, time
from zoneinfo import ZoneInfo

# EST timezone
EST = ZoneInfo('America/New_York')


def normalize_date_start(date_input):
    """
    Normalize a date to 00:00:00 EST
    
    Args:
        date_input: datetime, date, or date string (YYYY-MM-DD or ISO format)
    
    Returns:
        Naive datetime at 00:00:00 EST
    """
    if isinstance(date_input, str):
        # Check if it's a simple date string (YYYY-MM-DD)
        if len(date_input) == 10 and 'T' not in date_input:
            # Parse as date only and create EST datetime at midnight
            dt = datetime.strptime(date_input, '%Y-%m-%d')
            dt = dt.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=EST)
        else:
            # Parse ISO string with time/timezone
            dt = datetime.fromisoformat(date_input.replace('Z', '+00:00'))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=EST)
            # Convert to EST
            dt = dt.astimezone(EST)
            # Set to midnight
            dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    elif isinstance(date_input, datetime):
        dt = date_input
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=EST)
        else:
            dt = dt.astimezone(EST)
        dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        # date object
        dt = datetime.combine(date_input, time.min, tzinfo=EST)
    
    # Return as naive datetime (for MySQL)
    return dt.replace(tzinfo=None)


def normalize_date_end(date_input):
    """
    Normalize a date to 23:59:59 EST
    
    Args:
        date_input: datetime, date, or date string (YYYY-MM-DD or ISO format)
    
    Returns:
        Naive datetime at 23:59:59 EST
    """
    if isinstance(date_input, str):
        # Check if it's a simple date string (YYYY-MM-DD)
        if len(date_input) == 10 and 'T' not in date_input:
            # Parse as date only and create EST datetime at end of day
            dt = datetime.strptime(date_input, '%Y-%m-%d')
            dt = dt.replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=EST)
        else:
            # Parse ISO string with time/timezone
            dt = datetime.fromisoformat(date_input.replace('Z', '+00:00'))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=EST)
            else:
                dt = dt.astimezone(EST)
            # Set to end of day
            dt = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif isinstance(date_input, datetime):
        dt = date_input
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=EST)
        else:
            dt = dt.astimezone(EST)
        dt = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
    else:
        # date object
        dt = datetime.combine(date_input, time.max, tzinfo=EST)
    
    # Return as naive datetime (for MySQL)
    return dt.replace(tzinfo=None)


def format_date_only(dt):
    """
    Format datetime as date string only (YYYY-MM-DD)
    
    Args:
        dt: datetime object
    
    Returns:
        String in format YYYY-MM-DD
    """
    if dt is None:
        return None
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
    return dt.strftime('%Y-%m-%d')


def parse_date_string(date_str):
    """
    Parse a date string (YYYY-MM-DD) to datetime
    
    Args:
        date_str: String in format YYYY-MM-DD
    
    Returns:
        datetime object
    """
    if not date_str:
        return None
    return datetime.strptime(date_str, '%Y-%m-%d')

