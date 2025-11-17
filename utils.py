import random
import time
from datetime import datetime, timedelta
from typing import List
import re
import html

def rand_sleep(base: float = 1.0, jitter: float = 0.5):
    """Randomized sleep to help avoid detection."""
    t = base + random.random() * jitter
    time.sleep(t)

def now_utc():
    return datetime.utcnow()

def parse_hashtags(text: str) -> List[str]:
    return re.findall(r"#\w+", text)

def parse_mentions(text: str) -> List[str]:
    return re.findall(r"@\w+", text)

def clean_text(text: str) -> str:
    # Unescape HTML entities and normalize whitespace
    if text is None:
        return ""
    t = html.unescape(text)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def within_last_hours(dt, hours=24):
    if dt is None:
        return False
    return (now_utc() - dt) <= timedelta(hours=hours)
