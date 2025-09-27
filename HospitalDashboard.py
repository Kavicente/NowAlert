from collections import Counter
import sqlite3
import os
import logging

logger = logging.getLogger(__name__)

def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'users_web.db')
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return None

def get_hospital_stats(municipality):
    try:
        conn = get_db_connection()
        if conn is None:
            return Counter()
        c = conn.cursor()
        c.execute('''
            SELECT health_emergency_type
            FROM hospital_response
            WHERE barangay = ? AND responded = 1
        ''', (municipality,))
        health_types = [row['health_emergency_type'] for row in c.fetchall()]
        conn.close()
        return Counter(health_types)
    except Exception as e:
        logger.error(f"Error fetching hospital stats: {e}")
        return Counter()

def get_latest_alert(municipality):
    try:
        conn = get_db_connection()
        if conn is None:
            return {'lat': None, 'lon': None}
        c = conn.cursor()
        c.execute('''
            SELECT lat, lon
            FROM hospital_response
            WHERE barangay = ? AND responded = 1
            ORDER BY timestamp DESC
            LIMIT 1
        ''', (municipality,))
        row = c.fetchone()
        conn.close()
        if row:
            return {'lat': row['lat'], 'lon': row['lon']}
        return {'lat': None, 'lon': None}
    except Exception as e:
        logger.error(f"Error fetching latest hospital alert: {e}")
        return {'lat': None, 'lon': None}