"""
ADVANCED USAGE GUIDE - Smart Prawn Hatchery System

This module demonstrates advanced usage patterns and customizations.
"""

import pandas as pd
import numpy as np
from data_generator import WaterQualityDataGenerator
from data_processor import DataProcessor
from models import RandomForestModel, LSTMModel, ARIMAModel
from ensemble import EnsemblePredictor
from alert_system import AlertSystem
from visualizer import WaterQualityVisualizer
from config import SAFE_RANGES


# ============================================================================
# EXAMPLE 1: Custom Data Generation
# ============================================================================

def example_custom_data_generation():
    """Generate custom data with specific parameters."""
    print("\n" + "="*70)
    print("EXAMPLE 1: Custom Data Generation")
    print("="*70)
    
    generator = WaterQualityDataGenerator(seed=123)
    
    # Generate 72 hours of data
    data = generator.generate_batch(72)
    
    print(f"\nGenerated {len(data)} records")
    print(f"Anomalies: {data['Anomaly'].notna().sum()}")
    print("\nFirst 5 records:")
    print(data.head())
    
    return data


# ============================================================================
# EXAMPLE 2: Data Analysis
# ============================================================================

def example_data_analysis(data):
    """Analyze generated data."""
    print("\n" + "="*70)
    print("EXAMPLE 2: Data Analysis")
    print("="*70)
    
    print("\nStatistics:")
    print(data[['Salinity', 'Temperature', 'DO', 'pH', 'Alkalinity']].describe())
    
    print("\nCorrelation Matrix:")
    corr = data[['Salinity', 'Temperature', 'DO', 'pH', 'Alkalinity']].corr()
    print(corr)
    
    # Anomaly analysis
    anomaly_counts = data['Anomaly'].value_counts()
    print(f"\nAnomaly Distribution:")
    print(anomaly_counts)


# ============================================================================
# EXAMPLE 3: Feature Engineering
# ============================================================================

def example_feature_engineering(data):
    """Demonstrate feature engineering."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Feature Engineering")
    print("="*70)
    
    processor = DataProcessor()
    
    # Prepare data
    prepared = processor.prepare_data(data.copy(), fit=True)
    
    print(f"\nOriginal shape: {data.shape}")
    print(f"After feature engineering: {prepared.shape}")
    
    print(f"\nOriginal columns: {data.columns.tolist()}")
    print(f"\nEngineered features added:")
    engineered_cols = processor.get_engineered_columns()
    print(f"  - Total engineered features: {len(engineered_cols)}")
    print(f"  - Sample features: {engineered_cols[:5]}")
    
    return prepared


# ============================================================================
# EXAMPLE 4: Custom Alert Thresholds
# ============================================================================

def example_custom_alerts(data):
    """Set and test custom alert thresholds."""
    print("\n" + "="*70)
    print("EXAMPLE 4: Custom Alert Thresholds")
    print("="*70)
    
    alerts = AlertSystem()
    
    # Test with extreme values
    extreme_values = {
        'Salinity': 35.0,  # Above max
        'Temperature': 20.0,  # Below min
        'DO': 2.0,  # Below min
        'pH': 8.0,  # Normal
        'Alkalinity': 200.0  # Above max
    }
    
    print("\nTesting with extreme values:")
    for param, value in extreme_values.items():
        level, desc = alerts.check_parameter(param, value)
        print(f"  {desc} -> {level.value}")
    
    # Full alert check
    alert_data = alerts.check_all_parameters(extreme_values)
    print(f"\nOverall Alert Level: {alert_data['overall_level'].value}")


# ============================================================================
# EXAMPLE 5: Model Training & Comparison
# ============================================================================

def example_model_training(prepared_data):
    """Train and compare models."""
    print("\n" + "="*70)
    print("EXAMPLE 5: Model Training & Comparison")
    print("="*70)
    
    from data_processor import DataProcessor
    
    processor = DataProcessor()
    feature_cols = processor.get_engineered_columns()
    target_cols = ['Salinity', 'Temperature', 'DO', 'pH', 'Alkalinity']
    
    X = prepared_data[feature_cols].values
    y = prepared_data[target_cols].values
    
    # Split data
    split = int(0.8 * len(X))
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]
    
    # Random Forest
    print("\nTraining Random Forest...")
    rf = RandomForestModel()
    rf.train(X_train, y_train)
    rf_metrics = rf.evaluate(X_test, y_test)
    print(f"  RF - R²: {rf_metrics['R2'].mean():.4f}, RMSE: {rf_metrics['RMSE'].mean():.4f}")
    
    # LSTM
    print("Training LSTM...")
    lstm = LSTMModel()
    X_seq, y_seq = lstm.prepare_sequences(prepared_data[target_cols].values)
    split_lstm = int(0.8 * len(X_seq))
    lstm.train(X_seq[:split_lstm], y_seq[:split_lstm])
    lstm_metrics = lstm.evaluate(X_seq[split_lstm:], y_seq[split_lstm:])
    print(f"  LSTM - R²: {lstm_metrics['R2'].mean():.4f}, RMSE: {lstm_metrics['RMSE'].mean():.4f}")
    
    # ARIMA
    print("Training ARIMA...")
    arima = ARIMAModel()
    arima.train(prepared_data[target_cols])
    print("  ARIMA - Trained")
    
    return rf, lstm, arima


# ============================================================================
# EXAMPLE 6: Ensemble Predictions
# ============================================================================

def example_ensemble_predictions(rf, lstm, arima, recent_data):
    """Make ensemble predictions."""
    print("\n" + "="*70)
    print("EXAMPLE 6: Ensemble Predictions")
    print("="*70)
    
    from data_processor import DataProcessor
    
    processor = DataProcessor()
    
    # Prepare recent data
    prepared = processor.prepare_data(recent_data.copy(), fit=False)
    feature_cols = processor.get_engineered_columns()
    target_cols = ['Salinity', 'Temperature', 'DO', 'pH', 'Alkalinity']
    
    X_rf = prepared[feature_cols].values[-1:] if len(prepared) > 0 else None
    
    # LSTM sequence
    X_lstm_data = prepared[target_cols].values
    if X_lstm_data.shape[0] >= lstm.sequence_length:
        X_lstm = X_lstm_data[-lstm.sequence_length:].reshape(1, -1, 5)
    else:
        X_lstm = np.pad(X_lstm_data,
                       ((lstm.sequence_length - X_lstm_data.shape[0], 0), (0, 0)),
                       mode='edge').reshape(1, -1, 5)
    
    # Create ensemble
    ensemble = EnsemblePredictor(rf, lstm, arima)
    
    # Make predictions
    if X_rf is not None:
        predictions = ensemble.predict_multi_step(X_rf, X_lstm, steps_ahead=12)
        
        # Denormalize
        for col in target_cols:
            predictions[col] = processor.scalers[col].inverse_transform(
                predictions[[col]]
            )
        
        print("\n12-Hour Predictions:")
        print(predictions.to_string())
        
        return predictions


# ============================================================================
# EXAMPLE 7: Alert Predictions
# ============================================================================

def example_alert_predictions(predictions):
    """Check predictions for future alerts."""
    print("\n" + "="*70)
    print("EXAMPLE 7: Alert Predictions")
    print("="*70)
    
    alerts = AlertSystem()
    pred_alerts = alerts.check_predicted_values(predictions)
    
    print("\nChecking predicted values for alerts...\n")
    
    critical_count = 0
    warning_count = 0
    
    for hour, alert in pred_alerts.items():
        level = alert['overall_level'].value
        if level == 'CRITICAL':
            print(f"🚨 {hour}: CRITICAL")
            critical_count += 1
        elif level == 'WARNING':
            print(f"⚠️  {hour}: WARNING")
            warning_count += 1
    
    print(f"\nSummary: {critical_count} Critical, {warning_count} Warnings")


# ============================================================================
# EXAMPLE 8: Visualization
# ============================================================================

def example_visualization(data, predictions=None):
    """Generate visualizations."""
    print("\n" + "="*70)
    print("EXAMPLE 8: Visualization")
    print("="*70)
    
    viz = WaterQualityVisualizer()
    
    print("\nGenerating visualizations...")
    
    # Time series
    print("  1. Time series plot...")
    viz.plot_time_series(data, title="Water Quality Analysis",
                        filename="example_timeseries")
    
    # Anomalies
    print("  2. Anomaly plot...")
    viz.plot_anomalies(data, title="Anomaly Detection",
                      filename="example_anomalies")
    
    # Alert status
    print("  3. Alert status plot...")
    alerts = AlertSystem()
    recent_record = data.iloc[-1].to_dict()
    alert_data = alerts.check_all_parameters(recent_record)
    viz.plot_alert_status(alert_data, filename="example_alert_status")
    
    print("\n✓ Visualizations saved to outputs/graphs/")


# ============================================================================
# EXAMPLE 9: Custom Alert Thresholds
# ============================================================================

def example_modify_alert_thresholds():
    """Show how to modify alert thresholds dynamically."""
    print("\n" + "="*70)
    print("EXAMPLE 9: Modifying Alert Thresholds")
    print("="*70)
    
    # Original ranges
    print("\nOriginal Safe Ranges:")
    for param, range_vals in SAFE_RANGES.items():
        print(f"  {param}: {range_vals['min']:.1f} - {range_vals['max']:.1f}")
    
    # Custom ranges (more strict)
    custom_ranges = {
        'Salinity': {'min': 12.0, 'max': 22.0},      # Tighter
        'Temperature': {'min': 28.0, 'max': 30.0},   # Tighter
        'DO': {'min': 6.0, 'max': 10.0},             # Tighter
        'pH': {'min': 7.8, 'max': 8.2},              # Tighter
        'Alkalinity': {'min': 100.0, 'max': 140.0}   # Tighter
    }
    
    print("\nCustom (Tighter) Ranges:")
    for param, range_vals in custom_ranges.items():
        print(f"  {param}: {range_vals['min']:.1f} - {range_vals['max']:.1f}")
    
    print("\n💡 To use custom ranges, modify SAFE_RANGES in config.py")


# ============================================================================
# EXAMPLE 10: Performance Metrics
# ============================================================================

def example_performance_metrics(rf, lstm):
    """Display model performance metrics."""
    print("\n" + "="*70)
    print("EXAMPLE 10: Performance Metrics")
    print("="*70)
    
    print("\n💡 Model Performance Comparison:")
    print("  Random Forest: Fast training, good for complex relationships")
    print("  LSTM: Slower training, excellent for time-series patterns")
    print("  ARIMA: Lightweight, interpretable baseline")
    print("  Ensemble: Combines strengths of all models")
    
    print("\nRecommendations:")
    print("  - Use Random Forest (50%) as primary model")
    print("  - Use LSTM (30%) to capture temporal patterns")
    print("  - Use ARIMA (20%) as statistical baseline")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def run_all_examples():
    """Run all examples."""
    print("\n\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "ADVANCED USAGE EXAMPLES".center(68) + "║")
    print("║" + "Smart Prawn Hatchery System".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")
    
    # Example 1: Data generation
    data = example_custom_data_generation()
    
    # Example 2: Analysis
    example_data_analysis(data)
    
    # Example 3: Feature engineering
    prepared = example_feature_engineering(data)
    
    # Example 4: Alert thresholds
    example_custom_alerts(data)
    
    # Example 5: Model training
    rf, lstm, arima = example_model_training(prepared)
    
    # Example 6: Ensemble predictions
    predictions = example_ensemble_predictions(rf, lstm, arima, data)
    
    # Example 7: Alert predictions
    if predictions is not None:
        example_alert_predictions(predictions)
    
    # Example 8: Visualization
    example_visualization(data.tail(50), predictions)
    
    # Example 9: Custom thresholds
    example_modify_alert_thresholds()
    
    # Example 10: Performance metrics
    example_performance_metrics(rf, lstm)
    
    print("\n" + "="*70)
    print("✓ ALL EXAMPLES COMPLETED")
    print("="*70 + "\n")


if __name__ == "__main__":
    run_all_examples()
