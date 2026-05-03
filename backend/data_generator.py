"""
Real-time data generator for water quality parameters with anomaly injection.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import math
import random
from config import (
    BASELINE_VALUES, NOISE_LEVELS, ANOMALY_PROBABILITY,
    ANOMALY_TYPES, ANOMALY_SEVERITY
)


class WaterQualityDataGenerator:
    """Generate realistic synthetic water quality data with anomalies."""
    
    def __init__(self, seed=42):
        """
        Initialize data generator.
        
        Args:
            seed: Random seed for reproducibility
        """
        np.random.seed(seed)
        random.seed(seed)
        self.current_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.hour_counter = 0
        
    def generate_single_record(self):
        """
        Generate a single record of water quality data.
        
        Returns:
            dict: Data record with timestamp and all parameters
        """
        self.hour_counter += 1
        timestamp = self.current_time + timedelta(hours=self.hour_counter - 1)
        
        # Generate temperature with sinusoidal daily pattern
        hour_of_day = timestamp.hour
        temp_base = BASELINE_VALUES['Temperature']
        temp_sine = 3 * math.sin(2 * math.pi * hour_of_day / 24)
        temperature = temp_base + temp_sine + np.random.normal(0, NOISE_LEVELS['Temperature'])
        
        # Generate other parameters with random noise
        salinity = (BASELINE_VALUES['Salinity'] + 
                   np.random.normal(0, NOISE_LEVELS['Salinity'] * 0.5))  # Slower drift
        
        do_value = (BASELINE_VALUES['DO'] + 
                   np.random.normal(0, NOISE_LEVELS['DO']))
        
        ph_value = (BASELINE_VALUES['pH'] + 
                   np.random.normal(0, NOISE_LEVELS['pH']))
        
        alkalinity = (BASELINE_VALUES['Alkalinity'] + 
                     np.random.normal(0, NOISE_LEVELS['Alkalinity'] * 0.3))  # Slower drift
        
        # Inject anomalies
        anomaly_type = None
        if random.random() < ANOMALY_PROBABILITY:
            anomaly_type = random.choice(ANOMALY_TYPES)
            severity = np.random.uniform(
                ANOMALY_SEVERITY[anomaly_type]['min'],
                ANOMALY_SEVERITY[anomaly_type]['max']
            )
            
            if anomaly_type == 'DO_DROP':
                do_value += severity
            elif anomaly_type == 'TEMP_SPIKE':
                temperature += severity
            elif anomaly_type == 'SALINITY_DROP':
                salinity += severity
            elif anomaly_type == 'PH_SPIKE':
                ph_value += severity
        
        # Constrain values to realistic ranges
        temperature = max(20, min(40, temperature))
        salinity = max(0, min(40, salinity))
        do_value = max(0, min(15, do_value))
        ph_value = max(6, min(9, ph_value))
        alkalinity = max(0, min(300, alkalinity))
        
        record = {
            'Timestamp': timestamp,
            'Salinity': round(salinity, 2),
            'Temperature': round(temperature, 2),
            'DO': round(do_value, 2),
            'pH': round(ph_value, 2),
            'Alkalinity': round(alkalinity, 2),
            'Anomaly': anomaly_type
        }
        
        return record
    
    def generate_batch(self, num_records):
        """
        Generate multiple records.
        
        Args:
            num_records: Number of records to generate
            
        Returns:
            pd.DataFrame: DataFrame with generated records
        """
        records = []
        for _ in range(num_records):
            records.append(self.generate_single_record())
        
        return pd.DataFrame(records)
    
    def generate_historical_data(self, num_hours=720):
        """
        Generate historical data for initial training.
        
        Args:
            num_hours: Number of hours of history to generate (default 30 days)
            
        Returns:
            pd.DataFrame: Historical data
        """
        # Reset hour counter
        self.hour_counter = 0
        self.current_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(hours=num_hours)
        
        return self.generate_batch(num_hours)
