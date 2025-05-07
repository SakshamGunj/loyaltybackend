from datetime import datetime, timezone, timedelta

# Define IST timezone offset (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def utc_to_ist(utc_datetime):
    """Convert UTC datetime to IST datetime"""
    if utc_datetime is None:
        return None
    
    # If the datetime is naive (no timezone info), assume it's UTC
    if utc_datetime.tzinfo is None:
        utc_datetime = utc_datetime.replace(tzinfo=timezone.utc)
    
    # Convert to IST
    return utc_datetime.astimezone(IST)

def ist_now():
    """Get current time in IST"""
    return datetime.now(IST)

def ist_to_utc(ist_datetime):
    """Convert IST datetime to UTC datetime"""
    if ist_datetime is None:
        return None
    
    # If the datetime is naive (no timezone info), assume it's IST
    if ist_datetime.tzinfo is None:
        ist_datetime = ist_datetime.replace(tzinfo=IST)
    
    # Convert to UTC
    return ist_datetime.astimezone(timezone.utc) 