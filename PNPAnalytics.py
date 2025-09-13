import pandas as pd
import logging
from collections import Counter
from datetime import datetime, timedelta
import pytz
from flask import request, jsonify
from AlertNow import responses

logger = logging.getLogger(__name__)

def load_response_data(time_filter, role='pnp', municipality=''):
    try:
        response_data = [r for r in responses if r.get('role') == role and (not municipality or r.get('municipality', '').lower() == municipality.lower())]
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

def get_pnp_trends(time_filter, municipality=''):
    try:
        df = load_response_data(time_filter, 'pnp', municipality)
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
        logger.error(f"Error in get_pnp_trends: {e}")
        return {'labels': [], 'total': []}

def get_pnp_distribution(time_filter, municipality=''):
    try:
        df = load_response_data(time_filter, 'pnp', municipality)
        distribution = Counter(df.get('emergency_type', ['unknown']))
        return {k: {'total': v, 'responded': len(df[(df['emergency_type'] == k) & (df.get('responded', False) == True)])} for k, v in distribution.items()}
    except Exception as e:
        logger.error(f"Error in get_pnp_distribution: {e}")
        return {'Unknown': {'total': 0, 'responded': 0}}

def get_pnp_causes(time_filter, municipality=''):
    try:
        df = load_response_data(time_filter, 'pnp', municipality)
        road_causes = Counter(df.get('predicted_cause', df.get('cause', ['Unknown'])))
        return {'road': dict(road_causes)}
    except Exception as e:
        logger.error(f"Error in get_pnp_causes: {e}")
        return {'road': {'Unknown': 0}}

def get_pnp_accident_types(time_filter, municipality=''):
    try:
        df = load_response_data(time_filter, 'pnp', municipality)
        accident_types = Counter(df.get('accident_type', ['Unknown']))
        return dict(accident_types)
    except Exception as e:
        logger.error(f"Error in get_pnp_accident_types: {e}")
        return {'Unknown': 0}

def get_pnp_road_conditions(time_filter, municipality=''):
    try:
        df = load_response_data(time_filter, 'pnp', municipality)
        road_conditions = Counter(df.get('road_condition', ['Unknown']))
        return dict(road_conditions)
    except Exception as e:
        logger.error(f"Error in get_pnp_road_conditions: {e}")
        return {'Unknown': 0}

def get_pnp_weather(time_filter, municipality=''):
    try:
        df = load_response_data(time_filter, 'pnp', municipality)
        weather = Counter(df.get('weather', ['Unknown']))
        return dict(weather)
    except Exception as e:
        logger.error(f"Error in get_pnp_weather: {e}")
        return {'Unknown': 0}

def get_pnp_vehicle_types(time_filter, municipality=''):
    try:
        df = load_response_data(time_filter, 'pnp', municipality)
        vehicle_types = Counter(df.get('vehicle_type', ['Unknown']))
        return dict(vehicle_types)
    except Exception as e:
        logger.error(f"Error in get_pnp_vehicle_types: {e}")
        return {'Unknown': 0}

def get_pnp_driver_age(time_filter, municipality=''):
    try:
        df = load_response_data(time_filter, 'pnp', municipality)
        driver_age = Counter(df.get('driver_age', ['Unknown']))
        return dict(driver_age)
    except Exception as e:
        logger.error(f"Error in get_pnp_driver_age: {e}")
        return {'Unknown': 0}

def get_pnp_driver_gender(time_filter, municipality=''):
    try:
        df = load_response_data(time_filter, 'pnp', municipality)
        driver_gender = Counter(df.get('driver_gender', ['Unknown']))
        return dict(driver_gender)
    except Exception as e:
        logger.error(f"Error in get_pnp_driver_gender: {e}")
        return {'Unknown': 0}

def get_pnp_analytics_data():
    try:
        time_filter = request.args.get('time', 'weekly')
        municipality = request.args.get('municipality', '')
        trends = get_pnp_trends(time_filter, municipality)
        distribution = get_pnp_distribution(time_filter, municipality)
        causes = get_pnp_causes(time_filter, municipality)
        accident_types = get_pnp_accident_types(time_filter, municipality)
        road_conditions = get_pnp_road_conditions(time_filter, municipality)
        weather = get_pnp_weather(time_filter, municipality)
        vehicle_types = get_pnp_vehicle_types(time_filter, municipality)
        driver_age = get_pnp_driver_age(time_filter, municipality)
        driver_gender = get_pnp_driver_gender(time_filter, municipality)
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
        logger.error(f"Error in get_pnp_analytics_data: {e}")
        return jsonify({'error': 'Failed to retrieve analytics data'}), 500