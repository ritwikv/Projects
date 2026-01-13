# Time Series Model Maintenance Framework

A comprehensive framework for maintaining time series forecasting models (SARIMA, ARIMA, SARIMAX) with automated monitoring, retraining decisions, and scenario handling.

## 🎯 Overview

This framework addresses the challenge of maintaining time series model accuracy when:
- **Known project impacts** affect forecasted variables
- **Unknown changes** occur in data patterns  
- **Source variable changes** modify the dependent variable composition

Originally designed for monthly forecasting models trained on 36 months of data with 6 months test validation.

## 🏗️ Architecture

### Core Components

1. **Configuration Management** (`config.py`)
   - Centralized configuration for all framework parameters
   - Performance thresholds and monitoring settings
   - Retraining schedules and scenario handling rules

2. **Performance Monitor** (`performance_monitor.py`)
   - Real-time performance tracking against original benchmarks
   - Data drift detection using statistical tests
   - Seasonal performance analysis
   - Automated alerting system

3. **Retraining Manager** (`retraining_manager.py`)
   - Intelligent retraining decision making
   - Multiple retraining strategies (expanding window, rolling window, weighted)
   - Ensemble model creation and management
   - Model validation and diagnostics

4. **Scenario Handler** (`scenario_handler.py`)
   - **Scenario A**: Known impact management with intervention modeling
   - **Scenario B**: Unknown change detection and adaptive responses
   - **Scenario C**: Source variable changes with hierarchical forecasting

5. **Main Framework** (`main_framework.py`)
   - Orchestrates all components
   - Monthly maintenance routines
   - Emergency response capabilities
   - Health reporting and monitoring setup

## 🚀 Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Basic Usage

```python
from time_series_maintenance import TimeSeriesMaintenanceFramework
import pandas as pd
import numpy as np

# Initialize framework
framework = TimeSeriesMaintenanceFramework(
    model_id="sales_forecast_v1",
    original_performance={'mape': 12.5, 'mae': 150.0, 'rmse': 200.0}
)

# Prepare data
actual_values = np.array([1000, 1050, 980, 1100, 1020, 1080])
forecast_values = np.array([995, 1040, 990, 1090, 1030, 1070])
dates = pd.date_range('2024-01-01', periods=6, freq='M')

# Run monthly maintenance
results = framework.run_monthly_maintenance(
    actual_values=actual_values,
    forecast_values=forecast_values,
    dates=dates
)

print(f"Decision: {results['retraining_decision']['decision']}")
print(f"Recommendations: {results['recommendations']}")
```

## 📊 Key Features

### Performance Monitoring
- **MAPE/MAE/RMSE tracking** against original test benchmarks
- **Bias detection** for systematic forecast errors
- **Trend accuracy** monitoring for directional predictions
- **Seasonal performance** analysis by quarter/month

### Intelligent Retraining
- **Performance degradation** triggers (30% worse than test)
- **Data drift detection** using KS tests and statistical analysis
- **Time-based scheduling** (quarterly/annual retraining)
- **Adaptive training windows** based on change points

### Scenario Management

#### Scenario A: Known Project Impacts
Handle known business changes with intervention modeling using SARIMAX models with step, pulse, ramp, or seasonal intervention variables.

#### Scenario B: Unknown Changes
Detect structural breaks using change point detection algorithms (PELT, Binary Segmentation) and respond with adaptive ensemble methods.

#### Scenario C: Source Variable Changes
Manage changes in dependent variable composition using hierarchical forecasting with bottom-up or top-down reconciliation.

## ⚙️ Configuration

Customize performance thresholds, retraining frequencies, and scenario handling parameters through the centralized configuration system.

## 📈 Monitoring and Alerting

Generate comprehensive health reports with model freshness assessment, performance trends, and actionable recommendations.

## 🔧 Advanced Features

- **Intervention modeling** for known business impacts
- **Change point detection** for unknown structural breaks
- **Ensemble forecasting** for uncertainty periods
- **Emergency response** for critical performance issues
- **Hierarchical forecasting** for component-level changes

## 📋 Best Practices

### Monthly Maintenance Routine
1. **Performance Review**: Check MAPE against original 6M test benchmark
2. **Data Quality**: Validate recent actuals vs forecasts
3. **Drift Detection**: Run statistical tests on recent vs historical data
4. **Scenario Assessment**: Review known changes and detect unknown patterns
5. **Action Execution**: Implement retraining or interventions as needed

### Performance Benchmarks
- **Target MAPE**: <15% for stable periods, <20% during transitions
- **Bias threshold**: <±5% systematic error
- **Trend accuracy**: >80% directional accuracy
- **Health score**: >70/100 for production models

## 📚 Documentation

See the `examples/` directory for comprehensive usage examples and the complete documentation for detailed API reference.

---

**Framework Version**: 1.0.0  
**Compatible Models**: SARIMA, ARIMA, SARIMAX  
**Data Frequency**: Monthly (adaptable to other frequencies)  
**Python Version**: 3.8+
