"""
Ensemble model combining Random Forest, LSTM, and ARIMA predictions.
"""

import numpy as np
import pandas as pd
from config import MODEL_WEIGHTS


class EnsemblePredictor:
    """Ensemble model using weighted averaging of multiple models."""
    
    def __init__(self, rf_model, lstm_model, arima_model):
        """
        Initialize ensemble predictor.
        
        Args:
            rf_model: Trained RandomForestModel
            lstm_model: Trained LSTMModel
            arima_model: Trained ARIMAModel
        """
        self.rf_model = rf_model
        self.lstm_model = lstm_model
        self.arima_model = arima_model
        self.parameters = ['Salinity', 'Temperature', 'DO', 'pH', 'Alkalinity']
        
    def predict_ensemble(self, X_rf, X_lstm, steps_ahead=1):
        """
        Generate ensemble predictions combining all models.
        
        Args:
            X_rf: Features for Random Forest (2D array)
            X_lstm: Sequences for LSTM (3D array)
            steps_ahead: Number of hours ahead to predict
            
        Returns:
            dict: Ensemble predictions for each parameter
        """
        ensemble_predictions = {}
        
        # Random Forest predictions (for next step)
        rf_pred = self.rf_model.predict(X_rf)
        if rf_pred.ndim == 1:
            rf_pred = rf_pred.reshape(1, -1)
        
        # LSTM predictions
        lstm_pred = self.lstm_model.predict(X_lstm)
        if lstm_pred.ndim == 1:
            lstm_pred = lstm_pred.reshape(1, -1)
        
        # ARIMA predictions
        arima_pred = self.arima_model.predict(steps=steps_ahead)
        
        # Combine predictions with weights
        for i, param in enumerate(self.parameters):
            predictions = []
            
            # Random Forest contribution
            if not np.isnan(rf_pred[0, i]):
                predictions.append((rf_pred[0, i], MODEL_WEIGHTS['random_forest']))
            
            # LSTM contribution
            if not np.isnan(lstm_pred[0, i]):
                predictions.append((lstm_pred[0, i], MODEL_WEIGHTS['lstm']))
            
            # ARIMA contribution (if available)
            if param in arima_pred and not np.isnan(arima_pred[param][0]):
                predictions.append((arima_pred[param][0], MODEL_WEIGHTS['arima']))
            
            # Weighted average
            if predictions:
                numerator = sum(pred * weight for pred, weight in predictions)
                denominator = sum(weight for _, weight in predictions)
                ensemble_predictions[param] = numerator / denominator
            else:
                ensemble_predictions[param] = np.nan
        
        return ensemble_predictions
    
    def predict_multi_step(self, X_rf, X_lstm, steps_ahead=24):
        """
        Generate multi-step ahead predictions.
        
        Args:
            X_rf: Features for Random Forest
            X_lstm: Sequences for LSTM
            steps_ahead: Number of hours ahead to predict (default 24)
            
        Returns:
            pd.DataFrame: Multi-step predictions for each parameter
        """
        multi_step_predictions = []
        
        for step in range(steps_ahead):
            # For ARIMA, predict from current state
            ensemble_pred = self.predict_ensemble(X_rf, X_lstm, steps_ahead=step+1)
            
            pred_dict = {'Hours_Ahead': step + 1}
            pred_dict.update(ensemble_pred)
            multi_step_predictions.append(pred_dict)
        
        return pd.DataFrame(multi_step_predictions)
    
    def get_model_weights(self):
        """Get the weights used for each model."""
        return MODEL_WEIGHTS.copy()
    
    def evaluate_ensemble(self, y_true, rf_pred, lstm_pred, arima_predictions):
        """
        Evaluate ensemble performance against ground truth.
        
        Args:
            y_true: Ground truth values
            rf_pred: Random Forest predictions
            lstm_pred: LSTM predictions
            arima_predictions: ARIMA predictions
            
        Returns:
            dict: Evaluation metrics for ensemble
        """
        # Combine predictions with weights
        ensemble_pred = []
        
        for i in range(len(y_true)):
            pred_list = []
            
            if i < len(rf_pred) and not np.isnan(rf_pred[i]).any():
                pred_list.append((rf_pred[i], MODEL_WEIGHTS['random_forest']))
            
            if i < len(lstm_pred) and not np.isnan(lstm_pred[i]).any():
                pred_list.append((lstm_pred[i], MODEL_WEIGHTS['lstm']))
            
            if pred_list:
                numerator = sum((pred * weight).sum() for pred, weight in pred_list)
                denominator = sum(weight for _, weight in pred_list)
                ensemble_pred.append(numerator / denominator)
        
        ensemble_pred = np.array(ensemble_pred)
        
        from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
        
        mse = mean_squared_error(y_true, ensemble_pred)
        mae = mean_absolute_error(y_true, ensemble_pred)
        r2 = r2_score(y_true, ensemble_pred)
        rmse = np.sqrt(mse)
        
        return {
            'MSE': mse,
            'MAE': mae,
            'RMSE': rmse,
            'R2': r2
        }
