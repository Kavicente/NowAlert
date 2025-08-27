from alert_data import alerts
from collections import Counter
import logging

logger = logging.getLogger(__name__)

def get_pnp_stats():
    try:
        from AlertNow import alerts
        types = [a.get('emergency_type', 'unknown') for a in alerts if a.get('role') == 'pnp' or a.get('assigned_municipality')]
        return Counter(types)
    except Exception as e:
        logger.error(f"Error in get_pnp_stats: {e}")
        return Counter()

def get_latest_alert(alerts_list=None, municipality=None):
    try:
        if alerts_list is None:
            try:
                from AlertNow import alerts as alerts_list
            except Exception:
                alerts_list = []
        if alerts_list:
            return alerts_list[-1]
        return None
    except Exception as e:
        logger.error(f"Error in get_latest_alert: {e}")
        return None
