import joblib
import os
import logging
import pandas as pd

logger = logging.getLogger(__name__)

road_accident_df = pd.DataFrame()
try:
    road_accident_df = pd.read_csv(os.path.join(os.path.dirname(__file__), 'dataset', 'road_accident.csv'))
    logger.info("Successfully loaded road_accident.csv")
except FileNotFoundError:
    logger.error("road_accident.csv not found in dataset directory")
except Exception as e:
    logger.error(f"Error loading road_accident.csv: {e}")
    
fire_incident_df = pd.DataFrame()
try:
    fire_incident_df = pd.read_csv(os.path.join(os.path.dirname(__file__), 'dataset', 'fire_incident.csv'))
    logger.info("Successfully loaded fire_incident.csv")
except FileNotFoundError:
    logger.error("fire_incident.csv not found in dataset directory")
except Exception as e:
    logger.error(f"Error loading fire_incident.csv: {e}")
    
health_emergencies_df = pd.DataFrame()
try:
    health_emergencies_df = pd.read_csv(os.path.join(os.path.dirname(__file__), 'dataset', 'health_emergencies.csv'))
    logger.info("Successfully loaded fire_incident.csv")
except FileNotFoundError:
    logger.error("fire_incident.csv not found in dataset directory")
except Exception as e:
    logger.error(f"Error loading fire_incident.csv: {e}")
    
crime_df = pd.DataFrame()
try:
    health_emergencies_df = pd.read_csv(os.path.join(os.path.dirname(__file__), 'dataset', 'crime_emergencies.csv'))
    logger.info("Successfully loaded crime_emergencies.csv")
except FileNotFoundError:
    logger.error("crime_emergencies.csv not found in dataset directory")
except Exception as e:
    logger.error(f"Error loading crime_emergencies.csv: {e}")