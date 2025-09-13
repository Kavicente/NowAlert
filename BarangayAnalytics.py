from flask import Flask, request, jsonify
import pandas as pd
import logging
from collections import Counter
from datetime import datetime, timedelta
import pytz
from AlertNow import responses, road_accident_df, fire_incident_df


logger = logging.getLogger(__name__)

def load_csv_data(file_name, time_filter, incident_type=None):
    try:
        df = road_accident_df if incident_type == 'road' else fire_incident_df
        if df.empty:
            logger.warning(f"{file_name} is empty or not loaded")
            return pd.DataFrame()
        
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
            
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]
        
        return df
    except Exception as e:
        logger.error(f"Error in load_csv_data for {file_name}: {e}")
        return pd.DataFrame()

def get_barangay_trends(time_filter, barangay=''):
    try:
        road_df = load_csv_data('road_accident.csv', time_filter, incident_type='road')
        if barangay and 'barangay' in road_df.columns:
            road_df = road_df[road_df['barangay'] == barangay]
        
        labels = []
        total = []
        if time_filter == 'today':
            labels = [datetime.now(pytz.timezone('Asia/Manila')).strftime('%H:%M')]
            total = [len(road_df)]
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
            total = [len(road_df[road_df['timestamp'].dt.date == d.date()]) if time_filter in ['daily', 'weekly', 'monthly'] else len(road_df[road_df['timestamp'].dt.to_period('M') == d.to_period('M')]) for d in date_range]
        
        return {'labels': labels, 'total': total}
    except Exception as e:
        logger.error(f"Error in get_barangay_trends: {e}")
        return {'labels': [], 'total': []}

def get_barangay_distribution(time_filter, barangay=''):
    try:
        road_df = load_csv_data('road_accident.csv', time_filter, incident_type='road')
        if barangay and 'barangay' in road_df.columns:
            road_df = road_df[road_df['barangay'] == barangay]
        distribution = Counter(road_df['emergency_type'])
        return {k: {'total': v, 'responded': len(road_df[(road_df['emergency_type'] == k) & (road_df['responded'] == True)])} 
                for k, v in distribution.items()}
    except Exception as e:
        logger.error(f"Error in get_barangay_distribution: {e}")
        return {'Unknown': {'total': 0, 'responded': 0}}

def get_barangay_causes(time_filter, barangay=''):
    try:
        road_df = load_csv_data('road_accident.csv', time_filter, incident_type='road')
        if barangay and 'barangay' in road_df.columns:
            road_df = road_df[road_df['barangay'] == barangay]
        road_causes = Counter(road_df['predicted_cause'] if 'predicted_cause' in road_df else road_df['cause'])
        return {'road': dict(road_causes)}
    except Exception as e:
        logger.error(f"Error in get_barangay_causes: {e}")
        return {'road': {'Unknown': 0}}

def get_barangay_accident_types(time_filter, barangay=''):
    try:
        response_data = [r for r in responses if r.get('role') == 'barangay' and (not barangay or r.get('barangay', '').lower() == barangay.lower())]
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
        accident_types = Counter(df['road_accident_type'] if 'road_accident_type' in df else df['accident_type'])
        return dict(accident_types)
    except Exception as e:
        logger.error(f"Error in get_barangay_accident_types: {e}")
        return {'Unknown': 0}

def get_barangay_road_conditions(time_filter, barangay=''):
    try:
        response_data = [r for r in responses if r.get('role') == 'barangay' and (not barangay or r.get('barangay', '').lower() == barangay.lower())]
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
        road_conditions = Counter(df['road_condition'])
        return dict(road_conditions)
    except Exception as e:
        logger.error(f"Error in get_barangay_road_conditions: {e}")
        return {'Unknown': 0}

def get_barangay_weather(time_filter, barangay=''):
    try:
        response_data = [r for r in responses if r.get('role') == 'barangay' and (not barangay or r.get('barangay', '').lower() == barangay.lower())]
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
        weather = Counter(df['weather'])
        return dict(weather)
    except Exception as e:
        logger.error(f"Error in get_barangay_weather: {e}")
        return {'Unknown': 0}

def get_barangay_vehicle_types(time_filter, barangay=''):
    try:
        response_data = [r for r in responses if r.get('role') == 'barangay' and (not barangay or r.get('barangay', '').lower() == barangay.lower())]
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
        vehicle_types = Counter(df['vehicle_type'])
        return dict(vehicle_types)
    except Exception as e:
        logger.error(f"Error in get_barangay_vehicle_types: {e}")
        return {'Unknown': 0}

def get_barangay_driver_age(time_filter, barangay=''):
    try:
        response_data = [r for r in responses if r.get('role') == 'barangay' and (not barangay or r.get('barangay', '').lower() == barangay.lower())]
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
        driver_age = Counter(df['driver_age'])
        return dict(driver_age)
    except Exception as e:
        logger.error(f"Error in get_barangay_driver_age: {e}")
        return {'Unknown': 0}

def get_barangay_driver_gender(time_filter, barangay=''):
    try:
        response_data = [r for r in responses if r.get('role') == 'barangay' and (not barangay or r.get('barangay', '').lower() == barangay.lower())]
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
        driver_gender = Counter(df['driver_gender'])
        return dict(driver_gender)
    except Exception as e:
        logger.error(f"Error in get_barangay_driver_gender: {e}")
        return {'Unknown': 0}

def get_barangay_analytics_data():
    try:
        time_filter = request.args.get('time', 'weekly')
        barangay = request.args.get('barangay', '')
        trends = get_barangay_trends(time_filter, barangay)
        distribution = get_barangay_distribution(time_filter, barangay)
        causes = get_barangay_causes(time_filter, barangay)
        accident_types = get_barangay_accident_types(time_filter, barangay)
        road_conditions = get_barangay_road_conditions(time_filter, barangay)
        weather = get_barangay_weather(time_filter, barangay)
        vehicle_types = get_barangay_vehicle_types(time_filter, barangay)
        driver_age = get_barangay_driver_age(time_filter, barangay)
        driver_gender = get_barangay_driver_gender(time_filter, barangay)
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