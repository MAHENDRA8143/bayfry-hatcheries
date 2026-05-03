"""
Configuration file for Smart Prawn Hatchery Water Quality Prediction System
"""

import os
from datetime import datetime

# ============================================================================
# PROJECT CONFIGURATION
# ============================================================================

PROJECT_NAME = "AI-Based Smart Prawn Hatchery Water Quality Prediction System"
PROJECT_VERSION = "1.0.0"

# ============================================================================
# DATA GENERATION PARAMETERS
# ============================================================================

# Baseline values for each parameter
BASELINE_VALUES = {
    'Salinity': 18.0,      # ppt
    'Temperature': 29.0,   # °C
    'DO': 7.5,             # mg/L
    'pH': 8.0,
    'Alkalinity': 120.0    # mg/L
}

# Standard deviations for normal variation
NOISE_LEVELS = {
    'Salinity': 0.3,
    'Temperature': 0.5,
    'DO': 0.8,
    'pH': 0.15,
    'Alkalinity': 5.0
}

# Anomaly parameters
ANOMALY_PROBABILITY = 0.05  # 5% chance of anomaly each hour
ANOMALY_TYPES = ['DO_DROP', 'TEMP_SPIKE', 'SALINITY_DROP', 'PH_SPIKE']
ANOMALY_SEVERITY = {
    'DO_DROP': {'min': -4.0, 'max': -2.0},
    'TEMP_SPIKE': {'min': 2.0, 'max': 6.0},
    'SALINITY_DROP': {'min': -3.0, 'max': -1.0},
    'PH_SPIKE': {'min': -1.0, 'max': 1.0}
}

# ============================================================================
# SAFETY THRESHOLDS
# ============================================================================

SAFE_RANGES = {
    'Salinity': {'min': 10.0, 'max': 25.0},      # ppt
    'Temperature': {'min': 26.0, 'max': 32.0},   # °C
    'DO': {'min': 5.0, 'max': 15.0},             # mg/L
    'pH': {'min': 7.5, 'max': 8.5},
    'Alkalinity': {'min': 80.0, 'max': 150.0}    # mg/L
}

# Alert thresholds (deviation from safe range)
ALERT_THRESHOLDS = {
    'WARNING': 0.15,   # 15% beyond limit
    'CRITICAL': 0.25   # 25% beyond limit
}

# ============================================================================
# DATA PROCESSING PARAMETERS
# ============================================================================

LAG_FEATURES = [1, 2, 3, 6, 12]  # Hours to lag
ROLLING_WINDOW = 12  # 12-hour rolling window
NORMALIZATION_METHOD = 'minmax'  # 'minmax' or 'zscore'

# ============================================================================
# MODEL PARAMETERS
# ============================================================================

# Random Forest
RF_PARAMS = {
    'n_estimators': 100,
    'max_depth': 15,
    'min_samples_split': 5,
    'min_samples_leaf': 2,
    'random_state': 42,
    'n_jobs': -1
}

# LSTM
LSTM_PARAMS = {
    'sequence_length': 24,  # 24 hours of history
    'lstm_units': 64,
    'dense_units': 32,
    'dropout_rate': 0.2,
    'epochs': 50,
    'batch_size': 32,
    'validation_split': 0.2,
    'random_state': 42
}

# ARIMA
ARIMA_PARAMS = {
    'order': (5, 1, 2),  # (p, d, q)
    'seasonal_order': (0, 0, 0, 0)
}

# ============================================================================
# ENSEMBLE PARAMETERS
# ============================================================================

MODEL_WEIGHTS = {
    'random_forest': 0.5,  # 50% weight
    'lstm': 0.3,           # 30% weight
    'arima': 0.2           # 20% weight
}

# ============================================================================
# SIMULATION PARAMETERS
# ============================================================================

SIMULATION_HOUR_INTERVAL = 1  # seconds (for demo; production would be 3600)
PREDICTION_HORIZON = 24  # Predict next 24 hours
HISTORY_RETENTION = 720  # Keep 30 days of data (720 hours)

# ============================================================================
# OUTPUT PARAMETERS
# ============================================================================

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'outputs')
GRAPHS_DIR = os.path.join(OUTPUT_DIR, 'graphs')
DATA_DIR = os.path.join(OUTPUT_DIR, 'data')

# Graph parameters
GRAPH_DPI = 300
GRAPH_FORMAT = 'png'
GRAPH_FIGSIZE = (14, 8)

# ============================================================================
# LOGGING PARAMETERS
# ============================================================================

LOG_DIR = os.path.join(OUTPUT_DIR, 'logs')
LOG_LEVEL = 'INFO'

# Ensure directories exist
for directory in [OUTPUT_DIR, GRAPHS_DIR, DATA_DIR, LOG_DIR]:
    os.makedirs(directory, exist_ok=True)
