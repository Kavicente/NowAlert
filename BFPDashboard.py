from alert_data import alerts
from flask_socketio import sio
from collections import Counter
import logging
import sqlite3
import os

logger = logging.getLogger(__name__)

def get_bfp_stats():
    try:
        types = [a.get('emergency_type', 'unknown') for a in alerts if a.get('role') == 'bfp' or a.get('assigned_municipality')]
        return Counter(types)
    except Exception as e:
        logger.error(f"Error in get_bfp_stats: {e}")
        return Counter()

def get_latest_alert():
    try:
        if alerts:
            return alerts[-1]
        return None
    except Exception as e:
        logger.error(f"Error in get_latest_alert: {e}")
        return None
    
def get_heatmap_data(municipality):
    db_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'users_web.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT lat, lon FROM bfp_response WHERE municipality = ?', (municipality,))
    data = cursor.fetchall()
    conn.close()
    return [{'lat': row[0], 'lon': row[1]} for row in data]

@sio.event
def role_accepted(data):
    logger.info(f"Role {data['role']} accepted")
    if data['role'] == 'bfp':
        sio.on('forward_alert', lambda data: logger.info(f"Forwarded alert received: {data}") if data.get('emergency_type') == 'Fire Incident' else None)

@sio.event
def role_declined(data):
    logger.info(f"Role {data['role']} declined")
    if data['role'] == 'bfp':
        sio.off('forward_alert')