import pandas as pd
import os
import random
from datetime import datetime, timedelta
import pytz
from collections import Counter
import logging
from models import lr_road, lr_fire

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

def generate_mock_data(time_filter, emergency_type):
    try:
        num_records = {'daily': 50, 'weekly': 100, 'monthly': 200, 'yearly': 500}.get(time_filter, 100)
        data = []
        causes = ['Overspeeding', 'Drunk Driving', 'Reckless Driving', 'Overloading', 'Fatigue', 'Distracted Driving', 'Poor Maintenance', 'Mechanical Failure', 'Inexperience', 'Unknown']
        weathers = ['Sunny', 'Rainy', 'Foggy', 'Cloudy']
        road_conditions = ['Dry', 'Wet', 'Icy', 'Snowy']
        vehicle_types = ['Car', 'Motorcycle', 'Truck', 'Bus']
        accident_types = ['Head-on collision', 'Rear-end collision', 'Side-impact collision', 'Single vehicle accident', 'Pedestrian accident']
        property_types = ['Residential', 'Commercial', 'Industrial']
        fire_causes = ['Electrical', 'Arson', 'Gas Leak', 'Unknown']
        driver_ages = ['18-25', '26-35', '36-50', '51+']
        driver_genders = ['Male', 'Female']
        for _ in range(num_records):
            timestamp = (datetime.now(pytz.timezone('Asia/Manila')) - timedelta(days=random.randint(0, 365 if time_filter == 'yearly' else 30 if time_filter == 'monthly' else 7 if time_filter == 'weekly' else 1))).isoformat()
            record = {
                'emergency_type': emergency_type,
                'timestamp': timestamp,
                'responded': random.choice([True, False]),
                'barangay': random.choice(['Barangay 1', 'Barangay 2', 'Barangay 3']),
                'weather': random.choice(weathers),
                'road_condition': random.choice(road_conditions),
                'vehicle_type': random.choice(vehicle_types),
                'accident_type': random.choice(accident_types) if emergency_type == 'road' else None,
                'cause': random.choice(causes) if emergency_type == 'road' else random.choice(fire_causes),
                'property_type': random.choice(property_types) if emergency_type == 'fire' else None,
                'driver_age': random.choice(driver_ages) if emergency_type == 'road' else None,
                'driver_gender': random.choice(driver_genders) if emergency_type == 'road' else None
            }
            data.append(record)
        return data
    except Exception as e:
        logger.error(f"Error in generate_mock_data: {e}")
        return []

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
            mock_data = generate_mock_data(time_filter, 'road')
            labels = [f"{i:02d}:00" for i in range(24)] if time_filter == 'daily' else list(range(1, 32)) if time_filter == 'monthly' else ['Week ' + str(i) for i in range(1, 5)] if time_filter == 'weekly' else ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            total = [0] * len(labels)
            responded = [0] * len(labels)
            for record in mock_data:
                if record.get('emergency_type') == 'Road Accident':
                    timestamp = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00')).astimezone(pytz.timezone('Asia/Manila'))
                    index = timestamp.hour if time_filter == 'daily' else timestamp.day - 1 if time_filter == 'monthly' else (timestamp.day - 1) // 7 if time_filter == 'weekly' else timestamp.month - 1
                    index = min(index, len(labels) - 1)
                    total[index] += 1
                    if record.get('responded', False):
                        responded[index] += 1
            return {'labels': labels, 'total': total, 'responded': responded}
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
            mock_data = generate_mock_data(time_filter, 'road')
            distribution = Counter(r.get('emergency_type', 'Unknown') for r in mock_data)
            return {k: {'total': v, 'responded': sum(1 for r in mock_data if r.get('emergency_type') == k and r.get('responded', False))} for k, v in distribution.items()}
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
            road_causes = Counter(r.get('cause', 'Unknown') for r in mock_data)
            return {'road': dict(road_causes), 'fire': {'Unknown': 0}}
    except Exception as e:
        logger.error(f"Error in get_pnp_causes: {e}")
        return {'road': {'Unknown': 0}, 'fire': {'Unknown': 0}}

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
        
        return df.to_dict(orient='records')
    except Exception as e:
        logger.error(f"Error loading CSV {file_path}: {e}. Generating mock data.")
        return generate_mock_data(time_filter, 'fire')