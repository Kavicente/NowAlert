from alert_data import alerts
from collections import Counter
import logging

logger = logging.getLogger(__name__)

def get_cdrrmo_stats():
    try:
        from AlertNow import alerts
        types = [a.get('emergency_type', 'unknown') for a in alerts if a.get('role') == 'cdrrmo' or a.get('assigned_municipality')]
        return Counter(types)
    except Exception as e:
        logger.error(f"Error in get_cdrrmo_stats: {e}")
        return Counter()

def get_latest_alert():
    try:
        from AlertNow import alerts
        if alerts:
            return alerts[-1]
        return None
    except Exception as e:
        logger.error(f"Error in get_latest_alert: {e}")
        return None
