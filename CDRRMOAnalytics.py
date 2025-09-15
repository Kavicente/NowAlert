import pandas as pd
import logging
from datetime import datetime, timedelta
from collections import Counter
import sqlite3
import os

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'users_web.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def load_response_data(time_filter, municipality, date=None, week_start=None):
    try:
        conn = get_db_connection()
        query = "SELECT * FROM cdrrmo_response WHERE barangay IN (SELECT barangay FROM users WHERE assigned_municipality = ?)"
        params = [municipality]
        
        if time_filter == 'today':
            query += " AND date(timestamp) = date('now')"
        elif time_filter == 'daily' and date:
            query += " AND date(timestamp) = ?"
            params.append(date)
        elif time_filter == 'weekly' and week_start:
            query += " AND date(timestamp) >= ? AND date(timestamp) < date(?, '+7 days')"
            params.extend([week_start, week_start])
        elif time_filter == 'monthly':
            query += " AND date(timestamp) >= date('now', '-30 days')"
        elif time_filter == 'yearly':
            query += " AND date(timestamp) >= date('now', '-1 year')"

        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except Exception as e:
        logger.error(f"Error in load_response_data: {e}")
        return pd.DataFrame()

def get_cdrrmo_analytics_data(responses, time_filter='today', municipality='', date=None, week_start=None):
    try:
        df = load_response_data(time_filter, municipality, date, week_start)
        if time_filter == 'weekly' and week_start:
            start = pd.to_datetime(week_start)
            dates = [(start + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
            summary = {
                'total_alerts': len(df),
                'total_responded': len(df[df['responded'] == True]),
                'most_common_barangay': Counter(df['barangay']).most_common(1)[0][0] if len(df) > 0 else 'N/A',
                'total_road_accidents': len(df[df['emergency_type'] == 'road_accident']),
                'most_common_accident_type': Counter(df['road_accident_type']).most_common(1)[0][0] if len(df) > 0 else 'N/A',
                'most_common_cause': Counter(df['road_accident_cause']).most_common(1)[0][0] if len(df) > 0 else 'N/A',
                'most_common_weather': Counter(df['weather']).most_common(1)[0][0] if len(df) > 0 else 'N/A',
                'most_common_road_condition': Counter(df['road_condition']).most_common(1)[0][0] if len(df) > 0 else 'N/A',
                'most_common_vehicle_type': Counter(df['vehicle_type']).most_common(1)[0][0] if len(df) > 0 else 'N/A',
                'most_common_driver_age': Counter(df['driver_age']).most_common(1)[0][0] if len(df) > 0 else 'N/A',
                'most_common_driver_gender': Counter(df['driver_gender']).most_common(1)[0][0] if len(df) > 0 else 'N/A'
            }
            return {
                'trends': get_cdrrmo_trends(time_filter, municipality, date, week_start),
                'distribution': get_cdrrmo_distribution(time_filter, municipality, date, week_start),
                'causes': get_cdrrmo_causes(time_filter, municipality, date, week_start),
                'types': get_cdrrmo_types(time_filter, municipality, date, week_start),
                'road_conditions': get_cdrrmo_road_conditions(time_filter, municipality, date, week_start),
                'weather': get_cdrrmo_weather(time_filter, municipality, date, week_start),
                'vehicle_types': get_cdrrmo_vehicle_types(time_filter, municipality, date, week_start),
                'driver_age': get_cdrrmo_driver_age(time_filter, municipality, date, week_start),
                'driver_gender': get_cdrrmo_driver_gender(time_filter, municipality, date, week_start),
                'dates': dates,
                'summary': summary
            }
        return {
            'trends': get_cdrrmo_trends(time_filter, municipality, date, week_start),
            'distribution': get_cdrrmo_distribution(time_filter, municipality, date, week_start),
            'causes': get_cdrrmo_causes(time_filter, municipality, date, week_start),
            'types': get_cdrrmo_types(time_filter, municipality, date, week_start),
            'road_conditions': get_cdrrmo_road_conditions(time_filter, municipality, date, week_start),
            'weather': get_cdrrmo_weather(time_filter, municipality, date, week_start),
            'vehicle_types': get_cdrrmo_vehicle_types(time_filter, municipality, date, week_start),
            'driver_age': get_cdrrmo_driver_age(time_filter, municipality, date, week_start),
            'driver_gender': get_cdrrmo_driver_gender(time_filter, municipality, date, week_start)
        }
    except Exception as e:
        logger.error(f"Error in get_cdrrmo_analytics_data: {e}")
        return {'error': str(e)}

def get_cdrrmo_trends(time_filter, municipality='', date=None, week_start=None):
    try:
        df = load_response_data(time_filter, municipality, date, week_start)
        start = pd.to_datetime(date if date else week_start if week_start else datetime.now())
        if time_filter == 'today':
            labels = [(start + timedelta(hours=i)).strftime('%H:%M') for i in range(24)]
            total = [len(df[df['timestamp'].dt.hour == i]) for i in range(24)]
            responded = [len(df[(df['timestamp'].dt.hour == i) & (df['responded'] == True)]) for i in range(24)]
        elif time_filter == 'daily':
            labels = [(start + timedelta(hours=i)).strftime('%H:%M') for i in range(24)]
            total = [len(df[df['timestamp'].dt.hour == i]) for i in range(24)]
            responded = [len(df[(df['timestamp'].dt.hour == i) & (df['responded'] == True)]) for i in range(24)]
        elif time_filter == 'weekly':
            labels = [(start + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
            total = [len(df[df['timestamp'].dt.date == (start + timedelta(days=i)).date()]) for i in range(7)]
            responded = [len(df[(df['timestamp'].dt.date == (start + timedelta(days=i)).date()) & (df['responded'] == True)]) for i in range(7)]
        elif time_filter == 'monthly':
            labels = [(start + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(0, 30, 2)]
            total = [len(df[(df['timestamp'].dt.date >= (start + timedelta(days=i)).date()) & 
                           (df['timestamp'].dt.date < (start + timedelta(days=i+2)).date())]) for i in range(0, 30, 2)]
            responded = [len(df[(df['timestamp'].dt.date >= (start + timedelta(days=i)).date()) & 
                               (df['timestamp'].dt.date < (start + timedelta(days=i+2)).date()) & 
                               (df['responded'] == True)]) for i in range(0, 30, 2)]
        else:  # yearly
            labels = [(start + timedelta(days=i*30)).strftime('%Y-%m') for i in range(12)]
            total = [len(df[(df['timestamp'].dt.year == (start + timedelta(days=i*30)).year) & 
                           (df['timestamp'].dt.month == (start + timedelta(days=i*30)).month)]) for i in range(12)]
            responded = [len(df[(df['timestamp'].dt.year == (start + timedelta(days=i*30)).year) & 
                               (df['timestamp'].dt.month == (start + timedelta(days=i*30)).month) & 
                               (df['responded'] == True)]) for i in range(12)]
        return {'labels': labels, 'total': total, 'responded': responded}
    except Exception as e:
        logger.error(f"Error in get_cdrrmo_trends: {e}")
        return {'labels': [], 'total': [], 'responded': []}

def get_cdrrmo_distribution(time_filter, municipality='', date=None, week_start=None):
    try:
        df = load_response_data(time_filter, municipality, date, week_start)
        distribution = Counter(df['emergency_type'])
        return {k: {'total': v, 'responded': len(df[(df['emergency_type'] == k) & (df['responded'] == True)])} 
                for k, v in distribution.items()}
    except Exception as e:
        logger.error(f"Error in get_cdrrmo_distribution: {e}")
        return {'Unknown': {'total': 0, 'responded': 0}}

def get_cdrrmo_causes(time_filter, municipality='', date=None, week_start=None):
    try:
        df = load_response_data(time_filter, municipality, date, week_start)
        road_causes = Counter(df['road_accident_cause'])
        fire_causes = Counter(df[df['emergency_type'] == 'fire_incident']['fire_cause'] if 'fire_cause' in df else {})
        return {'road': dict(road_causes), 'fire': dict(fire_causes)}
    except Exception as e:
        logger.error(f"Error in get_cdrrmo_causes: {e}")
        return {'road': {'Unknown': 0}, 'fire': {'Unknown': 0}}

def get_cdrrmo_types(time_filter, municipality='', date=None, week_start=None):
    try:
        df = load_response_data(time_filter, municipality, date, week_start)
        return dict(Counter(df['road_accident_type']))
    except Exception as e:
        logger.error(f"Error in get_cdrrmo_types: {e}")
        return {'Unknown': 0}

def get_cdrrmo_road_conditions(time_filter, municipality='', date=None, week_start=None):
    try:
        df = load_response_data(time_filter, municipality, date, week_start)
        return dict(Counter(df['road_condition']))
    except Exception as e:
        logger.error(f"Error in get_cdrrmo_road_conditions: {e}")
        return {'Unknown': 0}

def get_cdrrmo_weather(time_filter, municipality='', date=None, week_start=None):
    try:
        df = load_response_data(time_filter, municipality, date, week_start)
        return dict(Counter(df['weather']))
    except Exception as e:
        logger.error(f"Error in get_cdrrmo_weather: {e}")
        return {'Unknown': 0}

def get_cdrrmo_vehicle_types(time_filter, municipality='', date=None, week_start=None):
    try:
        df = load_response_data(time_filter, municipality, date, week_start)
        return dict(Counter(df['vehicle_type']))
    except Exception as e:
        logger.error(f"Error in get_cdrrmo_vehicle_types: {e}")
        return {'Unknown': 0}

def get_cdrrmo_driver_age(time_filter, municipality='', date=None, week_start=None):
    try:
        df = load_response_data(time_filter, municipality, date, week_start)
        return dict(Counter(df['driver_age']))
    except Exception as e:
        logger.error(f"Error in get_cdrrmo_driver_age: {e}")
        return {'Unknown': 0}

def get_cdrrmo_driver_gender(time_filter, municipality='', date=None, week_start=None):
    try:
        df = load_response_data(time_filter, municipality, date, week_start)
        return dict(Counter(df['driver_gender']))
    except Exception as e:
        logger.error(f"Error in get_cdrrmo_driver_gender: {e}")
        return {'Unknown': 0}