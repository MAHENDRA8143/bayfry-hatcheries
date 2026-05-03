"""
Main orchestrator for the Smart Prawn Hatchery Water Quality Prediction System.
Coordinates all modules and runs the continuous simulation loop.
"""

import numpy as np
import pandas as pd
import time
from datetime import datetime, timedelta
import os
import warnings

# Import all modules
from config import (
    PROJECT_NAME, PROJECT_VERSION, SIMULATION_HOUR_INTERVAL, 
    PREDICTION_HORIZON, HISTORY_RETENTION, DATA_DIR, GRAPHS_DIR
)
from data_generator import WaterQualityDataGenerator
from data_processor import DataProcessor
from models import RandomForestModel, LSTMModel, ARIMAModel
from ensemble import EnsemblePredictor
from alert_system import AlertSystem
from visualizer import WaterQualityVisualizer

warnings.filterwarnings('ignore')


class SmartHatcherySystem:
    """Main system coordinator."""
    
    def __init__(self):
        """Initialize the system."""
        print(f"\n{'='*70}")
        print(f"{PROJECT_NAME}")
        print(f"Version {PROJECT_VERSION}")
        print(f"{'='*70}\n")
        
        # Initialize components
        self.data_generator = WaterQualityDataGenerator(seed=42)
        self.data_processor = DataProcessor()
        self.alert_system = AlertSystem()
        self.visualizer = WaterQualityVisualizer()
        
        # ML models
        self.rf_model = RandomForestModel()
        self.lstm_model = LSTMModel()
        self.arima_model = ARIMAModel()
        self.ensemble = None
        
        # Data storage
        self.data_history = pd.DataFrame()
        self.iteration_count = 0
        
    def initialize_system(self):
        """Initialize system with historical data and train models."""
        print("\n[INITIALIZATION PHASE]")
        print("-" * 70)
        
        # Generate historical data
        print("1. Generating historical data (30 days)...")
        historical_data = self.data_generator.generate_historical_data(num_hours=720)
        self.data_history = historical_data.copy()
        print(f"   ✓ Generated {len(self.data_history)} records\n")
        
        # Prepare data
        print("2. Preparing data for model training...")
        processed_data = self.data_processor.prepare_data(self.data_history.copy(), fit=True)
        print(f"   ✓ Data prepared. Shape: {processed_data.shape}\n")
        
        # Extract features and targets
        feature_cols = self.data_processor.get_engineered_columns()
        target_cols = ['Salinity', 'Temperature', 'DO', 'pH', 'Alkalinity']
        
        X = processed_data[feature_cols].values
        y = processed_data[target_cols].values
        
        # Split data
        split_idx = int(0.8 * len(X))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # Train Random Forest
        print("3. Training Random Forest model...")
        self.rf_model.train(X_train, y_train, feature_cols)
        rf_metrics = self.rf_model.evaluate(X_test, y_test)
        print(f"   ✓ RF R² Score: {np.asarray(rf_metrics['R2']).mean():.4f}\n")
        
        # Prepare LSTM sequences
        print("4. Training LSTM model...")
        X_seq, y_seq = self.lstm_model.prepare_sequences(
            processed_data[target_cols].values
        )
        split_lstm = int(0.8 * len(X_seq))
        X_seq_train = X_seq[:split_lstm]
        y_seq_train = y_seq[:split_lstm]
        X_seq_test = X_seq[split_lstm:]
        y_seq_test = y_seq[split_lstm:]
        
        self.lstm_model.train(X_seq_train, y_seq_train)
        lstm_metrics = self.lstm_model.evaluate(X_seq_test, y_seq_test)
        print(f"   ✓ LSTM R² Score: {np.asarray(lstm_metrics['R2']).mean():.4f}\n")
        
        # Train ARIMA
        print("5. Training ARIMA models...")
        self.arima_model.train(self.data_history[target_cols])
        print("   ✓ ARIMA models trained\n")
        
        # Initialize ensemble
        self.ensemble = EnsemblePredictor(self.rf_model, self.lstm_model, self.arima_model)
        print("6. Ensemble model initialized")
        weights = self.ensemble.get_model_weights()
        print(f"   ✓ Model weights: RF={weights['random_forest']}, "
              f"LSTM={weights['lstm']}, ARIMA={weights['arima']}\n")
        
        print("-" * 70)
        print("✓ SYSTEM INITIALIZATION COMPLETE\n")
    
    def run_simulation_iteration(self):
        """Run a single iteration of the simulation."""
        self.iteration_count += 1
        
        # Generate new data
        new_record = self.data_generator.generate_single_record()
        new_df = pd.DataFrame([new_record])
        
        # Append to history
        self.data_history = pd.concat([self.data_history, new_df], ignore_index=True)
        
        # Keep only recent history
        if len(self.data_history) > HISTORY_RETENTION:
            self.data_history = self.data_history.iloc[-HISTORY_RETENTION:].reset_index(drop=True)
        
        # Display current values
        self._display_current_values(new_record)
        
        # Check for anomalies
        if new_record['Anomaly']:
            print(f"\n⚠️  ANOMALY DETECTED: {new_record['Anomaly']}")
        
        # Generate alerts
        alert_data = self.alert_system.check_all_parameters({
            'Salinity': new_record['Salinity'],
            'Temperature': new_record['Temperature'],
            'DO': new_record['DO'],
            'pH': new_record['pH'],
            'Alkalinity': new_record['Alkalinity']
        })
        
        print(self.alert_system.format_alert_report(alert_data))
        
        # Make predictions (every 6 iterations to reduce computation)
        if self.iteration_count % 6 == 0:
            self._make_predictions()
        
        # Generate visualizations (every 12 iterations)
        if self.iteration_count % 12 == 0:
            self._generate_visualizations()
    
    def _display_current_values(self, record):
        """Display current sensor values."""
        print(f"\n{'='*70}")
        print(f"ITERATION #{self.iteration_count} - {record['Timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}")
        print(f"Salinity (ppt)    : {record['Salinity']:.2f}")
        print(f"Temperature (°C)  : {record['Temperature']:.2f}")
        print(f"DO (mg/L)         : {record['DO']:.2f}")
        print(f"pH                : {record['pH']:.2f}")
        print(f"Alkalinity (mg/L) : {record['Alkalinity']:.2f}")
    
    def _make_predictions(self):
        """Make ensemble predictions for next 24 hours."""
        print(f"\n[PREDICTION PHASE - Iteration {self.iteration_count}]")
        print("-" * 70)
        
        try:
            # Prepare recent data
            recent_data = self.data_history[
                ['Salinity', 'Temperature', 'DO', 'pH', 'Alkalinity']
            ].tail(100).copy()
            
            processed_recent = self.data_processor.prepare_data(recent_data, fit=False)
            
            # Get latest sequence for RF and LSTM
            feature_cols = self.data_processor.get_engineered_columns()
            X_rf = processed_recent[feature_cols].values[-1:] if len(processed_recent) > 0 else None
            
            # LSTM sequence
            X_lstm_data = processed_recent[
                ['Salinity', 'Temperature', 'DO', 'pH', 'Alkalinity']
            ].values
            
            if X_lstm_data.shape[0] >= self.lstm_model.sequence_length:
                X_lstm = X_lstm_data[-self.lstm_model.sequence_length:].reshape(1, -1, 5)
            else:
                X_lstm = np.pad(X_lstm_data, 
                              ((self.lstm_model.sequence_length - X_lstm_data.shape[0], 0), (0, 0)),
                              mode='edge').reshape(1, -1, 5)
            
            # Generate ensemble predictions
            if X_rf is not None:
                predictions = self.ensemble.predict_multi_step(X_rf, X_lstm, PREDICTION_HORIZON)
                
                # Denormalize predictions
                for col in ['Salinity', 'Temperature', 'DO', 'pH', 'Alkalinity']:
                    if col in predictions.columns:
                        predictions[col] = self.data_processor.scalers[col].inverse_transform(
                            predictions[[col]]
                        )
                
                # Display predictions
                print("\n24-HOUR FORECAST (Next 24 Hours):")
                print(predictions.to_string(index=False))
                
                # Check predicted alerts
                predicted_alerts = self.alert_system.check_predicted_values(predictions)
                
                critical_predictions = [
                    (hour, alert) for hour, alert in predicted_alerts.items()
                    if alert['overall_level'].value == 'CRITICAL'
                ]
                
                if critical_predictions:
                    print("\n🚨 CRITICAL PREDICTIONS DETECTED:")
                    for hour, alert in critical_predictions:
                        critical_parameters = [
                            p for p, i in alert['parameters'].items()
                            if i['level'].value == 'CRITICAL'
                        ]
                        print(f"   {hour}: {critical_parameters}")
        
        except Exception as e:
            print(f"⚠️  Prediction error: {e}")
        
        print("-" * 70)
    
    def _generate_visualizations(self):
        """Generate visualization outputs."""
        print(f"\n[VISUALIZATION PHASE - Iteration {self.iteration_count}]")
        print("-" * 70)
        
        try:
            # Time series plot
            timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            print("1. Generating time series plot...")
            self.visualizer.plot_time_series(
                self.data_history.tail(100),
                title="Water Quality Time Series (Recent 100 Hours)",
                filename=f"timeseries_{timestamp_str}"
            )
            
            # Anomaly detection plot
            print("2. Generating anomaly detection plot...")
            self.visualizer.plot_anomalies(
                self.data_history.tail(100),
                title="Anomaly Detection",
                filename=f"anomalies_{timestamp_str}"
            )
            
            # Alert status plot
            if self.alert_system.alert_history:
                print("3. Generating alert status plot...")
                latest_alert = self.alert_system.alert_history[-1]
                self.visualizer.plot_alert_status(
                    latest_alert,
                    title="Current Water Quality Alert Status",
                    filename=f"alert_status_{timestamp_str}"
                )
            
            print(f"✓ Visualizations saved to {GRAPHS_DIR}")
        
        except Exception as e:
            print(f"⚠️  Visualization error: {e}")
        
        print("-" * 70)
    
    def run_continuous_loop(self, num_iterations=24, save_data=True):
        """
        Run continuous simulation loop.
        
        Args:
            num_iterations: Number of iterations to run (default 24 for 24 hours)
            save_data: Whether to save data to CSV
        """
        print(f"\n[STARTING CONTINUOUS SIMULATION LOOP]")
        print(f"Iterations: {num_iterations}")
        print(f"Interval: {SIMULATION_HOUR_INTERVAL} second(s) per hour\n")
        
        try:
            for i in range(num_iterations):
                self.run_simulation_iteration()
                
                # Sleep to simulate hourly updates (configurable for demo)
                if i < num_iterations - 1:
                    time.sleep(SIMULATION_HOUR_INTERVAL)
                
                print(f"\nNext iteration in {SIMULATION_HOUR_INTERVAL} second(s)...\n")
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Simulation interrupted by user")
        
        finally:
            # Save data
            if save_data:
                self._save_data()
            
            # Generate final report
            self._generate_final_report()
    
    def _save_data(self):
        """Save data to CSV."""
        print("\n[SAVING DATA]")
        print("-" * 70)
        
        try:
            timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Save full history
            data_file = os.path.join(DATA_DIR, f'water_quality_data_{timestamp_str}.csv')
            self.data_history.to_csv(data_file, index=False)
            print(f"✓ Data saved: {data_file}")
            
            # Save alerts
            if self.alert_system.alert_history:
                alerts_list = []
                for alert in self.alert_system.alert_history:
                    alert_row = {
                        'Timestamp': alert['timestamp'],
                        'Overall_Level': alert['overall_level'].value
                    }
                    for param, info in alert['parameters'].items():
                        alert_row[f"{param}_Level"] = info['level'].value
                        alert_row[f"{param}_Value"] = info['value']
                    alerts_list.append(alert_row)
                
                alerts_df = pd.DataFrame(alerts_list)
                alerts_file = os.path.join(DATA_DIR, f'alerts_{timestamp_str}.csv')
                alerts_df.to_csv(alerts_file, index=False)
                print(f"✓ Alerts saved: {alerts_file}")
        
        except Exception as e:
            print(f"⚠️  Error saving data: {e}")
        
        print("-" * 70)
    
    def _generate_final_report(self):
        """Generate final report."""
        print("\n[FINAL REPORT]")
        print("=" * 70)
        print(f"Total Iterations: {self.iteration_count}")
        print(f"Data Records: {len(self.data_history)}")
        print(f"Alert Events: {len(self.alert_system.alert_history)}")
        print(self.alert_system.generate_summary_report())
        print("=" * 70)


def main():
    """Main entry point."""
    # Initialize system
    system = SmartHatcherySystem()
    
    # Initialize with historical data and train models
    system.initialize_system()
    
    # Run continuous simulation
    # For demo: 12 iterations (12 hours)
    # For production: modify SIMULATION_HOUR_INTERVAL to 3600 seconds
    system.run_continuous_loop(num_iterations=12, save_data=True)


if __name__ == "__main__":
    main()
