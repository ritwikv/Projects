"""
Performance Monitoring Module for Time Series Models
Monitors model performance against original benchmarks and detects degradation
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from scipy import stats
from datetime import datetime, timedelta
import warnings
import logging
from dataclasses import dataclass

try:
    from .config import config
except ImportError:
    from config import config

# Set up logging
logging.basicConfig(level=getattr(logging, config.log_level), format=config.log_format)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Container for performance metrics"""
    mape: float
    mae: float
    rmse: float
    bias: float
    trend_accuracy: float
    seasonal_accuracy: float
    directional_accuracy: float
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'mape': self.mape,
            'mae': self.mae,
            'rmse': self.rmse,
            'bias': self.bias,
            'trend_accuracy': self.trend_accuracy,
            'seasonal_accuracy': self.seasonal_accuracy,
            'directional_accuracy': self.directional_accuracy
        }

class PerformanceMonitor:
    """
    Comprehensive performance monitoring for time series models
    Compares live performance against original test benchmarks
    """
    
    def __init__(self, original_performance: Optional[Dict[str, float]] = None):
        """
        Initialize performance monitor
        
        Args:
            original_performance: Dictionary with original test performance metrics
        """
        self.original_performance = original_performance or {}
        self.performance_history = []
        self.alerts_history = []
        
        # Set original performance from config if available
        if config.model.original_test_mape:
            self.original_performance.update({
                'mape': config.model.original_test_mape,
                'mae': config.model.original_test_mae,
                'rmse': config.model.original_test_rmse
            })
    
    def calculate_metrics(self, actual: np.ndarray, forecast: np.ndarray, 
                         dates: Optional[pd.DatetimeIndex] = None) -> PerformanceMetrics:
        """
        Calculate comprehensive performance metrics
        
        Args:
            actual: Actual values
            forecast: Forecasted values
            dates: Optional datetime index for seasonal analysis
            
        Returns:
            PerformanceMetrics object with all calculated metrics
        """
        # Basic error metrics
        mape = self._calculate_mape(actual, forecast)
        mae = self._calculate_mae(actual, forecast)
        rmse = self._calculate_rmse(actual, forecast)
        bias = self._calculate_bias(actual, forecast)
        
        # Advanced metrics
        trend_accuracy = self._calculate_trend_accuracy(actual, forecast)
        directional_accuracy = self._calculate_directional_accuracy(actual, forecast)
        
        # Seasonal accuracy (if dates provided)
        seasonal_accuracy = self._calculate_seasonal_accuracy(actual, forecast, dates) if dates is not None else 0.0
        
        return PerformanceMetrics(
            mape=mape,
            mae=mae,
            rmse=rmse,
            bias=bias,
            trend_accuracy=trend_accuracy,
            seasonal_accuracy=seasonal_accuracy,
            directional_accuracy=directional_accuracy
        )
    
    def monitor_live_performance(self, actual: np.ndarray, forecast: np.ndarray,
                               dates: Optional[pd.DatetimeIndex] = None) -> Dict[str, Any]:
        """
        Monitor live performance against original benchmarks
        
        Args:
            actual: Recent actual values
            forecast: Recent forecasted values
            dates: Optional datetime index
            
        Returns:
            Dictionary with performance analysis and alerts
        """
        # Calculate current metrics
        current_metrics = self.calculate_metrics(actual, forecast, dates)
        
        # Store in history
        self.performance_history.append({
            'timestamp': datetime.now(),
            'metrics': current_metrics,
            'data_points': len(actual)
        })
        
        # Compare against original performance
        performance_comparison = self._compare_performance(current_metrics)
        
        # Generate alerts
        alerts = self._generate_alerts(current_metrics, performance_comparison)
        
        # Store alerts
        if alerts:
            self.alerts_history.extend(alerts)
        
        return {
            'current_metrics': current_metrics.to_dict(),
            'performance_comparison': performance_comparison,
            'alerts': alerts,
            'recommendation': self._get_recommendation(performance_comparison, alerts)
        }
    
    def detect_data_drift(self, original_data: np.ndarray, recent_data: np.ndarray) -> Dict[str, Any]:
        """
        Detect data drift between original training data and recent data
        
        Args:
            original_data: Original training data (36 months)
            recent_data: Recent data for comparison
            
        Returns:
            Dictionary with drift detection results
        """
        drift_results = {}
        
        # Statistical tests for distribution changes
        ks_stat, ks_pvalue = stats.ks_2samp(original_data, recent_data)
        drift_results['ks_test'] = {
            'statistic': ks_stat,
            'p_value': ks_pvalue,
            'drift_detected': ks_pvalue < config.monitoring.drift_significance_level
        }
        
        # Mann-Whitney U test for median differences
        mw_stat, mw_pvalue = stats.mannwhitneyu(original_data, recent_data, alternative='two-sided')
        drift_results['mann_whitney_test'] = {
            'statistic': mw_stat,
            'p_value': mw_pvalue,
            'drift_detected': mw_pvalue < config.monitoring.drift_significance_level
        }
        
        # Descriptive statistics comparison
        original_stats = self._calculate_descriptive_stats(original_data)
        recent_stats = self._calculate_descriptive_stats(recent_data)
        
        drift_results['descriptive_comparison'] = {
            'original_stats': original_stats,
            'recent_stats': recent_stats,
            'mean_change_pct': ((recent_stats['mean'] - original_stats['mean']) / original_stats['mean']) * 100,
            'std_change_pct': ((recent_stats['std'] - original_stats['std']) / original_stats['std']) * 100,
            'significant_change': abs((recent_stats['mean'] - original_stats['mean']) / original_stats['mean']) > 0.2
        }
        
        # Overall drift assessment
        drift_results['overall_assessment'] = {
            'drift_detected': any([
                drift_results['ks_test']['drift_detected'],
                drift_results['mann_whitney_test']['drift_detected'],
                drift_results['descriptive_comparison']['significant_change']
            ]),
            'severity': self._assess_drift_severity(drift_results)
        }
        
        logger.info(f"Data drift detection completed. Drift detected: {drift_results['overall_assessment']['drift_detected']}")
        
        return drift_results
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive performance report
        
        Returns:
            Dictionary with complete performance analysis
        """
        if not self.performance_history:
            return {'error': 'No performance data available'}
        
        # Recent performance trends
        recent_metrics = [entry['metrics'] for entry in self.performance_history[-6:]]  # Last 6 entries
        
        # Calculate trends
        mape_trend = [m.mape for m in recent_metrics]
        mae_trend = [m.mae for m in recent_metrics]
        
        # Performance summary
        current_performance = self.performance_history[-1]['metrics']
        
        report = {
            'summary': {
                'current_mape': current_performance.mape,
                'current_mae': current_performance.mae,
                'current_rmse': current_performance.rmse,
                'trend_direction': 'improving' if len(mape_trend) > 1 and mape_trend[-1] < mape_trend[0] else 'degrading',
                'total_monitoring_periods': len(self.performance_history)
            },
            'trends': {
                'mape_trend': mape_trend,
                'mae_trend': mae_trend,
                'performance_stability': np.std(mape_trend) if len(mape_trend) > 1 else 0
            },
            'alerts_summary': {
                'total_alerts': len(self.alerts_history),
                'recent_alerts': [alert for alert in self.alerts_history 
                                if (datetime.now() - alert['timestamp']).days <= 30],
                'alert_types': self._summarize_alert_types()
            },
            'recommendations': self._generate_recommendations()
        }
        
        return report
    
    # Private helper methods
    def _calculate_mape(self, actual: np.ndarray, forecast: np.ndarray) -> float:
        """Calculate Mean Absolute Percentage Error"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return np.mean(np.abs((actual - forecast) / actual)) * 100
    
    def _calculate_mae(self, actual: np.ndarray, forecast: np.ndarray) -> float:
        """Calculate Mean Absolute Error"""
        return np.mean(np.abs(actual - forecast))
    
    def _calculate_rmse(self, actual: np.ndarray, forecast: np.ndarray) -> float:
        """Calculate Root Mean Square Error"""
        return np.sqrt(np.mean((actual - forecast) ** 2))
    
    def _calculate_bias(self, actual: np.ndarray, forecast: np.ndarray) -> float:
        """Calculate forecast bias (percentage)"""
        return (np.mean(forecast) - np.mean(actual)) / np.mean(actual) * 100
    
    def _calculate_trend_accuracy(self, actual: np.ndarray, forecast: np.ndarray) -> float:
        """Calculate trend direction accuracy"""
        if len(actual) < 2:
            return 0.0
        
        actual_trends = np.diff(actual) > 0
        forecast_trends = np.diff(forecast) > 0
        
        return np.mean(actual_trends == forecast_trends) * 100
    
    def _calculate_directional_accuracy(self, actual: np.ndarray, forecast: np.ndarray) -> float:
        """Calculate directional accuracy (up/down predictions)"""
        if len(actual) < 2:
            return 0.0
        
        actual_direction = np.sign(np.diff(actual))
        forecast_direction = np.sign(np.diff(forecast))
        
        return np.mean(actual_direction == forecast_direction) * 100
    
    def _calculate_seasonal_accuracy(self, actual: np.ndarray, forecast: np.ndarray, 
                                   dates: pd.DatetimeIndex) -> float:
        """Calculate seasonal pattern accuracy"""
        if len(actual) < 12:
            return 0.0
        
        # Simple seasonal accuracy based on month-over-month changes
        df = pd.DataFrame({'actual': actual, 'forecast': forecast, 'month': dates.month})
        monthly_avg_actual = df.groupby('month')['actual'].mean()
        monthly_avg_forecast = df.groupby('month')['forecast'].mean()
        
        return 100 - self._calculate_mape(monthly_avg_actual.values, monthly_avg_forecast.values)
    
    def _calculate_descriptive_stats(self, data: np.ndarray) -> Dict[str, float]:
        """Calculate descriptive statistics for data"""
        return {
            'mean': np.mean(data),
            'std': np.std(data),
            'median': np.median(data),
            'min': np.min(data),
            'max': np.max(data),
            'skewness': stats.skew(data),
            'kurtosis': stats.kurtosis(data)
        }
    
    def _compare_performance(self, current_metrics: PerformanceMetrics) -> Dict[str, Any]:
        """Compare current performance against original benchmarks"""
        if not self.original_performance:
            return {'error': 'No original performance benchmarks available'}
        
        comparison = {}
        
        if 'mape' in self.original_performance:
            mape_change = (current_metrics.mape - self.original_performance['mape']) / self.original_performance['mape']
            comparison['mape_degradation'] = mape_change
            comparison['mape_status'] = self._get_performance_status(mape_change)
        
        if 'mae' in self.original_performance:
            mae_change = (current_metrics.mae - self.original_performance['mae']) / self.original_performance['mae']
            comparison['mae_degradation'] = mae_change
            comparison['mae_status'] = self._get_performance_status(mae_change)
        
        return comparison
    
    def _get_performance_status(self, degradation: float) -> str:
        """Get performance status based on degradation level"""
        if degradation <= 0:
            return 'improved'
        elif degradation <= config.monitoring.performance_degradation_warning:
            return 'stable'
        elif degradation <= config.monitoring.performance_degradation_critical:
            return 'degraded'
        else:
            return 'critical'
    
    def _generate_alerts(self, metrics: PerformanceMetrics, comparison: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate alerts based on performance metrics"""
        alerts = []
        timestamp = datetime.now()
        
        # MAPE alerts
        if metrics.mape > config.monitoring.mape_critical_threshold:
            alerts.append({
                'timestamp': timestamp,
                'type': 'CRITICAL',
                'metric': 'MAPE',
                'value': metrics.mape,
                'threshold': config.monitoring.mape_critical_threshold,
                'message': f'MAPE ({metrics.mape:.2f}%) exceeds critical threshold ({config.monitoring.mape_critical_threshold}%)'
            })
        elif metrics.mape > config.monitoring.mape_warning_threshold:
            alerts.append({
                'timestamp': timestamp,
                'type': 'WARNING',
                'metric': 'MAPE',
                'value': metrics.mape,
                'threshold': config.monitoring.mape_warning_threshold,
                'message': f'MAPE ({metrics.mape:.2f}%) exceeds warning threshold ({config.monitoring.mape_warning_threshold}%)'
            })
        
        # Bias alerts
        if abs(metrics.bias) > config.monitoring.bias_threshold:
            alerts.append({
                'timestamp': timestamp,
                'type': 'WARNING',
                'metric': 'BIAS',
                'value': metrics.bias,
                'threshold': config.monitoring.bias_threshold,
                'message': f'Forecast bias ({metrics.bias:.2f}%) exceeds threshold ({config.monitoring.bias_threshold}%)'
            })
        
        return alerts
    
    def _get_recommendation(self, comparison: Dict[str, Any], alerts: List[Dict[str, Any]]) -> str:
        """Get recommendation based on performance analysis"""
        if not alerts:
            return "CONTINUE_MONITORING"
        
        critical_alerts = [a for a in alerts if a['type'] == 'CRITICAL']
        
        if critical_alerts:
            return "IMMEDIATE_RETRAIN"
        elif len(alerts) >= 2:
            return "SCHEDULE_RETRAIN"
        else:
            return "INVESTIGATE"
    
    def _assess_drift_severity(self, drift_results: Dict[str, Any]) -> str:
        """Assess the severity of detected data drift"""
        severity_score = 0
        
        if drift_results['ks_test']['drift_detected']:
            severity_score += 1
        if drift_results['mann_whitney_test']['drift_detected']:
            severity_score += 1
        if drift_results['descriptive_comparison']['significant_change']:
            severity_score += 1
        
        if severity_score == 0:
            return 'none'
        elif severity_score == 1:
            return 'low'
        elif severity_score == 2:
            return 'medium'
        else:
            return 'high'
    
    def _summarize_alert_types(self) -> Dict[str, int]:
        """Summarize alert types from history"""
        alert_types = {}
        for alert in self.alerts_history:
            alert_type = alert['type']
            alert_types[alert_type] = alert_types.get(alert_type, 0) + 1
        return alert_types
    
    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations based on performance history"""
        recommendations = []
        
        if not self.performance_history:
            return ["Set up performance monitoring"]
        
        # Check recent performance trend
        if len(self.performance_history) >= 3:
            recent_mapes = [entry['metrics'].mape for entry in self.performance_history[-3:]]
            if all(recent_mapes[i] > recent_mapes[i-1] for i in range(1, len(recent_mapes))):
                recommendations.append("Performance is consistently degrading - consider retraining")
        
        # Check alert frequency
        recent_alerts = [alert for alert in self.alerts_history 
                        if (datetime.now() - alert['timestamp']).days <= 30]
        if len(recent_alerts) >= 3:
            recommendations.append("High alert frequency - investigate data quality and model assumptions")
        
        if not recommendations:
            recommendations.append("Performance is stable - continue monitoring")
        
        return recommendations

# Example usage
if __name__ == "__main__":
    # Example usage
    monitor = PerformanceMonitor()
    
    # Set original performance benchmarks
    monitor.original_performance = {
        'mape': 12.5,  # Example: 12.5% MAPE on test set
        'mae': 150.0,  # Example: 150 units MAE
        'rmse': 200.0  # Example: 200 units RMSE
    }
    
    # Simulate some performance monitoring
    np.random.seed(42)
    actual_values = np.random.normal(1000, 100, 6)  # 6 months of actual data
    forecast_values = actual_values + np.random.normal(0, 50, 6)  # Add some forecast error
    dates = pd.date_range('2024-01-01', periods=6, freq='M')
    
    # Monitor performance
    result = monitor.monitor_live_performance(actual_values, forecast_values, dates)
    print("Performance monitoring result:")
    print(f"Current MAPE: {result['current_metrics']['mape']:.2f}%")
    print(f"Alerts: {len(result['alerts'])}")
    print(f"Recommendation: {result['recommendation']}")
