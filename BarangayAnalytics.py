import pandas as pd
import logging
from datetime import datetime, timedelta
from collections import Counter
import pytz
import sqlite3
import os

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'users_web.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def load_response_data(time_filter, barangay, date=None, week_start=None):
    try:
        conn = get_db_connection()
        query = "SELECT * FROM barangay_response WHERE barangay = ?"
        params = [barangay]
        
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

def get_barangay_analytics_data(time_filter, barangay):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Define date range for 'today'
        today = datetime.now(pytz.timezone('Asia/Manila')).date()
        start_time = datetime.combine(today, datetime.min.time()).astimezone(pytz.timezone('Asia/Manila')).isoformat()
        end_time = datetime.combine(today, datetime.max.time()).astimezone(pytz.timezone('Asia/Manila')).isoformat()
        
        query = '''
            SELECT road_accident_cause, road_accident_type, weather, road_condition, vehicle_type, driver_age, driver_gender, timestamp
            FROM barangay_response
            WHERE barangay = ? AND emergency_type = 'road' AND timestamp BETWEEN ? AND ? AND responded = 1
        '''
        params = (barangay.lower(), start_time, end_time)
        
        if time_filter == 'daily':
            query = query.replace('timestamp BETWEEN ? AND ?', 'DATE(timestamp) = DATE(?)')
            params = (barangay.lower(), start_time)
        elif time_filter == 'weekly':
            start_time = (today - timedelta(days=today.weekday())).isoformat()
            query = query.replace('timestamp BETWEEN ? AND ?', 'timestamp >= ?')
            params = (barangay.lower(), start_time)
        elif time_filter == 'monthly':
            start_time = today.replace(day=1).isoformat()
            query = query.replace('timestamp BETWEEN ? AND ?', 'timestamp >= ?')
            params = (barangay.lower(), start_time)
        elif time_filter == 'yearly':
            start_time = today.replace(month=1, day=1).isoformat()
            query = query.replace('timestamp BETWEEN ? AND ?', 'timestamp >= ?')
            params = (barangay.lower(), start_time)

        c.execute(query, params)
        responses = c.fetchall()
        conn.close()

        # Initialize data structure
        data = {
            'trends': {'labels': [], 'total': [], 'responded': []},
            'distribution': {},
            'causes': {'road': {}, 'fire': {}},
            'types': {},
            'road_conditions': {},
            'weather': {},
            'vehicle_types': {},
            'driver_age': {},
            'driver_gender': {}
        }

        if not responses:
            return data

        # Process responses
        timestamps = [datetime.fromisoformat(row['timestamp']) for row in responses]
        causes = Counter(row['road_accident_cause'] or 'Unknown' for row in responses)
        types = Counter(row['road_accident_type'] or 'Unknown' for row in responses)
        road_conditions = Counter(row['road_condition'] or 'Unknown' for row in responses)
        weather = Counter(row['weather'] or 'Unknown' for row in responses)
        vehicle_types = Counter(row['vehicle_type'] or 'Unknown' for row in responses)
        driver_age = Counter(row['driver_age'] or 'Unknown' for row in responses)
        driver_gender = Counter(row['driver_gender'] or 'Unknown' for row in responses)

        # Trends (assuming hourly for today, daily for others)
        if time_filter == 'today':
            labels = [f"{h:02d}:00" for h in range(24)]
            total_counts = [0] * 24
            responded_counts = [0] * 24
            for ts in timestamps:
                hour = ts.hour
                total_counts[hour] += 1
                responded_counts[hour] += 1  # All responses are marked as responded
        else:
            # For daily, weekly, monthly, yearly, use dates as labels
            dates = sorted(set(ts.date().isoformat() for ts in timestamps))
            labels = dates
            total_counts = [sum(1 for ts in timestamps if ts.date().isoformat() == date) for date in dates]
            responded_counts = total_counts  # All responses are marked as responded

        data['trends'] = {
            'labels': labels,
            'total': total_counts,
            'responded': responded_counts
        }
        data['distribution'] = {key: {'total': value, 'responded': value} for key, value in causes.items()}
        data['causes']['road'] = dict(causes)
        data['types'] = dict(types)
        data['road_conditions'] = dict(road_conditions)
        data['weather'] = dict(weather)
        data['vehicle_types'] = dict(vehicle_types)
        data['driver_age'] = dict(driver_age)
        data['driver_gender'] = dict(driver_gender)

        return data
    except Exception as e:
        print(f"Error in get_barangay_analytics_data: {e}")
        return {
            'trends': {'labels': [], 'total': [], 'responded': []},
            'distribution': {},
            'causes': {'road': {}, 'fire': {}},
            'types': {},
            'road_conditions': {},
            'weather': {},
            'vehicle_types': {},
            'driver_age': {},
            'driver_gender': {}
        }

def get_barangay_trends(time_filter, barangay='', date=None, week_start=None):
    try:
        df = load_response_data(time_filter, barangay, date, week_start)
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
        logger.error(f"Error in get_barangay_trends: {e}")
        return {'labels': [], 'total': [], 'responded': []}

def get_barangay_distribution(time_filter, barangay='', date=None, week_start=None):
    try:
        df = load_response_data(time_filter, barangay, date, week_start)
        distribution = Counter(df['emergency_type'])
        return {k: {'total': v, 'responded': len(df[(df['emergency_type'] == k) & (df['responded'] == True)])} 
                for k, v in distribution.items()}
    except Exception as e:
        logger.error(f"Error in get_barangay_distribution: {e}")
        return {'Unknown': {'total': 0, 'responded': 0}}

def get_barangay_causes(time_filter, barangay='', date=None, week_start=None):
    try:
        df = load_response_data(time_filter, barangay, date, week_start)
        road_causes = Counter(df['road_accident_cause'])
        fire_causes = Counter(df[df['emergency_type'] == 'fire_incident']['fire_cause'] if 'fire_cause' in df else {})
        return {'road': dict(road_causes), 'fire': dict(fire_causes)}
    except Exception as e:
        logger.error(f"Error in get_barangay_causes: {e}")
        return {'road': {'Unknown': 0}, 'fire': {'Unknown': 0}}

def get_barangay_types(time_filter, barangay='', date=None, week_start=None):
    try:
        df = load_response_data(time_filter, barangay, date, week_start)
        return dict(Counter(df['road_accident_type']))
    except Exception as e:
        logger.error(f"Error in get_barangay_types: {e}")
        return {'Unknown': 0}

def get_barangay_road_conditions(time_filter, barangay='', date=None, week_start=None):
    try:
        df = load_response_data(time_filter, barangay, date, week_start)
        return dict(Counter(df['road_condition']))
    except Exception as e:
        logger.error(f"Error in get_barangay_road_conditions: {e}")
        return {'Unknown': 0}

def get_barangay_weather(time_filter, barangay='', date=None, week_start=None):
    try:
        df = load_response_data(time_filter, barangay, date, week_start)
        return dict(Counter(df['weather']))
    except Exception as e:
        logger.error(f"Error in get_barangay_weather: {e}")
        return {'Unknown': 0}

def get_barangay_vehicle_types(time_filter, barangay='', date=None, week_start=None):
    try:
        df = load_response_data(time_filter, barangay, date, week_start)
        return dict(Counter(df['vehicle_type']))
    except Exception as e:
        logger.error(f"Error in get_barangay_vehicle_types: {e}")
        return {'Unknown': 0}

def get_barangay_driver_age(time_filter, barangay='', date=None, week_start=None):
    try:
        df = load_response_data(time_filter, barangay, date, week_start)
        return dict(Counter(df['driver_age']))
    except Exception as e:
        logger.error(f"Error in get_barangay_driver_age: {e}")
        return {'Unknown': 0}

def get_barangay_driver_gender(time_filter, barangay='', date=None, week_start=None):
    try:
        df = load_response_data(time_filter, barangay, date, week_start)
        return dict(Counter(df['driver_gender']))
    except Exception as e:
        logger.error(f"Error in get_barangay_driver_gender: {e}")
        return {'Unknown': 0}

def generate_mock_data():
    return {
        'trends': {'labels': ['2023-01-01', '2023-01-02'], 'total': [10, 15], 'responded': [8, 12]},
        'distribution': {'road_accident': {'total': 20, 'responded': 15}, 'fire_incident': {'total': 5, 'responded': 4}},
        'causes': {'road': {'Collision': 10, 'Skidding': 5}, 'fire': {'Electrical': 3, 'Arson': 2}},
        'types': {'Collision': 10, 'Skidding': 5},
        'road_conditions': {'Wet': 8, 'Dry': 7},
        'weather': {'Rainy': 10, 'Clear': 5},
        'vehicle_types': {'Car': 10, 'Truck': 5},
        'driver_age': {'20-30': 8, '30-40': 7},
        'driver_gender': {'Male': 10, 'Female': 5}
    }