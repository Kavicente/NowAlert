import pandas as pd
import logging
from datetime import datetime, timedelta
import pytz
from collections import Counter
import os
from models import lr_road, lr_fire
import numpy as np

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


today_responses = []

def get_time_range(time_filter):
    now = datetime.now(pytz.timezone('Asia/Manila'))
    if time_filter == 'today':
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif time_filter == 'daily':
        start = now - timedelta(days=1)
        end = now
    elif time_filter == 'weekly':
        start = now - timedelta(days=7)
        end = now
    elif time_filter == 'monthly':
        start = now - timedelta(days=30)
        end = now
    elif time_filter == 'yearly':
        start = now - timedelta(days=365)
        end = now
    else:
        start = now - timedelta(days=7)
        end = now
    return start, end

def generate_mock_data(time_filter, incident_type='road'):
    start, end = get_time_range(time_filter)
    num_entries = 100 if time_filter == 'yearly' else 50 if time_filter == 'monthly' else 20 if time_filter == 'weekly' else 10
    timestamps = pd.date_range(start, end, periods=num_entries, tz='Asia/Manila')
    if incident_type == 'road':
        emergency_types = ['Collision', 'Rollover', 'Pedestrian']
        causes = ['Speeding', 'Drunk Driving', 'Distracted Driving']
        road_condition = ['Dry', 'Wet', 'Icy']
        vehicle_type = ['Car', 'Motorcycle', 'Truck']
        data = {
            'timestamp': timestamps,
            'emergency_type': np.random.choice(emergency_types, size=num_entries),
            'cause': np.random.choice(causes, size=num_entries),
            'responded': np.random.choice([True, False], size=num_entries),
            'weather': np.random.choice(['Sunny', 'Rainy', 'Foggy'], size=num_entries),
            'road_condition': np.random.choice(road_condition, size=num_entries),
            'vehicle_type': np.random.choice(vehicle_type, size=num_entries),
            'barangay': np.random.choice(['Barangay 1', 'Barangay 2', 'Barangay 3'], size=num_entries)
        }
    elif incident_type == 'fire':
        emergency_types = ['Electrical', 'Arson', 'Cooking']
        causes = ['Electrical Fault', 'Arson', 'Cooking Accident']
        property_type = ['Residential', 'Commercial', 'Industrial']
        data = {
            'timestamp': timestamps,
            'emergency_type': np.random.choice(emergency_types, size=num_entries),
            'cause': np.random.choice(causes, size=num_entries),
            'responded': np.random.choice([True, False], size=num_entries),
            'weather': np.random.choice(['Sunny', 'Rainy', 'Foggy'], size=num_entries),
            'property_type': np.random.choice(property_type, size=num_entries),
            'barangay': np.random.choice(['Barangay 1', 'Barangay 2', 'Barangay 3'], size=num_entries)
        }
    df = pd.DataFrame(data)
    if incident_type == 'road' and lr_road:
        features = pd.get_dummies(df[['weather', 'road_condition', 'vehicle_type']]).fillna(0)
        df['predicted_cause'] = lr_road.predict(features)
    elif incident_type == 'fire' and lr_fire:
        features = pd.get_dummies(df[['weather', 'property_type']]).fillna(0)
        df['predicted_cause'] = lr_fire.predict(features)
    return df

def load_csv_data_road(file_path, time_filter):
    try:
        file_path_full = os.path.join('dataset', file_path)
        if not os.path.exists(file_path_full):
            logger.warning(f"CSV file not found: {file_path_full}. Generating mock data.")
            return generate_mock_data(time_filter, 'road')
        
        df = pd.read_csv(file_path_full)
        
        column_mapping = {
            'Date': 'Date',
            'Time': 'Time',
            'Barangay': 'Barangay',
            'Weather': 'Weather',
            'Road_Condition': 'Road_Condition',
            'Vehicle_Type': 'Vehicle_Type',
            'Accident_Type': 'Accident_Type'
        }
        
        missing_columns = [col for col in column_mapping.keys() if col not in df.columns]
        if missing_columns:
            logger.warning(f"Missing columns in {file_path}: {missing_columns}. Generating mock data.")
            return generate_mock_data(time_filter, 'road')
        
        df['timestamp'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], format='%d/%m/%Y %H:%M', errors='coerce')
        df['timestamp'] = df['timestamp'].dt.tz_localize('Asia/Manila')
        
        df.rename(columns={
            'Barangay': 'barangay',
            'Weather': 'weather',
            'Road_Condition': 'road_condition',
            'Vehicle_Type': 'vehicle_type',
            'Accident_Type': 'accident_type'
        }, inplace=True)
        
        df['emergency_type'] = 'Road Accident'
        df['responded'] = True
        
        start, end = get_time_range(time_filter)
        df = df[(df['timestamp'].notna()) & (df['timestamp'] >= start) & (df['timestamp'] <= end)]
        
        if lr_road:
            features = pd.get_dummies(df[['weather', 'road_condition', 'vehicle_type']]).fillna(0)
            df['predicted_cause'] = lr_road.predict(features)
        
        return df
    except Exception as e:
        logger.error(f"Error loading CSV {file_path}: {e}. Generating mock data.")
        return generate_mock_data(time_filter, 'road')

def load_csv_data_fire(file_path, time_filter):
    try:
        file_path_full = os.path.join('dataset', file_path)
        if not os.path.exists(file_path_full):
            logger.warning(f"CSV file not found: {file_path_full}. Generating mock data.")
            return generate_mock_data(time_filter, 'fire')
        
        df = pd.read_csv(file_path_full)
        
        column_mapping = {
            'Date': 'Date',
            'Time': 'Time',
            'Barangay': 'Barangay',
            'Weather': 'Weather',
            'Property_Type': 'Property_Type',
            'Fire_Cause': 'Fire_Cause'
        }
        
        missing_columns = [col for col in column_mapping.keys() if col not in df.columns]
        if missing_columns:
            logger.warning(f"Missing columns in {file_path}: {missing_columns}. Generating mock data.")
            return generate_mock_data(time_filter, 'fire')
        
        df['timestamp'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], format='%d/%m/%Y %H:%M', errors='coerce')
        df['timestamp'] = df['timestamp'].dt.tz_localize('Asia/Manila')
        
        df.rename(columns={
            'Barangay': 'barangay',
            'Weather': 'weather',
            'Property_Type': 'property_type',
            'Fire_Cause': 'cause'
        }, inplace=True)
        
        df['emergency_type'] = 'Fire'
        df['responded'] = True
        
        start, end = get_time_range(time_filter)
        df = df[(df['timestamp'].notna()) & (df['timestamp'] >= start) & (df['timestamp'] <= end)]
        
        if lr_fire:
            features = pd.get_dummies(df[['weather', 'property_type']]).fillna(0)
            df['predicted_cause'] = lr_fire.predict(features)
        
        return df
    except Exception as e:
        logger.error(f"Error loading CSV {file_path}: {e}. Generating mock data.")
        return generate_mock_data(time_filter, 'fire')

def get_pnp_trends(time_filter, barangay=None):
    try:
        if time_filter == 'today':
            today = datetime.now(pytz.timezone('Asia/Manila')).date()
            labels = [f"{i:02d}:00" for i in range(24)]
            total = [0] * 24
            responded = [0] * 24
            for response in today_responses:
                response_time = datetime.fromisoformat(response['timestamp'].replace('Z', '+00:00')).astimezone(pytz.timezone('Asia/Manila'))
                if response_time.date() == today and response.get('emergency_type') == 'Road Accident':
                    hour = response_time.hour
                    total[hour] += 1
                    if response.get('responded', False):
                        responded[hour] += 1
            return {'labels': labels, 'total': total, 'responded': responded}
        else:
            return generate_mock_data(time_filter, 'road')
    except Exception as e:
        logger.error(f"Error in get_pnp_trends: {e}")
        return {'labels': [], 'total': [], 'responded': []}

def get_pnp_distribution(time_filter, barangay=None):
    try:
        if time_filter == 'today':
            today = datetime.now(pytz.timezone('Asia/Manila')).date()
            distribution = Counter()
            for response in today_responses:
                response_time = datetime.fromisoformat(response['timestamp'].replace('Z', '+00:00')).astimezone(pytz.timezone('Asia/Manila'))
                if response_time.date() == today and response.get('emergency_type') == 'Road Accident':
                    emergency_type = response.get('emergency_type', 'Unknown')
                    distribution[emergency_type] += 1
            return {k: {'total': v, 'responded': sum(1 for r in today_responses if r.get('emergency_type') == k and r.get('responded', False))} for k, v in distribution.items()}
        else:
            return generate_mock_data(time_filter, 'road')['emergency_type'].value_counts().to_dict()
    except Exception as e:
        logger.error(f"Error in get_pnp_distribution: {e}")
        return {'Unknown': {'total': 0, 'responded': 0}}

def get_pnp_causes(time_filter, barangay=None):
    try:
        if time_filter == 'today':
            today = datetime.now(pytz.timezone('Asia/Manila')).date()
            road_causes = Counter()
            for response in today_responses:
                response_time = datetime.fromisoformat(response['timestamp'].replace('Z', '+00:00')).astimezone(pytz.timezone('Asia/Manila'))
                if response_time.date() == today and response.get('emergency_type') == 'Road Accident':
                    cause = response.get('road_accident_cause', 'Unknown')
                    road_causes[cause] += 1
            return {'road': dict(road_causes), 'fire': {'Unknown': 0}}
        else:
            mock_data = generate_mock_data(time_filter, 'road')
            road_causes = Counter(mock_data['cause'])
            return {'road': dict(road_causes), 'fire': {'Unknown': 0}}
    except Exception as e:
        logger.error(f"Error in get_pnp_causes: {e}")
        return {'road': {'Unknown': 0}, 'fire': {'Unknown': 0}}