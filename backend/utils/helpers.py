from datetime import date, datetime, timezone

def normalize_string(txt: str) -> str:
    return txt.strip().lower()

def convert_unix_to_date(unix_timestamp: int) -> date:
    return datetime.fromtimestamp(unix_timestamp, tz=timezone.utc).date()