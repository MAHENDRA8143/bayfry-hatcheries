"""
Visualization module for water quality data and predictions.
Uses matplotlib only (no seaborn).
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from config import GRAPH_DPI, GRAPH_FORMAT, GRAPH_FIGSIZE, GRAPHS_DIR, SAFE_RANGES
import os


class WaterQualityVisualizer:
    """Generate visualizations for water quality monitoring."""
    
    def __init__(self):
        """Initialize visualizer."""
        self.colors = {
            'Salinity': '#1f77b4',      # blue
            'Temperature': '#ff7f0e',   # orange
            'DO': '#2ca02c',            # green
            'pH': '#d62728',            # red
            'Alkalinity': '#9467bd'     # purple
        }
        self.parameters = ['Salinity', 'Temperature', 'DO', 'pH', 'Alkalinity']
    
    def plot_time_series(self, df, title="Water Quality Time Series", filename=None):
        """
        Plot time series data for all parameters.
        
        Args:
            df: DataFrame with Timestamp and parameter columns
            title: Plot title
            filename: Output filename (without extension)
            
        Returns:
            str: Path to saved figure
        """
        fig, axes = plt.subplots(3, 2, figsize=GRAPH_FIGSIZE)
        fig.suptitle(title, fontsize=16, fontweight='bold')
        
        axes = axes.flatten()
        
        for idx, param in enumerate(self.parameters):
            ax = axes[idx]
            
            if param in df.columns and 'Timestamp' in df.columns:
                ax.plot(df['Timestamp'], df[param], 
                       color=self.colors[param], linewidth=1.5, label=param)
                
                # Add safe range band
                safe_range = SAFE_RANGES[param]
                ax.axhspan(safe_range['min'], safe_range['max'], 
                          alpha=0.1, color=self.colors[param], label='Safe Range')
                
                # Add threshold lines
                ax.axhline(safe_range['min'], color=self.colors[param], 
                          linestyle='--', linewidth=1, alpha=0.5)
                ax.axhline(safe_range['max'], color=self.colors[param], 
                          linestyle='--', linewidth=1, alpha=0.5)
                
                ax.set_title(param)
                ax.set_xlabel('Time')
                ax.set_ylabel('Value')
                ax.grid(True, alpha=0.3)
                ax.legend(loc='upper right', fontsize=8)
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
                ax.xaxis.set_major_locator(mdates.HourLocator(interval=12))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Remove extra subplot
        fig.delaxes(axes[5])
        
        plt.tight_layout()
        
        if filename:
            filepath = os.path.join(GRAPHS_DIR, f"{filename}.{GRAPH_FORMAT}")
            plt.savefig(filepath, dpi=GRAPH_DPI, format=GRAPH_FORMAT, bbox_inches='tight')
            plt.close()
            return filepath
        
        plt.show()
        return None
    
    def plot_anomalies(self, df, title="Anomaly Detection", filename=None):
        """
        Highlight detected anomalies in the data.
        
        Args:
            df: DataFrame with anomaly information
            title: Plot title
            filename: Output filename
            
        Returns:
            str: Path to saved figure
        """
        fig, axes = plt.subplots(3, 2, figsize=GRAPH_FIGSIZE)
        fig.suptitle(title, fontsize=16, fontweight='bold')
        
        axes = axes.flatten()
        
        # Get anomaly rows
        anomalies = df[df['Anomaly'].notna()] if 'Anomaly' in df.columns else pd.DataFrame()
        
        for idx, param in enumerate(self.parameters):
            ax = axes[idx]
            
            if param in df.columns and 'Timestamp' in df.columns:
                # Plot normal data
                ax.plot(df['Timestamp'], df[param], 
                       color=self.colors[param], linewidth=1.5, alpha=0.7, label='Normal')
                
                # Highlight anomalies
                if not anomalies.empty:
                    ax.scatter(anomalies['Timestamp'], anomalies[param], 
                             color='red', s=100, marker='X', label='Anomaly', zorder=5)
                
                # Safe range
                safe_range = SAFE_RANGES[param]
                ax.axhspan(safe_range['min'], safe_range['max'], 
                          alpha=0.1, color=self.colors[param])
                
                ax.set_title(f"{param} - Anomaly Detection")
                ax.set_xlabel('Time')
                ax.set_ylabel('Value')
                ax.grid(True, alpha=0.3)
                ax.legend(loc='upper right', fontsize=8)
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
                ax.xaxis.set_major_locator(mdates.HourLocator(interval=12))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        fig.delaxes(axes[5])
        
        plt.tight_layout()
        
        if filename:
            filepath = os.path.join(GRAPHS_DIR, f"{filename}.{GRAPH_FORMAT}")
            plt.savefig(filepath, dpi=GRAPH_DPI, format=GRAPH_FORMAT, bbox_inches='tight')
            plt.close()
            return filepath
        
        plt.show()
        return None
    
    def plot_predictions_vs_actual(self, actual_df, pred_df, 
                                   title="Predictions vs Actual", filename=None):
        """
        Compare predicted vs actual values.
        
        Args:
            actual_df: DataFrame with actual values
            pred_df: DataFrame with predictions
            title: Plot title
            filename: Output filename
            
        Returns:
            str: Path to saved figure
        """
        fig, axes = plt.subplots(3, 2, figsize=GRAPH_FIGSIZE)
        fig.suptitle(title, fontsize=16, fontweight='bold')
        
        axes = axes.flatten()
        
        for idx, param in enumerate(self.parameters):
            ax = axes[idx]
            
            if param in actual_df.columns and 'Timestamp' in actual_df.columns:
                # Plot actual values
                ax.plot(actual_df['Timestamp'], actual_df[param], 
                       color=self.colors[param], linewidth=2, label='Actual', marker='o', markersize=4)
            
            if param in pred_df.columns:
                # Plot predictions
                future_times = [actual_df['Timestamp'].iloc[-1] + timedelta(hours=i+1) 
                               for i in range(len(pred_df))]
                ax.plot(future_times, pred_df[param], 
                       color=self.colors[param], linewidth=2, linestyle='--', 
                       label='Predicted', marker='s', markersize=4)
            
            ax.set_title(f"{param}")
            ax.set_xlabel('Time')
            ax.set_ylabel('Value')
            ax.grid(True, alpha=0.3)
            ax.legend(loc='upper right', fontsize=8)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=12))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        fig.delaxes(axes[5])
        
        plt.tight_layout()
        
        if filename:
            filepath = os.path.join(GRAPHS_DIR, f"{filename}.{GRAPH_FORMAT}")
            plt.savefig(filepath, dpi=GRAPH_DPI, format=GRAPH_FORMAT, bbox_inches='tight')
            plt.close()
            return filepath
        
        plt.show()
        return None
    
    def plot_model_comparison(self, rf_pred, lstm_pred, ensemble_pred, actual_values,
                             title="Model Comparison", filename=None):
        """
        Compare predictions from different models.
        
        Args:
            rf_pred: Random Forest predictions
            lstm_pred: LSTM predictions
            ensemble_pred: Ensemble predictions
            actual_values: Actual values
            title: Plot title
            filename: Output filename
            
        Returns:
            str: Path to saved figure
        """
        fig, axes = plt.subplots(3, 2, figsize=GRAPH_FIGSIZE)
        fig.suptitle(title, fontsize=16, fontweight='bold')
        
        axes = axes.flatten()
        
        x_pos = np.arange(len(self.parameters))
        width = 0.2
        
        for param_idx, param in enumerate(self.parameters):
            ax = axes[param_idx]
            
            # Get predictions for this parameter
            rf_val = rf_pred[param_idx] if param_idx < len(rf_pred) else 0
            lstm_val = lstm_pred[param_idx] if param_idx < len(lstm_pred) else 0
            ensemble_val = ensemble_pred.get(param, 0) if isinstance(ensemble_pred, dict) else ensemble_pred[param_idx]
            actual_val = actual_values[param_idx] if param_idx < len(actual_values) else 0
            
            values = [actual_val, rf_val, lstm_val, ensemble_val]
            labels = ['Actual', 'RF', 'LSTM', 'Ensemble']
            colors_bar = ['green', '#1f77b4', '#ff7f0e', '#d62728']
            
            bars = ax.bar(labels, values, color=colors_bar, alpha=0.7, edgecolor='black')
            
            # Add value labels on bars
            for bar, val in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{val:.2f}', ha='center', va='bottom', fontsize=9)
            
            ax.set_title(param)
            ax.set_ylabel('Value')
            ax.grid(True, alpha=0.3, axis='y')
        
        fig.delaxes(axes[5])
        
        plt.tight_layout()
        
        if filename:
            filepath = os.path.join(GRAPHS_DIR, f"{filename}.{GRAPH_FORMAT}")
            plt.savefig(filepath, dpi=GRAPH_DPI, format=GRAPH_FORMAT, bbox_inches='tight')
            plt.close()
            return filepath
        
        plt.show()
        return None
    
    def plot_alert_status(self, alert_data, title="Water Quality Alert Status", filename=None):
        """
        Visualize current alert status.
        
        Args:
            alert_data: Alert dictionary from AlertSystem
            title: Plot title
            filename: Output filename
            
        Returns:
            str: Path to saved figure
        """
        fig, ax = plt.subplots(figsize=(12, 8))
        
        parameters = []
        values = []
        min_ranges = []
        max_ranges = []
        colors = []
        
        for param in self.parameters:
            if param in alert_data['parameters']:
                param_info = alert_data['parameters'][param]
                parameters.append(param)
                values.append(param_info['value'])
                
                safe_range = SAFE_RANGES[param]
                min_ranges.append(safe_range['min'])
                max_ranges.append(safe_range['max'])
                
                # Color based on alert level
                level = param_info['level'].value
                if level == 'NORMAL':
                    colors.append('green')
                elif level == 'WARNING':
                    colors.append('orange')
                else:
                    colors.append('red')
        
        x_pos = np.arange(len(parameters))
        
        # Plot safe ranges as background bars
        ax.bar(x_pos, max_ranges, bottom=min_ranges, alpha=0.2, color='green', 
              label='Safe Range', width=0.4)
        
        # Plot actual values
        ax.bar(x_pos, values, alpha=0.8, color=colors, label='Current Value', width=0.4)
        
        # Add threshold lines
        for i, param in enumerate(parameters):
            safe_range = SAFE_RANGES[param]
            ax.axhline(safe_range['min'], color='gray', linestyle='--', linewidth=0.5, alpha=0.5)
            ax.axhline(safe_range['max'], color='gray', linestyle='--', linewidth=0.5, alpha=0.5)
        
        ax.set_xticks(x_pos)
        ax.set_xticklabels(parameters)
        ax.set_ylabel('Value')
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        if filename:
            filepath = os.path.join(GRAPHS_DIR, f"{filename}.{GRAPH_FORMAT}")
            plt.savefig(filepath, dpi=GRAPH_DPI, format=GRAPH_FORMAT, bbox_inches='tight')
            plt.close()
            return filepath
        
        plt.show()
        return None
