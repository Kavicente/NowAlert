import joblib
import os
import logging

logger = logging.getLogger(__name__)


#ARIMA MODEL

arima_m = None
try:
    arima_m = joblib.load(os.path.join(os.path.dirname(__file__), 'training', 'Road Models', 
                                       'ARIMA_ROAD', 'arima_monthly', 'monthly_arima70_15_15.pkl'))
    logger.info("monthly_arima70_15_15.pkl loaded successfully.")
except FileNotFoundError:
    logger.error("monthly_arima70_15_15.pkl not found.")
except Exception as e:
    logger.error(f"Error loading monthly_arima70_15_15.pkl: {e}")

arima_22 = None
try:
    arima_22 = joblib.load(os.path.join(os.path.dirname(__file__), 'training', 'Road Models', 
                                        'ARIMA_ROAD', 'arima_forecast', 'forecast_70_15_15.pkl'))
    logger.info("forecast_70_15_15.pkl loaded successfully.")
except FileNotFoundError:
    logger.error("forecast_70_15_15.pkl not found.")
except Exception as e:
    logger.error(f"Error loading forecast_70_15_15.pkl: {e}")

arima_pred = None
try:
    arima_pred = joblib.load(os.path.join(os.path.dirname(__file__), 'training', 'Road Models', 
                                          'ARIMA_ROAD', 'arima_pred', 'arima80_20.pkl'))
    logger.info("arima80_20.pkl loaded successfully.")
except FileNotFoundError:
    logger.error("arima80_20.pkl not found.")
except Exception as e:
    logger.error(f"Error loading arima80_20.pkl: {e}")
    
#ARIMAX MODEL  
    
arimax_m = None
try:
    arimax_m = joblib.load(os.path.join(os.path.dirname(__file__), 'training', 'Road Models', 
                                       'ARIMAX ROAD', 'arimax_monthly', 'monthly_arimax80_20.pkl'))
    logger.info("monthly_arimax70_15_15.pkl loaded successfully.")
except FileNotFoundError:
    logger.error("monthly_arimax70_15_15.pkl not found.")
except Exception as e:
    logger.error(f"Error loading monthly_arimax70_15_15.pkl: {e}")

arimax_22 = None
try:
    arimax_22 = joblib.load(os.path.join(os.path.dirname(__file__), 'training', 'Road Models', 
                                        'ARIMAX ROAD', 'arimax_forecast', 'arimax_forecast_80_20.pkl'))
    logger.info("arimax_forecast_70_15_15.pkl loaded successfully.")
except FileNotFoundError:
    logger.error("arimax_forecast_70_15_15.pkl not found.")
except Exception as e:
    logger.error(f"Error loading arimax_forecast_70_15_15.pkl: {e}")

arimax_pred = None
try:
    arimax_pred = joblib.load(os.path.join(os.path.dirname(__file__), 'training', 'Road Models', 
                                          'ARIMAX ROAD', 'arimax_pred', 'arimax70_15_15.pkl'))
    logger.info("arimax70_30.pkl loaded successfully.")
except FileNotFoundError:
    logger.error("arimax70_30.pkl not found.")
except Exception as e:
    logger.error(f"Error loading arimax70_30.pkl: {e}")
    

#SARIMA MODEL

sarima_m = None
try:
    sarima_m = joblib.load(os.path.join(os.path.dirname(__file__), 'training', 'Road Models', 
                                       'SARIMA ROAD', 'sarima_monthly', 'monthly_sarima70_15_15.pkl'))
    logger.info("monthly_sarima70_15_15.pkl loaded successfully.")
except FileNotFoundError:
    logger.error("monthly_sarima70_15_15.pkl not found.")
except Exception as e:
    logger.error(f"Error loading monthly_sarima70_15_15.pkl: {e}")

sarima_22 = None
try:
    sarima_22 = joblib.load(os.path.join(os.path.dirname(__file__), 'training', 'Road Models', 
                                        'SARIMA ROAD', 'sarima_forecast', 'sarima_forecast_70_15_15.pkl'))
    logger.info("sarima_forecast_70_15_15.pkl loaded successfully.")
except FileNotFoundError:
    logger.error("sarima_forecast_70_15_15.pkl not found.")
except Exception as e:
    logger.error(f"Error loading sarima_forecast_70_15_15.pkl: {e}")

sarima_pred = None
try:
    sarima_pred = joblib.load(os.path.join(os.path.dirname(__file__), 'training', 'Road Models', 
                                          'SARIMA ROAD', 'sarima_pred', 'sarima70_15_15.pkl'))
    logger.info("sarima80_20.pkl loaded successfully.")
except FileNotFoundError:
    logger.error("sarima80_20.pkl not found.")
except Exception as e:
    logger.error(f"Error loading sarima80_20.pkl: {e}")
    
#SARIMAX MODEL

sarimax_m = None
try:
    sarimax_m = joblib.load(os.path.join(os.path.dirname(__file__), 'training', 'Road Models', 
                                       'SARIMAX ROAD', 'sarimax_monthly', 'monthly_sarimax70_15_15.pkl'))
    logger.info("monthly_sarimax70_15_15.pkl loaded successfully.")
except FileNotFoundError:
    logger.error("monthly_sarimax70_15_15.pkl not found.")
except Exception as e:
    logger.error(f"Error loading monthly_sarimax70_15_15.pkl: {e}")

sarimax_22 = None
try:
    sarimax_22 = joblib.load(os.path.join(os.path.dirname(__file__), 'training', 'Road Models', 
                                        'SARIMAX ROAD', 'sarimax_forecast', 'sarimax_forecast_70_15_15.pkl'))
    logger.info("sarimax_forecast_70_15_15.pkl loaded successfully.")
except FileNotFoundError:
    logger.error("sarimax_forecast_70_15_15.pkl not found.")
except Exception as e:
    logger.error(f"Error loading sarimax_forecast_70_15_15.pkl: {e}")

sarimax_pred = None
try:
    sarimax_pred = joblib.load(os.path.join(os.path.dirname(__file__), 'training', 'Road Models', 
                                          'SARIMAX ROAD', 'sarimax_pred', 'sarimax80_20.pkl'))
    logger.info("sarimax80_20.pkl loaded successfully.")
except FileNotFoundError:
    logger.error("sarimax80_20.pkl not found.")
except Exception as e:
    logger.error(f"Error loading sarimax80_20.pkl: {e}")