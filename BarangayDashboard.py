from alert_data import alerts
from collections import Counter
import logging

logger = logging.getLogger(__name__)

def get_barangay_stats(alerts_list=None, barangay=None):
    """
    Return Counter of emergency types for the specified barangay (if provided).
    If alerts_list is None, attempt to import from AlertNow (best-effort; may fail in some contexts).
    """
    try:
        if alerts_list is None:
            # try to import in a safe way
            try:
                from AlertNow import alerts as alerts_list  # may exist when running with the server
            except Exception:
                alerts_list = []
        filtered = alerts_list
        if barangay:
            filtered = [a for a in alerts_list if (a.get('barangay') or '').strip().lower() == barangay.strip().lower()]
        types = [a.get('emergency_type', 'unknown') for a in filtered]
        return Counter(types)
    except Exception as e:
        logger.error(f"Error in get_barangay_stats: {e}")
        return Counter()

def get_latest_alert(alerts_list=None):
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
