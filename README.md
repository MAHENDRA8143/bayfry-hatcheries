# AI-Based Smart Prawn Hatchery Water Quality Prediction and Monitoring System

## Project Overview

A comprehensive Python application for real-time monitoring and prediction of water quality parameters in prawn hatcheries using machine learning and ensemble modeling techniques.

**Version**: 1.0.0

## Features

### 1. **Real-Time Data Generation**
- Synthetic time-series data generator simulating realistic water quality parameters
- Hourly data generation with continuous simulation loop
- 5 Key Parameters:
  - **Salinity** (ppt): Stable with slow drift
  - **Temperature** (°C): Sinusoidal daily pattern
  - **DO** (mg/L): Dissolved oxygen with random fluctuations
  - **pH**: Stable with slight variations
  - **Alkalinity** (mg/L): Slow drift pattern

### 2. **Anomaly Detection**
- Random spike injection (5% probability per hour)
- 4 Anomaly types:
  - DO depletion (-2 to -4 mg/L)
  - Temperature spike (+2 to +6°C)
  - Salinity drop (-1 to -3 ppt)
  - pH variation (±1)

### 3. **Advanced Data Processing**
- Missing value handling (interpolation, forward-fill)
- Feature normalization (MinMax/StandardScaler)
- Lag feature engineering (1, 2, 3, 6, 12 hours)
- Rolling averages (12-hour window)

### 4. **Machine Learning Models**

#### Random Forest (50% weight)
- 100 estimators with multi-output regression
- 15 max depth for interpretability
- Excellent for capturing non-linear relationships

#### LSTM (30% weight)
- 2-layer LSTM with 64 units
- Dropout regularization (20%)
- Sequence-to-sequence architecture
- 24-hour history window

#### ARIMA (20% weight)
- Baseline statistical model
- Order (5, 1, 2) for univariate predictions
- Lightweight and interpretable

### 5. **Ensemble Prediction**
- Weighted averaging of all three models
- Adaptive weight distribution
- 24-hour future prediction horizon

### 6. **Alert System**
Three alert levels based on safe thresholds:
```
SAFE RANGES:
- Salinity: 10–25 ppt
- Temperature: 26–32°C
- DO: > 5 mg/L
- pH: 7.5–8.5
- Alkalinity: 80–150 mg/L

Alert Levels:
- NORMAL: Within safe range
- WARNING: 15% beyond limit
- CRITICAL: 25% beyond limit
```

### 7. **Professional Visualizations**
Using matplotlib (300 DPI, PNG format):
- Time series with safe range bands
- Anomaly detection highlighting
- Predicted vs actual comparisons
- Model performance comparison charts
- Alert status dashboards

### 8. **Output & Logging**
- Console output every iteration
- CSV data export (historical + alerts)
- PNG graph generation at 300 DPI
- Comprehensive alert history
- Performance metrics per model

## Project Structure

```
project2/
├── config.py                 # Configuration & constants
├── data_generator.py         # Synthetic data generation
├── data_processor.py         # Data preprocessing
├── models.py                 # ML models (RF, LSTM, ARIMA)
├── ensemble.py               # Ensemble prediction
├── alert_system.py           # Alert logic & thresholds
├── visualizer.py             # Matplotlib visualizations
├── main.py                   # Main orchestrator
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── outputs/
│   ├── data/                 # CSV exports
│   ├── graphs/               # PNG visualizations
│   └── logs/                 # Log files
```

## Installation

### Prerequisites
- Python 3.8+
- pip package manager

### Setup Instructions

1. **Clone/Extract Project**
   ```bash
   cd e:\proooject2
   ```

2. **Create Virtual Environment** (Recommended)
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Execution

```bash
python main.py
```

This will:
1. Initialize system with 30 days of historical data
2. Train Random Forest, LSTM, and ARIMA models
3. Run 12 simulation iterations (12 hours)
4. Generate predictions every 6 iterations
5. Create visualizations every 12 iterations
6. Save all data and graphs to `outputs/`

### Configuration

Edit `config.py` to customize:

```python
# Change simulation speed (seconds per simulated hour)
SIMULATION_HOUR_INTERVAL = 1  # 1 second = 1 hour

# Adjust anomaly probability
ANOMALY_PROBABILITY = 0.05  # 5% per hour

# Modify safe thresholds
SAFE_RANGES = {
    'Salinity': {'min': 10.0, 'max': 25.0},
    # ... etc
}

# Change prediction horizon
PREDICTION_HORIZON = 24  # 24 hours ahead

# Adjust model weights
MODEL_WEIGHTS = {
    'random_forest': 0.5,
    'lstm': 0.3,
    'arima': 0.2
}
```

## Key Modules

### 1. **DataGenerator** (`data_generator.py`)
```python
gen = WaterQualityDataGenerator(seed=42)
historical = gen.generate_historical_data(num_hours=720)
new_record = gen.generate_single_record()
```

### 2. **DataProcessor** (`data_processor.py`)
```python
processor = DataProcessor()
prepared_data = processor.prepare_data(df, fit=True)
normalized = processor.normalize_features(df)
```

### 3. **Models** (`models.py`)
```python
rf = RandomForestModel()
rf.train(X_train, y_train)
predictions = rf.predict(X_test)

lstm = LSTMModel()
lstm.train(X_seq_train, y_seq_train)
lstm_pred = lstm.predict(X_seq_test)

arima = ARIMAModel()
arima.train(df)
arima_pred = arima.predict(steps=24)
```

### 4. **EnsemblePredictor** (`ensemble.py`)
```python
ensemble = EnsemblePredictor(rf, lstm, arima)
predictions = ensemble.predict_ensemble(X_rf, X_lstm)
multi_step = ensemble.predict_multi_step(X_rf, X_lstm, steps_ahead=24)
```

### 5. **AlertSystem** (`alert_system.py`)
```python
alerts = AlertSystem()
alert_data = alerts.check_all_parameters({
    'Salinity': 18.5,
    'Temperature': 29.2,
    # ...
})
print(alerts.format_alert_report(alert_data))
```

### 6. **Visualizer** (`visualizer.py`)
```python
viz = WaterQualityVisualizer()
viz.plot_time_series(df, filename="ts_plot")
viz.plot_anomalies(df, filename="anomalies")
viz.plot_predictions_vs_actual(actual_df, pred_df)
viz.plot_alert_status(alert_data, filename="alerts")
```

## Output Files

### CSV Data Export
- `water_quality_data_YYYYMMDD_HHMMSS.csv` - All sensor readings
- `alerts_YYYYMMDD_HHMMSS.csv` - Alert event log

### PNG Visualizations (300 DPI)
- `timeseries_YYYYMMDD_HHMMSS.png` - Time series plot
- `anomalies_YYYYMMDD_HHMMSS.png` - Anomaly detection
- `alert_status_YYYYMMDD_HHMMSS.png` - Alert dashboard
- `predictions_YYYYMMDD_HHMMSS.png` - Model comparisons

## Model Performance

### Expected Metrics
- **Random Forest**: R² ~0.85-0.92
- **LSTM**: R² ~0.80-0.88
- **ARIMA**: R² ~0.75-0.85
- **Ensemble**: R² ~0.88-0.94 (typically highest)

Performance depends on data characteristics and model tuning.

## Key Hyperparameters

### Random Forest
```python
RF_PARAMS = {
    'n_estimators': 100,
    'max_depth': 15,
    'min_samples_split': 5,
    'min_samples_leaf': 2,
}
```

### LSTM
```python
LSTM_PARAMS = {
    'sequence_length': 24,
    'lstm_units': 64,
    'dense_units': 32,
    'dropout_rate': 0.2,
    'epochs': 50,
    'batch_size': 32,
}
```

### ARIMA
```python
ARIMA_PARAMS = {
    'order': (5, 1, 2),
}
```

## Monitoring in Production

For real production deployment:

1. **Change simulation interval**
   ```python
   SIMULATION_HOUR_INTERVAL = 3600  # 1 hour in seconds
   ```

2. **Replace data generator** with actual sensor API/database

3. **Add logging**
   ```python
   import logging
   logging.basicConfig(filename='logs/system.log', level=logging.INFO)
   ```

4. **Retrain models periodically**
   - Weekly: Check R² degradation
   - Monthly: Full retraining

5. **Monitor resource usage**
   - Check memory during LSTM inference
   - Profile data processing pipeline

## Customization Examples

### Change Alert Thresholds
Edit `config.py`:
```python
SAFE_RANGES = {
    'DO': {'min': 4.0, 'max': 12.0},  # More restrictive
}
```

### Adjust Model Weights
```python
MODEL_WEIGHTS = {
    'random_forest': 0.6,  # Increase RF weight
    'lstm': 0.2,
    'arima': 0.2
}
```

### Longer Prediction Horizon
```python
PREDICTION_HORIZON = 48  # 48 hours instead of 24
```

## Troubleshooting

### Issue: LSTM Training Slow
**Solution**: Reduce LSTM_PARAMS['epochs'] or increase batch_size

### Issue: Memory Error
**Solution**: Reduce HISTORY_RETENTION in config.py

### Issue: Predictions Always Same
**Solution**: Check if data has enough variance; verify normalization

## Academic Use Cases

This system is suitable for:
- Water quality prediction research
- Time-series forecasting studies
- Ensemble learning methods comparison
- Aquaculture optimization
- IoT data analysis
- Industrial process monitoring

## References

- Scikit-learn Documentation: https://scikit-learn.org/
- TensorFlow/Keras: https://www.tensorflow.org/
- Statsmodels ARIMA: https://www.statsmodels.org/
- Matplotlib: https://matplotlib.org/

## License

This project is provided as-is for educational and research purposes.

## Author Notes

This system demonstrates:
✓ Real-time data generation and simulation
✓ Advanced feature engineering
✓ Multiple ML model integration
✓ Ensemble learning techniques
✓ Alert system design
✓ Professional visualization
✓ Production-ready code structure
✓ Comprehensive documentation

For questions or improvements, review the code comments and configuration parameters.

---

**Last Updated**: May 2026
**Version**: 1.0.0
