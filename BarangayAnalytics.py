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
            logger.info("CSV file not found: {}. Generating mock data.".format(file_path_full))
            return generate_mock_data(time_filter, 'road')
        
        df = pd.read_csv(file_path_full)
        if df.empty:
            logger.info("CSV file {} is empty. Generating mock data.".format(file_path))
            return generate_mock_data(time_filter, 'road')
        
        column_mapping = {
            'Date': 'Date', 'Time': 'Time', 'Barangay': 'Barangay', 'Weather': 'Weather',
            'Road_Condition': 'Road_Condition', 'Vehicle_Type': 'Vehicle_Type',
            'Accident_Cause': 'Accident_Cause', 'Road_Accident_Type': 'Road_Accident_Type', 'Latitude': 'Latitude', 'Longitude': 'Longitude',
            'Day_of_Week': 'Day_of_Week', 'Injuries': 'Injuries', 'Fatalities': 'Fatalities',
            'Driver_Age': 'Driver_Age', 'Driver_Gender': 'Driver_Gender'
        }
        
        missing_columns = [col for col in column_mapping.keys() if col not in df.columns]
        if missing_columns:
            logger.info("Missing columns in {}: {}. Generating mock data.".format(file_path, missing_columns))
            return generate_mock_data(time_filter, 'road')
        
        # Proceed with processing (timestamp creation, renaming, filtering, etc.)
        df['timestamp'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], format='%d/%m/%Y %H:%M', errors='coerce')
        df['timestamp'] = df['timestamp'].dt.tz_localize('Asia/Manila')
        # ... rest of the function ...
        
        return df
    except Exception as e:
        logger.info("Failed to load CSV {}: {}. Generating mock data.".format(file_path, e))
        return generate_mock_data(time_filter, 'road')

def load_csv_data_fire(file_path, time_filter):
    try:
        file_path_full = os.path.join('dataset', file_path)
        if not os.path.exists(file_path_full):
            logger.warning(f"CSV file not found: {file_path_full}. Generating mock data.")
            return generate_mock_data(time_filter, 'fire')
        
        df = pd.read_csv(file_path_full)
        
        # Define expected columns and map them
        column_mapping = {
            'Date': 'Date',
            'Time': 'Time',
            'Barangay': 'Barangay',
            'Weather': 'Weather',
            'Property_Type': 'Property_Type',
            'Fire_Cause': 'Fire_Cause',
            'Latitude': 'Latitude',
            'Longitude': 'Longitude',
            'Day_of_Week': 'Day_of_Week',
            'Fire_Severity': 'Fire_Severity',
            'Casualty_Count': 'Casualty_Count',
            'Response_Time': 'Response_Time',
            'Fire_Duration': 'Fire_Duration'
        }
        
        missing_columns = [col for col in column_mapping.keys() if col not in df.columns]
        if missing_columns:
            logger.warning(f"Missing columns in {file_path}: {missing_columns}. Generating mock data.")
            return generate_mock_data(time_filter, 'fire')
        
        # Create timezone-aware timestamp
        df['timestamp'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], format='%d/%m/%Y %H:%M', errors='coerce')
        df['timestamp'] = df['timestamp'].dt.tz_localize('Asia/Manila')
        
        # Rename columns to standardized names
        df.rename(columns={
            'Barangay': 'barangay',
            'Weather': 'weather',
            'Property_Type': 'property_type',
            'Fire_Cause': 'cause',
            'Latitude': 'latitude',
            'Longitude': 'longitude',
            'Day_of_Week': 'day_of_week',
            'Fire_Severity': 'fire_severity',
            'Casualty_Count': 'casualty_count',
            'Response_Time': 'response_time',
            'Fire_Duration': 'fire_duration'
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

def get_barangay_trends(time_filter, barangay=None):
    try:
        if time_filter == 'today':
            today = datetime.now(pytz.timezone('Asia/Manila')).date()
            hours = [f"{i:02d}:00" for i in range(24)]
            total = [0] * 24
            responded = [0] * 24
            from AlertNow import today_responses
            for response in today_responses:
                response_time = datetime.fromisoformat(response.get('timestamp', '').replace('Z', '+00:00')).astimezone(pytz.timezone('Asia/Manila'))
                if response_time.date() == today and response.get('barangay', '').lower() == barangay.lower():
                    hour = response_time.hour
                    total[hour] += 1
                    if response.get('responded', False):
                        responded[hour] += 1
            return {'labels': hours, 'total': total, 'responded': responded}
        else:
            mock_data = generate_mock_data(time_filter, 'road')
            hours = [f"{i:02d}:00" for i in range(24)]
            total = [0] * 24
            responded = [0] * 24
            for record in mock_data:
                if record.get('barangay', '').lower() == barangay.lower():
                    record_time = datetime.fromisoformat(record.get('timestamp', '').replace('Z', '+00:00')).astimezone(pytz.timezone('Asia/Manila'))
                    hour = record_time.hour
                    total[hour] += 1
                    if record.get('responded', False):
                        responded[hour] += 1
            return {'labels': hours, 'total': total, 'responded': responded}
    except Exception as e:
        logger.error(f"Error in get_barangay_trends: {e}")
        return {'labels': [f"{i:02d}:00" for i in range(24)], 'total': [0] * 24, 'responded': [0] * 24}

def get_barangay_distribution(time_filter, barangay=None):
    try:
        if time_filter == 'today':
            from AlertNow import today_responses
            distribution = Counter(response.get('emergency_type', 'Unknown') for response in today_responses if response.get('barangay', '').lower() == barangay.lower())
            return {k: {'total': v, 'responded': sum(1 for r in today_responses if r.get('emergency_type', '') == k and r.get('barangay', '').lower() == barangay.lower() and r.get('responded', False))} for k, v in distribution.items()}
        else:
            mock_data = generate_mock_data(time_filter, 'road')
            distribution = Counter(record.get('emergency_type', 'Unknown') for record in mock_data if record.get('barangay', '').lower() == barangay.lower())
            return {k: {'total': v, 'responded': sum(1 for r in mock_data if r.get('emergency_type', '') == k and r.get('barangay', '').lower() == barangay.lower() and r.get('responded', False))} for k, v in distribution.items()}
    except Exception as e:
        logger.error(f"Error in get_barangay_distribution: {e}")
        return {'Unknown': {'total': 0, 'responded': 0}}

def get_barangay_causes(time_filter, barangay=None):
    try:
        if time_filter == 'today':
            today = datetime.now(pytz.timezone('Asia/Manila')).date()
            road_causes = Counter()
            fire_causes = Counter()
            from AlertNow import today_responses
            for response in today_responses:
                response_time = datetime.fromisoformat(response.get('timestamp', '').replace('Z', '+00:00')).astimezone(pytz.timezone('Asia/Manila'))
                if response_time.date() == today and response.get('barangay', '').lower() == barangay.lower():
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
                if record.get('barangay', '').lower() == barangay.lower():
                    if record.get('emergency_type', '') == 'Road Accident':
                        cause = record.get('cause', 'Unknown')
                        road_causes[cause] += 1
                    elif record.get('emergency_type', '') == 'Fire':
                        cause = record.get('cause', 'Unknown')
                        fire_causes[cause] += 1
            return {'road': dict(road_causes), 'fire': dict(fire_causes)}
    except Exception as e:
        logger.error(f"Error in get_barangay_causes: {e}")
        return {'road': {'Unknown': 0}, 'fire': {'Unknown': 0}}