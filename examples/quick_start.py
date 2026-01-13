"""
Quick Start Example for Time Series Model Maintenance Framework
Demonstrates basic usage and key features
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

# Add the time_series_maintenance module to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def generate_sample_data():
    """Generate sample time series data for demonstration"""
    np.random.seed(42)
    
    # Generate 42 months of historical data (36 train + 6 test)
    dates = pd.date_range('2021-01-01', periods=42, freq='M')
    
    # Base trend with seasonality
    trend = np.linspace(1000, 1200, 42)
    seasonal = 50 * np.sin(2 * np.pi * np.arange(42) / 12)
    noise = np.random.normal(0, 30, 42)
    
    historical_data = trend + seasonal + noise
    historical_series = pd.Series(historical_data, index=dates)
    
    # Generate recent actual values (last 6 months)
    recent_dates = pd.date_range('2024-07-01', periods=6, freq='M')
    recent_actual = np.array([1350, 1380, 1320, 1400, 1360, 1420])
    
    # Generate corresponding forecasts (with some error)
    recent_forecast = recent_actual + np.random.normal(0, 40, 6)
    
    return historical_series, recent_actual, recent_forecast, recent_dates

def main():
    """Main demonstration function"""
    print("Time Series Model Maintenance Framework - Quick Start")
    print("="*60)
    
    # Generate sample data
    historical_data, recent_actual, recent_forecast, recent_dates = generate_sample_data()
    
    print(f"Sample data generated:")
    print(f"  - Historical data: {len(historical_data)} months")
    print(f"  - Recent actual values: {len(recent_actual)} months")
    print(f"  - Date range: {recent_dates[0].strftime('%Y-%m')} to {recent_dates[-1].strftime('%Y-%m')}")
    
    # Calculate basic performance metrics
    mape = np.mean(np.abs((recent_actual - recent_forecast) / recent_actual)) * 100
    mae = np.mean(np.abs(recent_actual - recent_forecast))
    rmse = np.sqrt(np.mean((recent_actual - recent_forecast) ** 2))
    
    print(f"\nCurrent Performance Metrics:")
    print(f"  - MAPE: {mape:.2f}%")
    print(f"  - MAE: {mae:.2f}")
    print(f"  - RMSE: {rmse:.2f}")
    
    # Simulate original test performance (from 36M+6M setup)
    original_performance = {
        'mape': 12.5,  # Original 6-month test MAPE
        'mae': 150.0,  # Original 6-month test MAE
        'rmse': 200.0  # Original 6-month test RMSE
    }
    
    print(f"\nOriginal Test Performance (Benchmark):")
    print(f"  - MAPE: {original_performance['mape']:.2f}%")
    print(f"  - MAE: {original_performance['mae']:.2f}")
    print(f"  - RMSE: {original_performance['rmse']:.2f}")
    
    # Performance comparison
    mape_degradation = (mape - original_performance['mape']) / original_performance['mape']
    print(f"\nPerformance Analysis:")
    print(f"  - MAPE degradation: {mape_degradation*100:.1f}%")
    
    if mape_degradation > 0.3:
        print("  ⚠️ Performance has degraded significantly (>30%)")
        recommendation = "IMMEDIATE_RETRAIN"
    elif mape_degradation > 0.15:
        print("  ⚠️ Performance degradation detected (>15%)")
        recommendation = "SCHEDULE_RETRAIN"
    else:
        print("  ✅ Performance is stable")
        recommendation = "CONTINUE_MONITORING"
    
    print(f"  - Recommendation: {recommendation}")
    
    # Scenario examples
    print(f"\n" + "="*60)
    print("SCENARIO EXAMPLES")
    print("="*60)
    
    # Scenario A: Known impacts
    print(f"\nScenario A: Known Project Impacts")
    known_impacts = [
        {
            'date': '2024-03-01',
            'type': 'step',
            'severity': 'high',
            'description': 'New product launch affecting demand'
        },
        {
            'date': '2024-06-01',
            'type': 'ramp',
            'severity': 'medium',
            'description': 'Marketing campaign rollout'
        }
    ]
    
    print(f"  Known impacts to handle: {len(known_impacts)}")
    for i, impact in enumerate(known_impacts, 1):
        print(f"    {i}. {impact['description']} ({impact['type']}) - {impact['severity']} severity")
    
    print(f"  Recommended action: Create intervention model with SARIMAX")
    
    # Scenario B: Unknown changes
    print(f"\nScenario B: Unknown Changes")
    print(f"  Change point detection would analyze recent data patterns")
    print(f"  If structural breaks detected: Create adaptive ensemble")
    print(f"  Current data shows: {'Potential change detected' if mape_degradation > 0.2 else 'No significant changes'}")
    
    # Scenario C: Source changes
    print(f"\nScenario C: Source Variable Changes")
    print(f"  Example: New product line added to total sales")
    print(f"  Recommended action: Implement hierarchical forecasting")
    print(f"  Method: Bottom-up reconciliation of component forecasts")
    
    # Framework capabilities summary
    print(f"\n" + "="*60)
    print("FRAMEWORK CAPABILITIES")
    print("="*60)
    
    capabilities = [
        "✅ Performance monitoring against original benchmarks",
        "✅ Data drift detection using statistical tests",
        "✅ Intelligent retraining decisions",
        "✅ Known impact handling with intervention modeling",
        "✅ Unknown change detection and adaptive responses",
        "✅ Source variable changes with hierarchical forecasting",
        "✅ Emergency response for critical issues",
        "✅ Comprehensive health reporting",
        "✅ Configurable thresholds and schedules"
    ]
    
    for capability in capabilities:
        print(f"  {capability}")
    
    # Next steps
    print(f"\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)
    
    next_steps = [
        "1. Install required dependencies: pip install -r requirements.txt",
        "2. Configure performance thresholds for your use case",
        "3. Set up data sources and model pipeline integration",
        "4. Implement monthly maintenance routine",
        "5. Establish monitoring and alerting procedures",
        "6. Test with your actual historical data",
        "7. Deploy automated monitoring pipeline"
    ]
    
    for step in next_steps:
        print(f"  {step}")
    
    print(f"\n" + "="*60)
    print("FRAMEWORK READY FOR IMPLEMENTATION")
    print("="*60)

if __name__ == "__main__":
    main()
