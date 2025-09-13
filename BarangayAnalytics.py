import pandas as pd
import logging
from collections import Counter
from datetime import datetime, timedelta
import pytz
from flask import request, jsonify

logger = logging.getLogger(__name__)

def load_response_data(responses, time_filter, role='barangay', barangay=''):
    try:
        response_data = [r for r in responses if r.get('role') == role and (not barangay or r.get('barangay', '').lower() == barangay.lower())]
        df = pd.DataFrame(response_data)
        if time_filter != 'yearly':
            end_date = datetime.now(pytz.timezone('Asia/Manila'))
            if time_filter == 'today':
                start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
            elif time_filter == 'daily':
                start_date = end_date - timedelta(days=1)
            elif time_filter == 'weekly':
                start_date = end_date - timedelta(days=7)
            elif time_filter == 'monthly':
                start_date = end_date - timedelta(days=30)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]
        return df
    except Exception as e:
        logger.error(f"Error in load_response_data: {e}")
        return pd.DataFrame()

def get_barangay_trends(responses, time_filter, barangay=''):
    try:
        df = load_response_data(responses, time_filter, 'barangay', barangay)
        labels = []
        total = []
        if time_filter == 'today':
            labels = [datetime.now(pytz.timezone('Asia/Manila')).strftime('%H:%M')]
            total = [len(df)]
        elif time_filter in ['daily', 'weekly', 'monthly', 'yearly']:
            if time_filter == 'daily':
                freq = 'H'
                periods = 24
            elif time_filter == 'weekly':
                freq = 'D'
                periods = 7
            elif time_filter == 'monthly':
                freq = 'D'
                periods = 30
            elif time_filter == 'yearly':
                freq = 'M'
                periods = 12
            date_range = pd.date_range(end=datetime.now(pytz.timezone('Asia/Manila')), periods=periods, freq=freq)
            labels = [d.strftime('%Y-%m-%d') if time_filter in ['daily', 'weekly', 'monthly'] else d.strftime('%Y-%m') for d in date_range]
            total = [len(df[df['timestamp'].dt.date == d.date()]) if time_filter in ['daily', 'weekly', 'monthly'] else len(df[df['timestamp'].dt.to_period('M') == d.to_period('M')]) for d in date_range]
        return {'labels': labels, 'total': total}
    except Exception as e:
        logger.error(f"Error in get_barangay_trends: {e}")
        return {'labels': [], 'total': []}

def get_barangay_distribution(responses, time_filter, barangay=''):
    try:
        df = load_response_data(responses, time_filter, 'barangay', barangay)
        distribution = Counter(df.get('emergency_type', ['unknown']))
        return {k: {'total': v, 'responded': len(df[(df['emergency_type'] == k) & (df.get('responded', False) == True)])} for k, v in distribution.items()}
    except Exception as e:
        logger.error(f"Error in get_barangay_distribution: {e}")
        return {'Unknown': {'total': 0, 'responded': 0}}

def get_barangay_causes(responses, time_filter, barangay=''):
    try:
        df = load_response_data(responses, time_filter, 'barangay', barangay)
        road_causes = Counter(df.get('predicted_cause', df.get('cause', ['Unknown'])))
        return {'road': dict(road_causes)}
    except Exception as e:
        logger.error(f"Error in get_barangay_causes: {e}")
        return {'road': {'Unknown': 0}}

def get_barangay_accident_types(responses, time_filter, barangay=''):
    try:
        df = load_response_data(responses, time_filter, 'barangay', barangay)
        accident_types = Counter(df.get('road_accident_type', df.get('accident_type', ['Unknown'])))
        return dict(accident_types)
    except Exception as e:
        logger.error(f"Error in get_barangay_accident_types: {e}")
        return {'Unknown': 0}

def get_barangay_road_conditions(responses, time_filter, barangay=''):
    try:
        df = load_response_data(responses, time_filter, 'barangay', barangay)
        road_conditions = Counter(df.get('road_condition', ['Unknown']))
        return dict(road_conditions)
    except Exception as e:
        logger.error(f"Error in get_barangay_road_conditions: {e}")
        return {'Unknown': 0}

def get_barangay_weather(responses, time_filter, barangay=''):
    try:
        df = load_response_data(responses, time_filter, 'barangay', barangay)
        weather = Counter(df.get('weather', ['Unknown']))
        return dict(weather)
    except Exception as e:
        logger.error(f"Error in get_barangay_weather: {e}")
        return {'Unknown': 0}

def get_barangay_vehicle_types(responses, time_filter, barangay=''):
    try:
        df = load_response_data(responses, time_filter, 'barangay', barangay)
        vehicle_types = Counter(df.get('vehicle_type', ['Unknown']))
        return dict(vehicle_types)
    except Exception as e:
        logger.error(f"Error in get_barangay_vehicle_types: {e}")
        return {'Unknown': 0}

def get_barangay_driver_age(responses, time_filter, barangay=''):
    try:
        df = load_response_data(responses, time_filter, 'barangay', barangay)
        driver_age = Counter(df.get('driver_age', ['Unknown']))
        return dict(driver_age)
    except Exception as e:
        logger.error(f"Error in get_barangay_driver_age: {e}")
        return {'Unknown': 0}

def get_barangay_driver_gender(responses, time_filter, barangay=''):
    try:
        df = load_response_data(responses, time_filter, 'barangay', barangay)
        driver_gender = Counter(df.get('driver_gender', ['Unknown']))
        return dict(driver_gender)
    except Exception as e:
        logger.error(f"Error in get_barangay_driver_gender: {e}")
        return {'Unknown': 0}

def get_barangay_analytics_data(responses):
    try:
        time_filter = request.args.get('time', 'weekly')
        barangay = request.args.get('barangay', '')
        trends = get_barangay_trends(responses, time_filter, barangay)
        distribution = get_barangay_distribution(responses, time_filter, barangay)
        causes = get_barangay_causes(responses, time_filter, barangay)
        accident_types = get_barangay_accident_types(responses, time_filter, barangay)
        road_conditions = get_barangay_road_conditions(responses, time_filter, barangay)
        weather = get_barangay_weather(responses, time_filter, barangay)
        vehicle_types = get_barangay_vehicle_types(responses, time_filter, barangay)
        driver_age = get_barangay_driver_age(responses, time_filter, barangay)
        driver_gender = get_barangay_driver_gender(responses, time_filter, barangay)
        responded = {k: v['responded'] for k, v in distribution.items()}
        
        return jsonify({
            'trends': trends,
            'distribution': distribution,
            'causes': causes,
            'accident_types': accident_types,
            'road_conditions': road_conditions,
            'weather': weather,
            'vehicle_types': vehicle_types,
            'driver_age': driver_age,
            'driver_gender': driver_gender,
            'responded': responded
        })
    except Exception as e:
        logger.error(f"Error in get_barangay_analytics_data: {e}")
        return jsonify({'error': 'Failed to retrieve analytics data'}), 500

def generate_mock_data():
    mock_data = {
        'road_accidents': [{'timestamp': '2023-01-01 10:00', 'emergency_type': 'road_accident', 'barangay': 'Barangay 1', 'cause': 'Overspeeding'}],
        'fire_incidents': [{'timestamp': '2023-01-01 12:00', 'emergency_type': 'fire_incident', 'barangay': 'Barangay 1', 'cause': 'Electrical Fault'}]
    }
    return mock_data