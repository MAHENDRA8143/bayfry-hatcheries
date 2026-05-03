"""
Alert system for monitoring water quality and triggering warnings.
"""

import pandas as pd
from enum import Enum
from datetime import datetime
from config import SAFE_RANGES, ALERT_THRESHOLDS


class AlertLevel(Enum):
    """Alert severity levels."""
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AlertSystem:
    """Monitor water quality and generate alerts."""
    
    def __init__(self):
        """Initialize alert system."""
        self.parameters = ['Salinity', 'Temperature', 'DO', 'pH', 'Alkalinity']
        self.alert_history = []
        
    def check_parameter(self, parameter, value):
        """
        Check if parameter value is within safe range.
        
        Args:
            parameter: Parameter name
            value: Current value
            
        Returns:
            tuple: (AlertLevel, description)
        """
        if parameter not in SAFE_RANGES:
            return AlertLevel.NORMAL, "Unknown parameter"
        
        safe_range = SAFE_RANGES[parameter]
        min_val = safe_range['min']
        max_val = safe_range['max']
        range_width = max_val - min_val
        
        # Check if value is within safe range
        if min_val <= value <= max_val:
            return AlertLevel.NORMAL, f"{parameter}: {value:.2f} (Normal)"
        
        # Calculate deviation percentage
        if value < min_val:
            deviation = (min_val - value) / range_width
            description = f"{parameter}: {value:.2f} (Below minimum {min_val})"
        else:
            deviation = (value - max_val) / range_width
            description = f"{parameter}: {value:.2f} (Above maximum {max_val})"
        
        # Determine alert level based on deviation
        if deviation >= ALERT_THRESHOLDS['CRITICAL']:
            return AlertLevel.CRITICAL, description
        elif deviation >= ALERT_THRESHOLDS['WARNING']:
            return AlertLevel.WARNING, description
        else:
            return AlertLevel.NORMAL, description
    
    def check_all_parameters(self, data_dict):
        """
        Check all parameters and generate alerts.
        
        Args:
            data_dict: Dictionary with parameter values
            
        Returns:
            dict: Alert status for all parameters
        """
        alerts = {
            'timestamp': datetime.now(),
            'overall_level': AlertLevel.NORMAL,
            'parameters': {}
        }
        
        max_level = AlertLevel.NORMAL
        
        for param in self.parameters:
            if param in data_dict:
                level, description = self.check_parameter(param, data_dict[param])
                alerts['parameters'][param] = {
                    'level': level,
                    'description': description,
                    'value': data_dict[param]
                }
                
                # Update overall alert level (highest severity)
                if level.value == 'CRITICAL':
                    max_level = AlertLevel.CRITICAL
                elif level.value == 'WARNING' and max_level.value != 'CRITICAL':
                    max_level = AlertLevel.WARNING
        
        alerts['overall_level'] = max_level
        self.alert_history.append(alerts)
        
        return alerts
    
    def check_predicted_values(self, predictions_df):
        """
        Check predicted values for future anomalies.
        
        Args:
            predictions_df: DataFrame with predictions (Hours_Ahead, Salinity, Temperature, DO, pH, Alkalinity)
            
        Returns:
            dict: Alert status for predictions
        """
        predicted_alerts = {}
        
        for idx, row in predictions_df.iterrows():
            hours_ahead = row.get('Hours_Ahead', idx + 1)
            
            alerts = self.check_all_parameters({
                'Salinity': row.get('Salinity', 0),
                'Temperature': row.get('Temperature', 0),
                'DO': row.get('DO', 0),
                'pH': row.get('pH', 0),
                'Alkalinity': row.get('Alkalinity', 0)
            })
            
            predicted_alerts[f'Hour_{int(hours_ahead)}'] = alerts
        
        return predicted_alerts
    
    def get_critical_alerts(self):
        """
        Get all critical alerts from history.
        
        Returns:
            list: Critical alerts
        """
        critical = []
        for alert in self.alert_history:
            if alert['overall_level'] == AlertLevel.CRITICAL:
                critical.append(alert)
        return critical
    
    def get_recent_alerts(self, n=10):
        """
        Get recent alerts.
        
        Args:
            n: Number of recent alerts to retrieve
            
        Returns:
            list: Recent alerts
        """
        return self.alert_history[-n:]
    
    def format_alert_report(self, alerts):
        """
        Format alerts into a readable report.
        
        Args:
            alerts: Alert dictionary from check_all_parameters
            
        Returns:
            str: Formatted alert report
        """
        report = []
        report.append(f"\n{'='*70}")
        report.append(f"WATER QUALITY ALERT REPORT")
        report.append(f"Timestamp: {alerts['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Overall Status: {alerts['overall_level'].value}")
        report.append(f"{'='*70}")
        
        # Color codes for terminal
        color_map = {
            AlertLevel.NORMAL: '✓ ',
            AlertLevel.WARNING: '⚠ ',
            AlertLevel.CRITICAL: '✗ '
        }
        
        for param, info in alerts['parameters'].items():
            symbol = color_map.get(info['level'], '  ')
            report.append(f"{symbol} {info['description']}")
        
        report.append(f"{'='*70}\n")
        
        return '\n'.join(report)
    
    def generate_summary_report(self):
        """
        Generate a summary of alert history.
        
        Returns:
            str: Summary report
        """
        if not self.alert_history:
            return "No alerts recorded yet."
        
        report = []
        report.append(f"\n{'='*70}")
        report.append(f"ALERT HISTORY SUMMARY")
        report.append(f"Total Alerts: {len(self.alert_history)}")
        
        critical_count = sum(1 for a in self.alert_history if a['overall_level'] == AlertLevel.CRITICAL)
        warning_count = sum(1 for a in self.alert_history if a['overall_level'] == AlertLevel.WARNING)
        normal_count = len(self.alert_history) - critical_count - warning_count
        
        report.append(f"Normal:   {normal_count}")
        report.append(f"Warnings: {warning_count}")
        report.append(f"Critical: {critical_count}")
        report.append(f"{'='*70}\n")
        
        return '\n'.join(report)
