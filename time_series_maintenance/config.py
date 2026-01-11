"""
Configuration file for Time Series Model Maintenance Framework
Handles all configuration parameters for monthly forecasting models
"""

import pandas as pd
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np

@dataclass
class ModelConfig:
    """Configuration for original model setup"""
    training_months: int = 36
    test_months: int = 6
    forecast_horizon: int = 6
    seasonal_period: int = 12
    
    # Original model performance benchmarks (to be set from your actual results)
    original_test_mape: Optional[float] = None
    original_test_mae: Optional[float] = None
    original_test_rmse: Optional[float] = None
    
    # Model parameters (adjust based on your actual models)
    sarima_order: Tuple[int, int, int] = (1, 1, 1)
    seasonal_order: Tuple[int, int, int, int] = (1, 1, 1, 12)

@dataclass
class MonitoringConfig:
    """Configuration for performance monitoring"""
    # Performance thresholds
    mape_warning_threshold: float = 15.0  # 15% MAPE triggers investigation
    mape_critical_threshold: float = 25.0  # 25% MAPE triggers immediate retraining
    bias_threshold: float = 10.0  # 10% systematic bias
    trend_deviation_threshold: float = 20.0  # 20% trend direction error
    
    # Performance degradation thresholds
    performance_degradation_warning: float = 0.3  # 30% worse than test performance
    performance_degradation_critical: float = 0.5  # 50% worse than test performance
    
    # Data drift detection
    drift_significance_level: float = 0.05  # p-value for statistical tests
    min_months_for_drift_detection: int = 3  # Minimum months of data for drift detection

@dataclass
class RetrainingConfig:
    """Configuration for retraining decisions and schedules"""
    # Retraining frequency
    scheduled_retrain_months: int = 12  # Full retrain every 12 months
    parameter_update_months: int = 3  # Light parameter updates every 3 months
    
    # Change point detection
    min_months_between_changes: int = 6  # Minimum 6 months between detected changes
    change_confirmation_months: int = 3  # Require 3 months of consistent change
    
    # Training window strategies
    min_training_window: int = 18  # Minimum 18 months for training
    max_training_window: int = 60  # Maximum 60 months for training
    
    # Ensemble configuration
    ensemble_models: List[str] = None
    
    def __post_init__(self):
        if self.ensemble_models is None:
            self.ensemble_models = ['seasonal_focus', 'trend_focus', 'balanced']

@dataclass
class ScenarioConfig:
    """Configuration for handling different scenarios"""
    # Known impact scenarios
    intervention_lead_time_months: int = 2  # Plan interventions 2 months ahead
    intervention_validation_months: int = 3  # 3-month validation period
    intervention_rollout_months: int = 3  # Gradual rollout over 3 months
    
    # Unknown change scenarios
    change_detection_window: int = 6  # 6-month rolling window for detection
    fallback_model_retention_months: int = 6  # Keep previous model for 6 months
    
    # Source variable change scenarios
    source_change_retrain_months: int = 1  # Retrain within 1 month of source changes
    hierarchical_validation_months: int = 3  # 3-month validation for hierarchical models

class GlobalConfig:
    """Main configuration class that combines all configurations"""
    
    def __init__(self):
        self.model = ModelConfig()
        self.monitoring = MonitoringConfig()
        self.retraining = RetrainingConfig()
        self.scenarios = ScenarioConfig()
        
        # File paths
        self.data_path = "data/"
        self.models_path = "models/"
        self.logs_path = "logs/"
        self.reports_path = "reports/"
        
        # Logging configuration
        self.log_level = "INFO"
        self.log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    def update_original_performance(self, test_mape: float, test_mae: float, test_rmse: float):
        """Update original model performance benchmarks"""
        self.model.original_test_mape = test_mape
        self.model.original_test_mae = test_mae
        self.model.original_test_rmse = test_rmse
    
    def get_performance_thresholds(self) -> Dict[str, float]:
        """Get all performance thresholds in a dictionary"""
        return {
            'mape_warning': self.monitoring.mape_warning_threshold,
            'mape_critical': self.monitoring.mape_critical_threshold,
            'bias_threshold': self.monitoring.bias_threshold,
            'trend_deviation': self.monitoring.trend_deviation_threshold,
            'degradation_warning': self.monitoring.performance_degradation_warning,
            'degradation_critical': self.monitoring.performance_degradation_critical
        }
    
    def validate_config(self) -> bool:
        """Validate configuration parameters"""
        try:
            # Check that training window is sufficient
            assert self.model.training_months >= 24, "Training months should be at least 24"
            
            # Check that test period is reasonable
            assert self.model.test_months >= 3, "Test months should be at least 3"
            
            # Check threshold values are reasonable
            assert 0 < self.monitoring.mape_warning_threshold < 100, "MAPE warning threshold should be between 0 and 100"
            assert self.monitoring.mape_warning_threshold < self.monitoring.mape_critical_threshold, "Critical threshold should be higher than warning"
            
            # Check retraining frequencies
            assert self.retraining.parameter_update_months <= self.retraining.scheduled_retrain_months, "Parameter update frequency should be more frequent than full retrain"
            
            return True
            
        except AssertionError as e:
            print(f"Configuration validation failed: {e}")
            return False

# Global configuration instance
config = GlobalConfig()

if __name__ == "__main__":
    # Test configuration
    test_config = GlobalConfig()
    print("Configuration validation:", test_config.validate_config())
    print("Performance thresholds:", test_config.get_performance_thresholds())
