"""
Date/Time helper utilities for EST timezone handling
All dates are normalized to EST timezone, preserving time information when provided
"""
from datetime import datetime, time
from zoneinfo import ZoneInfo

# EST timezone
EST = ZoneInfo('America/New_York')


def normalize_date_start(date_input):
    """
    Normalize a date/datetime to EST timezone, preserving the time if provided
    
    Args:
        date_input: datetime, date, or date string (YYYY-MM-DD or ISO format)
    
    Returns:
        Naive datetime in EST timezone
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
                # Treat as EST if no timezone specified
                dt = dt.replace(tzinfo=EST)
            else:
                # Convert to EST
                dt = dt.astimezone(EST)
            # PRESERVE the time - don't override it
    elif isinstance(date_input, datetime):
        dt = date_input
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=EST)
        else:
            dt = dt.astimezone(EST)
        # PRESERVE the time - don't override it
    else:
        # date object (no time specified)
        dt = datetime.combine(date_input, time.min, tzinfo=EST)
    
    # Return as naive datetime (for MySQL)
    return dt.replace(tzinfo=None)


def normalize_date_end(date_input):
    """
    Normalize a date/datetime to EST timezone, preserving the time if provided
    
    Args:
        date_input: datetime, date, or date string (YYYY-MM-DD or ISO format)
    
    Returns:
        Naive datetime in EST timezone
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
                # Treat as EST if no timezone specified
                dt = dt.replace(tzinfo=EST)
            else:
                # Convert to EST
                dt = dt.astimezone(EST)
            # PRESERVE the time - don't override it
    elif isinstance(date_input, datetime):
        dt = date_input
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=EST)
        else:
            dt = dt.astimezone(EST)
        # PRESERVE the time - don't override it
    else:
        # date object (no time specified)
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

