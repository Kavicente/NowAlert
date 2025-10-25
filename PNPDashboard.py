from alert_data import alerts
from collections import Counter

import logging
import sqlite3
import os


logger = logging.getLogger(__name__)

def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'users_web.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_pnp_stats():
    try:
        types = [a.get('emergency_type', 'unknown') for a in alerts if a.get('role') == 'pnp' or a.get('municipality')]
        return Counter(types)
    except Exception as e:
        logger.error(f"Error in get_pnp_stats: {e}")
        return Counter()

def get_latest_alert():
    try:
        if alerts:
            return alerts[-1]
        return None
    except Exception as e:
        logger.error(f"Error in get_latest_alert: {e}")
        return None
    
def get_the_pnp_stats(barangay):
    try:
        conn = get_db_connection()
        # Check if 'municipality' column exists in any of the tables
        cursor = conn.execute("PRAGMA table_info(pnp_response)")
        columns = [col['name'] for col in cursor.fetchall()]
        location_column = 'municipality' if 'municipality' in columns else 'barangay'
        
        cursor = conn.execute(f'''
            SELECT COUNT(*) as total 
            FROM (
                SELECT {location_column} FROM pnp_response WHERE {location_column} = ? OR {location_column} IS NULL
                UNION ALL
                SELECT {location_column} FROM pnp_crime_response WHERE {location_column} = ? OR {location_column} IS NULL
                UNION ALL
                SELECT {location_column} FROM pnp_fire_response WHERE {location_column} = ? OR {location_column} IS NULL
            ) AS combined
        ''', (barangay, barangay, barangay))
        total = cursor.fetchone()['total']
        conn.close()
        return type('Stats', (), {'total': lambda self: total})()
    except Exception as e:
        logger.error(f"Error fetching PNP stats for {barangay}: {e}")
        return type('Stats', (), {'total': lambda self: 0})()

def get_pnp_new_alert(municipality):
    try:
        conn = get_db_connection()
        # Check if 'municipality' column exists
        cursor = conn.execute("PRAGMA table_info(pnp_response)")
        columns = [col['name'] for col in cursor.fetchall()]
        location_column = 'municipality' if 'municipality' in columns else 'barangay'
        
        cursor = conn.execute(f'''
            SELECT * FROM (
                SELECT alert_id, {location_column}, emergency_type, timestamp 
                FROM pnp_response WHERE {location_column} = ? OR {location_column} IS NULL
                UNION ALL
                SELECT alert_id, {location_column}, emergency_type, timestamp 
                FROM pnp_crime_response WHERE {location_column} = ? OR {location_column} IS NULL
                UNION ALL
                SELECT alert_id, {location_column}, emergency_type, timestamp 
                FROM pnp_fire_response WHERE {location_column} = ? OR {location_column} IS NULL
            ) AS combined
            ORDER BY timestamp DESC LIMIT 1
        ''', (municipality, municipality, municipality))
        alert = cursor.fetchone()
        conn.close()
        return dict(alert) if alert else None
    except Exception as e:
        logger.error(f"Error fetching latest alert for {municipality}: {e}")
        return None

def get_pnp_emergency_types(barangay=None):
    if not barangay:
        logger.warning("No barangay provided for emergency types")
        return {'Road Accident': 0, 'Crime Incident': 0, 'Fire Incident': 0, 'Health Emergency': 0}
    try:
        conn = get_db_connection()
        cursor = conn.execute('''
            SELECT emergency_type, COUNT(*) as count 
            FROM (
                SELECT emergency_type FROM pnp_response WHERE resident_barangay = ?
                UNION ALL
                SELECT emergency_type FROM pnp_crime_response WHERE resident_barangay = ?
                UNION ALL
                SELECT emergency_type FROM pnp_fire_response WHERE resident_barangay = ?
            ) AS combined
            GROUP BY emergency_type
        ''', (barangay, barangay, barangay))
        emergency_types = {'Road Accident': 0, 'Crime Incident': 0, 'Fire Incident': 0}
        for row in cursor:
            if row['emergency_type'] in emergency_types:
                emergency_types[row['emergency_type']] = row['count']
        conn.close()
        return emergency_types
    except Exception as e:
        logger.error(f"Error fetching emergency types for {barangay}: {e}")
        return {'Road Accident': 0, 'Crime Incident': 0, 'Fire Incident': 0}

def get_pnp_responded_count(municipality):
    try:
        conn = get_db_connection()
        # Check if 'municipality' column exists
        cursor = conn.execute("PRAGMA table_info(pnp_response)")
        columns = [col['name'] for col in cursor.fetchall()]
        location_column = 'municipality' if 'municipality' in columns else 'barangay'
        
        cursor = conn.execute(f'''
            SELECT COUNT(*) as count 
            FROM pnp_response 
            WHERE ({location_column} = ? OR {location_column} IS NULL) AND responded = TRUE
        ''', (municipality,))
        count = cursor.fetchone()['count']
        conn.close()
        return count
    except Exception as e:
        logger.error(f"Error fetching responded count for {municipality}: {e}")
        return 0

def emit_pnp_emergency_types_update(socketio, municipality):
    if not municipality:
        logger.error("No municipality provided for emitting emergency types update")
        return
    emergency_types = get_pnp_emergency_types(municipality)
    socketio.emit('update_pnp_emergency_types', emergency_types, room=f"pnp_{municipality.lower()}")
    
def get_heatmap_data(municipality):
    db_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'users_web.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT lat, lon FROM pnp_response WHERE municipality = ?', (municipality,))
    data = cursor.fetchall()
    conn.close()
    return [{'lat': row[0], 'lon': row[1]} for row in data]

# Add this near the existing socketio event definitions (e.g., after @socketio.on('alert'))
