import pandas as pd
import logging
from datetime import datetime, timedelta
import pytz
from collections import Counter
import sqlite3
import os
import numpy as np
from models import lr_road

logger = logging.getLogger(__name__)

# Placeholder for machine learning model
lr_road = None

def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'users_web.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_time_range(time_filter):
    end = datetime.now(pytz.timezone('Asia/Manila'))
    if time_filter == 'today':
        start = end.replace(hour=0, minute=0, second=0, microsecond=0)
    elif time_filter == 'daily':
        start = end - timedelta(days=1)
    elif time_filter == 'weekly':
        start = end - timedelta(days=7)
    elif time_filter == 'monthly':
        start = end - timedelta(days=30)
    elif time_filter == 'yearly':
        start = end - timedelta(days=365)
    else:
        start = end - timedelta(days=7)  # Default to weekly
    return start, end

def generate_mock_data(time_filter, incident_type='road'):
    start, end = get_time_range(time_filter)
    num_entries = 100
    dates = pd.date_range(start, end, periods=num_entries)
    barangays = ['Barangay 1', 'Barangay 2', 'Barangay 3']
    weather_types = ['Sunny', 'Rainy', 'Cloudy', 'Foggy']
    road_conditions = ['Dry', 'Wet', 'Icy', 'Snowy']
    vehicle_types = ['Car', 'Motorcycle', 'Truck', 'Bus']
    driver_ages = ['18-25', '26-35', '36-50', '51+']
    driver_genders = ['Male', 'Female']
    accident_types = ['Overspeeding', 'Drunk Driving', 'Reckless Driving', 'Overloading', 'Fatigue']
    accident_causes = ['Head-on collision', 'Rear-end collision', 'Side-impact collision', 'Single vehicle accident', 'Pedestrian accident']
    
    data = {
        'timestamp': dates,
        'barangay': np.random.choice(barangays, size=num_entries),
        'weather': np.random.choice(weather_types, size=num_entries),
        'road_condition': np.random.choice(road_conditions, size=num_entries),
        'vehicle_type': np.random.choice(vehicle_types, size=num_entries),
        'driver_age': np.random.choice(driver_ages, size=num_entries),
        'driver_gender': np.random.choice(driver_genders, size=num_entries),
        'road_accident_type': np.random.choice(accident_types, size=num_entries),
        'road_accident_cause': np.random.choice(accident_causes, size=num_entries),
        'emergency_type': [incident_type] * num_entries,
        'responded': np.random.choice([True, False], size=num_entries)
    }
    return pd.DataFrame(data)

def load_response_data(time_filter, municipality=''):
    try:
        conn = get_db_connection()
        query = '''
            SELECT * FROM pnp_response
            WHERE timestamp >= ? AND timestamp <= ?
        '''
        params = [get_time_range(time_filter)[0].isoformat(), get_time_range(time_filter)[1].isoformat()]
        if municipality:
            query += ' AND barangay IN (SELECT barangay FROM barangays WHERE municipality = ?)'
            params.append(municipality)
        
        df = pd.read_sql_query(query, conn, params=params, parse_dates=['timestamp'])
        conn.close()
        
        if df.empty:
            logger.warning(f"No response data found for municipality {municipality}, generating mock data")
            return generate_mock_data(time_filter, incident_type='road')
        
        return df
    except Exception as e:
        logger.error(f"Error loading response data: {e}")
        return generate_mock_data(time_filter, incident_type='road')


# Add this function to PNPAnalytics.py
def get_pnp_analytics_data(time_filter, municipality=''):
    try:
        data = {
            'trends': get_pnp_trends(time_filter, municipality),
            'distribution': get_pnp_distribution(time_filter, municipality),
            'causes': get_pnp_causes(time_filter, municipality),
            'types': get_pnp_types(time_filter, municipality),
            'road_conditions': get_pnp_road_conditions(time_filter, municipality),
            'weather': get_pnp_weather(time_filter, municipality),
            'vehicle_types': get_pnp_vehicle_types(time_filter, municipality),
            'driver_age': get_pnp_driver_age(time_filter, municipality),
            'driver_gender': get_pnp_driver_gender(time_filter, municipality)
        }
        return data
    except Exception as e:
        logger.error(f"Error in get_pnp_analytics_data: {e}")
        return {'error': str(e)}

def get_pnp_trends(time_filter, municipality=''):
    try:
        df = load_response_data(time_filter, municipality)
        start, end = get_time_range(time_filter)
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
        else:
            labels = [(start + timedelta(days=i*30)).strftime('%Y-%m') for i in range(12)]
            total = [len(df[(df['timestamp'].dt.year == (start + timedelta(days=i*30)).year) & 
                           (df['timestamp'].dt.month == (start + timedelta(days=i*30)).month)]) for i in range(12)]
            responded = [len(df[(df['timestamp'].dt.year == (start + timedelta(days=i*30)).year) & 
                               (df['timestamp'].dt.month == (start + timedelta(days=i*30)).month) & 
                               (df['responded'] == True)]) for i in range(12)]
        return {'labels': labels, 'total': total, 'responded': responded}
    except Exception as e:
        logger.error(f"Error in get_pnp_trends: {e}")
        return {'labels': [], 'total': [], 'responded': []}

def get_pnp_distribution(time_filter, municipality=''):
    try:
        df = load_response_data(time_filter, municipality)
        distribution = Counter(df['emergency_type'])
        return {k: {'total': v, 'responded': len(df[(df['emergency_type'] == k) & (df['responded'] == True)])} 
                for k, v in distribution.items()}
    except Exception as e:
        logger.error(f"Error in get_pnp_distribution: {e}")
        return {'Unknown': {'total': 0, 'responded': 0}}

def get_pnp_causes(time_filter, municipality=''):
    try:
        df = load_response_data(time_filter, municipality)
        road_causes = Counter(df['road_accident_cause'])
        return {'road': dict(road_causes)}
    except Exception as e:
        logger.error(f"Error in get_pnp_causes: {e}")
        return {'road': {'Unknown': 0}}

def get_pnp_types(time_filter, municipality=''):
    try:
        df = load_response_data(time_filter, municipality)
        return dict(Counter(df['road_accident_type']))
    except Exception as e:
        logger.error(f"Error in get_pnp_types: {e}")
        return {'Unknown': 0}

def get_pnp_road_conditions(time_filter, municipality=''):
    try:
        df = load_response_data(time_filter, municipality)
        return dict(Counter(df['road_condition']))
    except Exception as e:
        logger.error(f"Error in get_pnp_road_conditions: {e}")
        return {'Unknown': 0}

def get_pnp_weather(time_filter, municipality=''):
    try:
        df = load_response_data(time_filter, municipality)
        return dict(Counter(df['weather']))
    except Exception as e:
        logger.error(f"Error in get_pnp_weather: {e}")
        return {'Unknown': 0}

def get_pnp_vehicle_types(time_filter, municipality=''):
    try:
        df = load_response_data(time_filter, municipality)
        return dict(Counter(df['vehicle_type']))
    except Exception as e:
        logger.error(f"Error in get_pnp_vehicle_types: {e}")
        return {'Unknown': 0}

def get_pnp_driver_age(time_filter, municipality=''):
    try:
        df = load_response_data(time_filter, municipality)
        return dict(Counter(df['driver_age']))
    except Exception as e:
        logger.error(f"Error in get_pnp_driver_age: {e}")
        return {'Unknown': 0}

def get_pnp_driver_gender(time_filter, municipality=''):
    try:
        df = load_response_data(time_filter, municipality)
        return dict(Counter(df['driver_gender']))
    except Exception as e:
        logger.error(f"Error in get_pnp_driver_gender: {e}")
        return {'Unknown': 0}