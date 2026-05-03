"""
Data processing module for handling missing values, normalization, and feature engineering.
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from config import LAG_FEATURES, ROLLING_WINDOW, NORMALIZATION_METHOD


class DataProcessor:
    """Handle data preprocessing, normalization, and feature engineering."""
    
    def __init__(self):
        """Initialize data processor with scalers."""
        self.scalers = {}
        self.feature_columns = ['Salinity', 'Temperature', 'DO', 'pH', 'Alkalinity']
        
    def handle_missing_values(self, df, method='interpolate'):
        """
        Handle missing values in the dataset.
        
        Args:
            df: Input DataFrame
            method: 'interpolate' (linear), 'forward_fill', or 'drop'
            
        Returns:
            pd.DataFrame: Processed DataFrame
        """
        df = df.copy()
        
        if method == 'interpolate':
            df[self.feature_columns] = df[self.feature_columns].interpolate(
                method='linear', limit_direction='both'
            )
        elif method == 'forward_fill':
            df[self.feature_columns] = df[self.feature_columns].fillna(method='ffill')
        elif method == 'drop':
            df = df.dropna(subset=self.feature_columns)
        
        # Fill any remaining NaN with mean
        df[self.feature_columns] = df[self.feature_columns].fillna(
            df[self.feature_columns].mean()
        )
        
        return df
    
    def normalize_features(self, df, fit=True):
        """
        Normalize features using MinMax or StandardScaler.
        
        Args:
            df: Input DataFrame
            fit: If True, fit the scaler on this data
            
        Returns:
            pd.DataFrame: Normalized DataFrame
        """
        df = df.copy()
        
        for col in self.feature_columns:
            if fit:
                if NORMALIZATION_METHOD == 'minmax':
                    scaler = MinMaxScaler()
                else:
                    scaler = StandardScaler()
                
                df[col] = scaler.fit_transform(df[[col]])
                self.scalers[col] = scaler
            else:
                if col in self.scalers:
                    df[col] = self.scalers[col].transform(df[[col]])
        
        return df
    
    def denormalize_features(self, df):
        """
        Reverse normalization to original scale.
        
        Args:
            df: Normalized DataFrame
            
        Returns:
            pd.DataFrame: Denormalized DataFrame
        """
        df = df.copy()
        
        for col in self.feature_columns:
            if col in self.scalers:
                df[col] = self.scalers[col].inverse_transform(df[[col]])
        
        return df
    
    def create_lag_features(self, df):
        """
        Create lag features for time-series modeling.
        
        Args:
            df: Input DataFrame with features
            
        Returns:
            pd.DataFrame: DataFrame with lag features added
        """
        df = df.copy()
        
        for col in self.feature_columns:
            for lag in LAG_FEATURES:
                df[f'{col}_lag_{lag}'] = df[col].shift(lag)
        
        return df
    
    def create_rolling_features(self, df):
        """
        Create rolling average features.
        
        Args:
            df: Input DataFrame
            
        Returns:
            pd.DataFrame: DataFrame with rolling features added
        """
        df = df.copy()
        
        for col in self.feature_columns:
            df[f'{col}_rolling_mean'] = df[col].rolling(window=ROLLING_WINDOW, min_periods=1).mean()
            df[f'{col}_rolling_std'] = df[col].rolling(window=ROLLING_WINDOW, min_periods=1).std()
        
        return df
    
    def prepare_data(self, df, fit=True):
        """
        Complete data preparation pipeline.
        
        Args:
            df: Input DataFrame
            fit: If True, fit scalers and create training features
            
        Returns:
            pd.DataFrame: Prepared DataFrame
        """
        # Handle missing values
        df = self.handle_missing_values(df)
        
        # Normalize features
        df = self.normalize_features(df, fit=fit)
        
        # Create engineered features
        df = self.create_lag_features(df)
        df = self.create_rolling_features(df)
        
        # Drop rows with NaN created by lag/rolling features
        df = df.dropna()
        
        return df
    
    def get_feature_columns(self):
        """Get all feature columns after engineering."""
        return self.feature_columns
    
    def get_engineered_columns(self):
        """Get all engineered feature columns."""
        engineered = []
        
        for col in self.feature_columns:
            # Lag features
            for lag in LAG_FEATURES:
                engineered.append(f'{col}_lag_{lag}')
            
            # Rolling features
            engineered.append(f'{col}_rolling_mean')
            engineered.append(f'{col}_rolling_std')
        
        return engineered
