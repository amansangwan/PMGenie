from datetime import datetime

def get_current_date():
    """
    Returns the current date in ISO format (YYYY-MM-DD).
    """
    return datetime.now().date().isoformat()
