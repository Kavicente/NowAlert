from alert_data import alerts
from collections import Counter
import logging
import sqlite3
import os

logger = logging.getLogger(__name__)
def get_hospital_stats():
    try:
        types = [a.get('emergency_type', 'unknown') for a in alerts if a.get('role') == 'health' or a.get('assigned_municipality')]
        return Counter(types)
    except Exception as e:
        logger.error(f"Error in get_health_stats: {e}")
        return Counter()

def get_latest_alert():
    if alerts:
        return list(alerts)[-1]
    return None