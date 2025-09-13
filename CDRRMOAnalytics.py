from collections import Counter
from datetime import datetime, timedelta
import pytz
import pandas as pd
import os
import logging
import random
from models import lr_road, lr_fire
import json

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_time_range(time_filter):
    manila_tz = pytz.timezone('Asia/Manila')
    now = datetime.now(manila_tz)
    if time_filter == 'today':
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif time_filter == 'daily':
        start = now - timedelta(days=1)
        end = now
    elif time_filter == 'weekly':
        start = now - timedelta(days=7)
        end = now
    elif time_filter == 'monthly':
        start = now - timedelta(days=30)
        end = now
    else:  # yearly
        start = now - timedelta(days=365)
        end = now
    return start, end

def generate_mock_data(time_filter, emergency_type):
    try:
        start, end = get_time_range(time_filter)
        num_records = {'today': 10, 'daily': 50, 'weekly': 100, 'monthly': 300, 'yearly': 1000}.get(time_filter, 10)
        data = []
        for _ in range(num_records):
            record = {
                'timestamp': (start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))).isoformat(),
                'emergency_type': emergency_type,
                'barangay': random.choice(['Barangay 1', 'Barangay 2', 'Barangay 3']),
                'municipality': 'Unknown',
                'role': 'cdrrmo',
                'responded': random.choice([True, False])
            }
            if emergency_type == 'road':
                record.update({
                    'weather': random.choice(['Sunny', 'Rainy', 'Foggy', 'Cloudy']),
                    'road_condition': random.choice(['Dry', 'Wet', 'Icy', 'Snowy']),
                    'vehicle_type': random.choice(['Car', 'Motorcycle', 'Truck', 'Bus']),
                    'driver_age': random.choice(['18-25', '26-35', '36-50', '51+']),
                    'driver_gender': random.choice(['Male', 'Female']),
                    'road_accident_type': random.choice(['Head-on collision', 'Rear-end collision', 'Side-impact collision', 'Single vehicle accident', 'Pedestrian accident']),
                    'cause': random.choice(['Overspeeding', 'Drunk Driving', 'Reckless Driving', 'Overloading', 'Fatigue', 'Distracted Driving', 'Poor Maintenance', 'Mechanical Failure', 'Inexperience']),
                    'injuries': random.randint(0, 5),
                    'fatalities': random.randint(0, 2)
                })
            elif emergency_type == 'fire':
                record.update({
                    'weather': random.choice(['Sunny', 'Rainy', 'Foggy', 'Cloudy']),
                    'property_type': random.choice(['Residential', 'Commercial', 'Industrial', 'Other']),
                    'cause': random.choice(['Electrical', 'Arson', 'Accidental', 'Unknown'])
                })
            data.append(record)
        return data
    except Exception as e:
        logger.error(f"Error generating mock data: {e}")
        return []

def get_cdrrmo_trends(time_filter, municipality=None):
    try:
        if time_filter == 'today':
            today = datetime.now(pytz.timezone('Asia/Manila')).date()
            hours = [f"{i:02d}:00" for i in range(24)]
            total = [0] * 24
            responded = [0] * 24
            from AlertNow import today_responses
            for response in today_responses:
                response_time = datetime.fromisoformat(response.get('timestamp', '').replace('Z', '+00:00')).astimezone(pytz.timezone('Asia/Manila'))
                if response_time.date() == today and response.get('municipality', '').lower() == municipality.lower() and response.get('role', '').lower() == 'cdrrmo':
                    hour = response_time.hour
                    total[hour] += 1
                    if response.get('responded', False):
                        responded[hour] += 1
            return {'labels': hours, 'total': total, 'responded': responded}
        else:
            mock_data = generate_mock_data(time_filter, 'road') + generate_mock_data(time_filter, 'fire')
            hours = [f"{i:02d}:00" for i in range(24)]
            total = [0] * 24
            responded = [0] * 24
            for record in mock_data:
                if isinstance(response, str):
                    try:
                        response = json.loads(response)
                    except json.JSONDecodeError:
                        logger.warning(f"Skipping invalid JSON response: {response}")
                        continue
                if record.get('municipality', '').lower() == municipality.lower() and record.get('role', '').lower() == 'cdrrmo':
                    record_time = datetime.fromisoformat(record.get('timestamp', '').replace('Z', '+00:00')).astimezone(pytz.timezone('Asia/Manila'))
                    hour = record_time.hour
                    total[hour] += 1
                    if record.get('responded', False):
                        responded[hour] += 1
            return {'labels': hours, 'total': total, 'responded': responded}
    except Exception as e:
        logger.error(f"Error in get_cdrrmo_trends: {e}")
        return {'labels': [f"{i:02d}:00" for i in range(24)], 'total': [0] * 24, 'responded': [0] * 24}

def get_cdrrmo_distribution(time_filter, municipality=None):
    try:
        if time_filter == 'today':
            from AlertNow import today_responses
            distribution = Counter(response.get('emergency_type', 'Unknown') for response in today_responses if response.get('municipality', '').lower() == municipality.lower() and response.get('role', '').lower() == 'cdrrmo')
            return {k: {'total': v, 'responded': sum(1 for r in today_responses if r.get('emergency_type', '') == k and r.get('municipality', '').lower() == municipality.lower() and r.get('role', '').lower() == 'cdrrmo' and r.get('responded', False))} for k, v in distribution.items()}
        else:
            mock_data = generate_mock_data(time_filter, 'road') + generate_mock_data(time_filter, 'fire')
            distribution = Counter(record.get('emergency_type', 'Unknown') for record in mock_data if record.get('municipality', '').lower() == municipality.lower() and record.get('role', '').lower() == 'cdrrmo')
            return {k: {'total': v, 'responded': sum(1 for r in mock_data if r.get('emergency_type', '') == k and r.get('municipality', '').lower() == municipality.lower() and r.get('role', '').lower() == 'cdrrmo' and r.get('responded', False))} for k, v in distribution.items()}
    except Exception as e:
        logger.error(f"Error in get_cdrrmo_distribution: {e}")
        return {'Unknown': {'total': 0, 'responded': 0}}

def get_cdrrmo_causes(time_filter, municipality=None):
    try:
        if time_filter == 'today':
            today = datetime.now(pytz.timezone('Asia/Manila')).date()
            road_causes = Counter()
            fire_causes = Counter()
            from AlertNow import today_responses
            for response in today_responses:
                response_time = datetime.fromisoformat(response.get('timestamp', '').replace('Z', '+00:00')).astimezone(pytz.timezone('Asia/Manila'))
                if response_time.date() == today and response.get('municipality', '').lower() == municipality.lower() and response.get('role', '').lower() == 'cdrrmo':
                    if response.get('emergency_type', '') == 'Road Accident':
                        cause = response.get('cause', 'Unknown')
                        road_causes[cause] += 1
                    elif response.get('emergency_type', '') == 'Fire':
                        cause = response.get('cause', 'Unknown')
                        fire_causes[cause] += 1
            return {'road': dict(road_causes), 'fire': dict(fire_causes)}
        else:
            mock_data = generate_mock_data(time_filter, 'road') + generate_mock_data(time_filter, 'fire')
            road_causes = Counter()
            fire_causes = Counter()
            for record in mock_data:
                if isinstance(response, str):
                    try:
                        response = json.loads(response)
                    except json.JSONDecodeError:
                        logger.warning(f"Skipping invalid JSON response: {response}")
                        continue
                if record.get('municipality', '').lower() == municipality.lower() and record.get('role', '').lower() == 'cdrrmo':
                    if record.get('emergency_type', '') == 'Road Accident':
                        cause = record.get('cause', 'Unknown')
                        road_causes[cause] += 1
                    elif record.get('emergency_type', '') == 'Fire':
                        cause = record.get('cause', 'Unknown')
                        fire_causes[cause] += 1
            return {'road': dict(road_causes), 'fire': dict(fire_causes)}
    except Exception as e:
        logger.error(f"Error in get_cdrrmo_causes: {e}")
        return {'road': {'Unknown': 0}, 'fire': {'Unknown': 0}}

def load_csv_data_road(file_path, time_filter):
    try:
        file_path_full = os.path.join('dataset', file_path)
        if not os.path.exists(file_path_full):
            logger.info(f"CSV file not found: {file_path_full}. Generating mock data.")
            return generate_mock_data(time_filter, 'road')
        
        df = pd.read_csv(file_path_full)
        if df.empty:
            logger.info(f"CSV file {file_path} is empty. Generating mock data.")
            return generate_mock_data(time_filter, 'road')
        
        column_mapping = {
            'Date': 'Date', 'Time': 'Time', 'Barangay': 'Barangay', 'Weather': 'Weather',
            'Road_Condition': 'Road_Condition', 'Vehicle_Type': 'Vehicle_Type',
            'Accident_Cause': 'Accident_Cause', 'Road_Accident_Type': 'Road_Accident_Type',
            'Latitude': 'Latitude', 'Longitude': 'Longitude',
            'Day_of_Week': 'Day_of_Week', 'Injuries': 'Injuries', 'Fatalities': 'Fatalities',
            'Driver_Age': 'Driver_Age', 'Driver_Gender': 'Driver_Gender'
        }
        
        missing_columns = [col for col in column_mapping.keys() if col not in df.columns]
        if missing_columns:
            logger.info(f"Missing columns in {file_path}: {missing_columns}. Generating mock data.")
            return generate_mock_data(time_filter, 'road')
        
        df['timestamp'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], format='%d/%m/%Y %H:%M', errors='coerce')
        df['timestamp'] = df['timestamp'].dt.tz_localize('Asia/Manila')
        
        df.rename(columns={
            'Barangay': 'barangay',
            'Weather': 'weather',
            'Road_Condition': 'road_condition',
            'Vehicle_Type': 'vehicle_type',
            'Accident_Cause': 'cause',
            'Road_Accident_Type': 'road_accident_type',
            'Latitude': 'latitude',
            'Longitude': 'longitude',
            'Day_of_Week': 'day_of_week',
            'Injuries': 'injuries',
            'Fatalities': 'fatalities',
            'Driver_Age': 'driver_age',
            'Driver_Gender': 'driver_gender'
        }, inplace=True)
        
        df['emergency_type'] = 'Road Accident'
        df['responded'] = True
        
        start, end = get_time_range(time_filter)
        df = df[(df['timestamp'].notna()) & (df['timestamp'] >= start) & (df['timestamp'] <= end)]
        
        if lr_road:
            features = pd.get_dummies(df[['weather', 'road_condition', 'vehicle_type', 'driver_age', 'driver_gender']]).fillna(0)
            df['predicted_cause'] = lr_road.predict(features)
        
        return df.to_dict(orient='records')
    except Exception as e:
        logger.info(f"Failed to load CSV {file_path}: {e}. Generating mock data.")
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
        
        return df.to_dict(orient='records')
    except Exception as e:
        logger.error(f"Error loading CSV {file_path}: {e}. Generating mock data.")
        return generate_mock_data(time_filter, 'fire')