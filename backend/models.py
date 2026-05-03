"""
Machine learning models for water quality prediction.
Includes: Random Forest, LSTM, and ARIMA
"""

import numpy as np
import pandas as pd
import warnings
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.neural_network import MLPRegressor
from statsmodels.tsa.arima.model import ARIMA

from config import RF_PARAMS, LSTM_PARAMS, ARIMA_PARAMS

warnings.filterwarnings('ignore')

try:
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.optimizers import Adam
    TENSORFLOW_AVAILABLE = True
except ImportError:
    Sequential = None
    LSTM = Dense = Dropout = Adam = None
    TENSORFLOW_AVAILABLE = False


class RandomForestModel:
    """Random Forest model for multi-output prediction."""
    
    def __init__(self):
        """Initialize Random Forest model."""
        self.models = {}
        self.feature_columns = None
        
    def train(self, X_train, y_train, feature_columns=None):
        """
        Train Random Forest model.
        
        Args:
            X_train: Training features
            y_train: Training targets (5 outputs: Salinity, Temperature, DO, pH, Alkalinity)
            feature_columns: Names of feature columns
        """
        self.feature_columns = feature_columns
        
        # Use MultiOutputRegressor for multiple outputs
        rf = MultiOutputRegressor(RandomForestRegressor(**RF_PARAMS))
        rf.fit(X_train, y_train)
        self.model = rf
        
        print("✓ Random Forest model trained")
    
    def predict(self, X, hours_ahead=1):
        """
        Make predictions.
        
        Args:
            X: Input features
            hours_ahead: Number of hours ahead to predict
            
        Returns:
            np.ndarray: Predictions for each output
        """
        predictions = self.model.predict(X)
        return predictions
    
    def evaluate(self, X_test, y_test):
        """
        Evaluate model performance.
        
        Args:
            X_test: Test features
            y_test: Test targets
            
        Returns:
            dict: Evaluation metrics
        """
        y_pred = self.predict(X_test)
        
        mse = mean_squared_error(y_test, y_pred, multioutput='raw_values')
        mae = mean_absolute_error(y_test, y_pred, multioutput='raw_values')
        r2 = r2_score(y_test, y_pred, multioutput='raw_values')
        
        return {
            'MSE': mse,
            'MAE': mae,
            'R2': r2,
            'RMSE': np.sqrt(mse)
        }


class LSTMModel:
    """LSTM model for time-series prediction."""
    
    def __init__(self):
        """Initialize LSTM model."""
        self.model = None
        self.sequence_length = LSTM_PARAMS['sequence_length']
        self.uses_tensorflow = TENSORFLOW_AVAILABLE
        
    def build_model(self, input_shape):
        """
        Build LSTM neural network.
        
        Args:
            input_shape: Shape of input features (sequence_length, num_features)
        """
        if not self.uses_tensorflow:
            return

        self.model = Sequential([
            LSTM(LSTM_PARAMS['lstm_units'], activation='relu', 
                 input_shape=input_shape, return_sequences=True),
            Dropout(LSTM_PARAMS['dropout_rate']),
            LSTM(LSTM_PARAMS['lstm_units'], activation='relu'),
            Dropout(LSTM_PARAMS['dropout_rate']),
            Dense(LSTM_PARAMS['dense_units'], activation='relu'),
            Dropout(LSTM_PARAMS['dropout_rate']),
            Dense(5)  # 5 outputs: Salinity, Temperature, DO, pH, Alkalinity
        ])
        
        self.model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
    
    def prepare_sequences(self, data):
        """
        Prepare sequences for LSTM.
        
        Args:
            data: Input data array
            
        Returns:
            tuple: (X, y) sequences
        """
        X, y = [], []
        
        for i in range(len(data) - self.sequence_length - 1):
            X.append(data[i:i + self.sequence_length])
            y.append(data[i + self.sequence_length])
        
        return np.array(X), np.array(y)
    
    def train(self, X_train, y_train):
        """
        Train LSTM model.
        
        Args:
            X_train: Training sequences
            y_train: Training targets
        """
        X_train = np.asarray(X_train)
        y_train = np.asarray(y_train)
        sample_count = X_train.shape[0]

        if not self.uses_tensorflow:
            use_early_stopping = sample_count >= 10
            self.model = MLPRegressor(
                hidden_layer_sizes=(64, 32),
                activation='relu',
                solver='adam',
                max_iter=max(200, LSTM_PARAMS['epochs'] * 10),
                random_state=LSTM_PARAMS.get('random_state', 42),
                early_stopping=use_early_stopping,
                validation_fraction=LSTM_PARAMS['validation_split'] if use_early_stopping else 0.0
            )
            self.model.fit(self._flatten_sequences(X_train), y_train)
            if use_early_stopping:
                print("✓ Neural fallback model trained (TensorFlow unavailable)")
            else:
                print("✓ Neural fallback model trained without validation split (TensorFlow unavailable)")
            return

        input_shape = (X_train.shape[1], X_train.shape[2])
        self.build_model(input_shape)

        validation_split = LSTM_PARAMS['validation_split'] if sample_count >= 10 else 0.0
        
        self.model.fit(
            X_train, y_train,
            epochs=LSTM_PARAMS['epochs'],
            batch_size=LSTM_PARAMS['batch_size'],
            validation_split=validation_split,
            verbose=0
        )

        if validation_split > 0:
            print("✓ LSTM model trained")
        else:
            print("✓ LSTM model trained without validation split")
    
    def predict(self, X):
        """
        Make predictions.
        
        Args:
            X: Input sequences
            
        Returns:
            np.ndarray: Predictions
        """
        if not self.uses_tensorflow:
            return self.model.predict(self._flatten_sequences(X))

        return self.model.predict(X, verbose=0)

    def _flatten_sequences(self, X):
        """Flatten sequence data for the scikit-learn fallback model."""
        X = np.asarray(X)
        if X.ndim == 3:
            return X.reshape(X.shape[0], X.shape[1] * X.shape[2])
        return X
    
    def evaluate(self, X_test, y_test):
        """
        Evaluate model performance.
        
        Args:
            X_test: Test sequences
            y_test: Test targets
            
        Returns:
            dict: Evaluation metrics
        """
        y_pred = self.predict(X_test)
        
        mse = mean_squared_error(y_test, y_pred, multioutput='raw_values')
        mae = mean_absolute_error(y_test, y_pred, multioutput='raw_values')
        r2 = r2_score(y_test, y_pred, multioutput='raw_values')
        
        return {
            'MSE': mse,
            'MAE': mae,
            'R2': r2,
            'RMSE': np.sqrt(mse)
        }


class ARIMAModel:
    """ARIMA model for univariate time-series prediction."""
    
    def __init__(self):
        """Initialize ARIMA models (one per parameter)."""
        self.models = {}
        self.parameters = ['Salinity', 'Temperature', 'DO', 'pH', 'Alkalinity']
    
    def train(self, df):
        """
        Train ARIMA models for each parameter.
        
        Args:
            df: DataFrame with Salinity, Temperature, DO, pH, Alkalinity columns
        """
        for param in self.parameters:
            try:
                self.models[param] = ARIMA(
                    df[param],
                    order=ARIMA_PARAMS['order'],
                    seasonal_order=ARIMA_PARAMS['seasonal_order']
                ).fit()
            except Exception as e:
                print(f"Warning: Could not fit ARIMA for {param}: {e}")
                # Use simple naive forecast as fallback
                self.models[param] = None
        
        print("✓ ARIMA models trained")
    
    def predict(self, steps=1):
        """
        Make predictions for next steps.
        
        Args:
            steps: Number of steps ahead to predict
            
        Returns:
            dict: Predictions for each parameter
        """
        predictions = {}
        
        for param in self.parameters:
            try:
                if self.models[param] is not None:
                    forecast = self.models[param].get_forecast(steps=steps)
                    predictions[param] = forecast.predicted_mean.values
                else:
                    predictions[param] = np.full(steps, np.nan)
            except Exception as e:
                print(f"Warning: Prediction failed for {param}: {e}")
                predictions[param] = np.full(steps, np.nan)
        
        return predictions
    
    def evaluate(self, test_data):
        """
        Evaluate ARIMA models.
        
        Args:
            test_data: Test DataFrame
            
        Returns:
            dict: Evaluation metrics
        """
        metrics = {}
        
        for param in self.parameters:
            try:
                if self.models[param] is not None:
                    train_size = len(test_data) - len(test_data) // 5
                    
                    forecasts = []
                    for i in range(len(test_data) - train_size):
                        forecast = self.models[param].get_forecast(steps=1)
                        forecasts.append(forecast.predicted_mean.values[0])
                    
                    mse = mean_squared_error(test_data[param].iloc[train_size:], forecasts)
                    mae = mean_absolute_error(test_data[param].iloc[train_size:], forecasts)
                    
                    metrics[param] = {
                        'MSE': mse,
                        'MAE': mae,
                        'RMSE': np.sqrt(mse)
                    }
            except Exception as e:
                print(f"Warning: Evaluation failed for {param}: {e}")
        
        return metrics
