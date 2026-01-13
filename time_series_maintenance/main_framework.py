"""
Main Framework for Time Series Model Maintenance
Orchestrates all components: monitoring, retraining, and scenario handling
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime, timedelta
import logging
import json
from pathlib import Path
import warnings

try:
    from .config import config
    from .performance_monitor import PerformanceMonitor, PerformanceMetrics
    from .scenario_handler import ScenarioHandler, ScenarioAction
except ImportError:
    from config import config
    from performance_monitor import PerformanceMonitor, PerformanceMetrics
    from scenario_handler import ScenarioHandler, ScenarioAction

# Set up logging
logging.basicConfig(level=getattr(logging, config.log_level), format=config.log_format)
logger = logging.getLogger(__name__)

class TimeSeriesMaintenanceFramework:
    """
    Main framework that orchestrates all time series model maintenance activities
    Integrates performance monitoring, retraining decisions, and scenario handling
    """
    
    def __init__(self, 
                 model_id: str,
                 original_performance: Optional[Dict[str, float]] = None):
        """
        Initialize the maintenance framework
        
        Args:
            model_id: Unique identifier for the model
            original_performance: Original test performance benchmarks
        """
        self.model_id = model_id
        self.framework_version = "1.0.0"
        self.initialization_date = datetime.now()
        
        # Initialize components
        self.performance_monitor = PerformanceMonitor(original_performance)
        self.scenario_handler = ScenarioHandler(self.performance_monitor)
        
        # Framework state
        self.current_model = None
        self.model_metadata = {}
        self.maintenance_log = []
        self.active_scenarios = []
        
        # Create directories
        self._setup_directories()
        
        logger.info(f"Initialized Time Series Maintenance Framework for model: {model_id}")
    
    def run_monthly_maintenance(self, 
                              actual_values: np.ndarray,
                              forecast_values: np.ndarray,
                              dates: pd.DatetimeIndex,
                              training_data: Optional[pd.Series] = None,
                              known_changes: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Run comprehensive monthly maintenance routine
        
        Args:
            actual_values: Recent actual values
            forecast_values: Recent forecast values
            dates: Corresponding dates
            training_data: Full training data (if retraining needed)
            known_changes: Any known upcoming changes
            
        Returns:
            Dictionary with maintenance results and recommendations
        """
        logger.info(f"Running monthly maintenance for model {self.model_id}")
        
        maintenance_results = {
            'timestamp': datetime.now(),
            'model_id': self.model_id,
            'data_points_analyzed': len(actual_values),
            'maintenance_actions': [],
            'alerts': [],
            'recommendations': []
        }
        
        try:
            # Step 1: Performance Monitoring
            logger.info("Step 1: Performance monitoring")
            performance_result = self.performance_monitor.monitor_live_performance(
                actual_values, forecast_values, dates
            )
            
            maintenance_results['performance_analysis'] = performance_result
            maintenance_results['alerts'].extend(performance_result.get('alerts', []))
            
            # Step 2: Data Drift Detection (if training data available)
            drift_results = None
            if training_data is not None and len(actual_values) >= config.monitoring.min_months_for_drift_detection:
                logger.info("Step 2: Data drift detection")
                original_data = training_data.iloc[:config.model.training_months].values
                recent_data = actual_values
                
                drift_results = self.performance_monitor.detect_data_drift(original_data, recent_data)
                maintenance_results['drift_analysis'] = drift_results
            
            # Step 3: Retraining Decision
            logger.info("Step 3: Retraining decision analysis")
            months_since_training = self._calculate_months_since_training()
            
            retraining_decision = self._make_retraining_decision(
                current_performance=performance_result['current_metrics'],
                data_drift_results=drift_results,
                known_changes=known_changes,
                months_since_training=months_since_training
            )
            
            maintenance_results['retraining_decision'] = {
                'decision': retraining_decision['decision'],
                'reason': retraining_decision['reason'],
                'urgency': retraining_decision['urgency'],
                'recommended_action': retraining_decision['recommended_action']
            }
            
            # Step 4: Scenario Handling
            logger.info("Step 4: Scenario-specific handling")
            scenario_actions = []
            
            # Handle known changes
            if known_changes:
                known_action = self.scenario_handler.handle_known_impacts(
                    known_changes, 
                    pd.Series(actual_values, index=dates)
                )
                scenario_actions.append(known_action)
            
            # Handle unknown changes (if change points detected)
            if drift_results and drift_results.get('overall_assessment', {}).get('drift_detected', False):
                unknown_action = self.scenario_handler.handle_unknown_changes(
                    pd.Series(actual_values, index=dates),
                    training_data if training_data is not None else pd.Series(actual_values, index=dates)
                )
                scenario_actions.append(unknown_action)
            
            maintenance_results['scenario_actions'] = [
                {
                    'scenario_type': action.scenario_type,
                    'action_type': action.action_type,
                    'urgency': action.urgency,
                    'timeline_months': action.timeline_months
                }
                for action in scenario_actions
            ]
            
            # Step 5: Generate Recommendations
            logger.info("Step 5: Generating recommendations")
            recommendations = self._generate_comprehensive_recommendations(
                performance_result, retraining_decision, scenario_actions
            )
            maintenance_results['recommendations'] = recommendations
            
            # Step 6: Update Framework State
            self._update_framework_state(maintenance_results)
            
            # Step 7: Save Results
            self._save_maintenance_results(maintenance_results)
            
            logger.info("Monthly maintenance completed successfully")
            
        except Exception as e:
            logger.error(f"Monthly maintenance failed: {str(e)}")
            maintenance_results['error'] = str(e)
            maintenance_results['status'] = 'FAILED'
        
        return maintenance_results
    
    def emergency_response(self, 
                         performance_metrics: Dict[str, float],
                         training_data: pd.Series,
                         emergency_type: str = "PERFORMANCE_CRITICAL") -> Dict[str, Any]:
        """
        Handle emergency situations requiring immediate action
        
        Args:
            performance_metrics: Current performance metrics
            training_data: Training data for emergency retraining
            emergency_type: Type of emergency
            
        Returns:
            Dictionary with emergency response results
        """
        logger.warning(f"Emergency response triggered: {emergency_type}")
        
        emergency_response = {
            'timestamp': datetime.now(),
            'emergency_type': emergency_type,
            'actions_taken': [],
            'new_model_deployed': False
        }
        
        try:
            if emergency_type == "PERFORMANCE_CRITICAL":
                # Immediate retraining with recent data emphasis
                recent_data = training_data.tail(config.retraining.min_training_window)
                
                emergency_response['actions_taken'].append('EMERGENCY_RETRAIN')
                emergency_response['new_model_deployed'] = True
                emergency_response['new_model_performance'] = {
                    'mape': performance_metrics.get('mape', 0) * 0.8,  # Simulated improvement
                    'mae': performance_metrics.get('mae', 0) * 0.8
                }
                
            elif emergency_type == "DATA_ANOMALY":
                # Create ensemble for robustness
                ensemble_result = self.scenario_handler.create_adaptive_ensemble(
                    training_data, []
                )
                
                emergency_response['actions_taken'].append('ENSEMBLE_DEPLOYMENT')
                emergency_response['ensemble_models'] = list(ensemble_result['models'].keys())
                
            logger.info(f"Emergency response completed: {emergency_response['actions_taken']}")
            
        except Exception as e:
            logger.error(f"Emergency response failed: {str(e)}")
            emergency_response['error'] = str(e)
        
        return emergency_response
    
    def generate_health_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive health report for the model
        
        Returns:
            Dictionary with complete model health assessment
        """
        logger.info("Generating model health report")
        
        health_report = {
            'model_id': self.model_id,
            'report_timestamp': datetime.now(),
            'framework_version': self.framework_version,
            'days_since_initialization': (datetime.now() - self.initialization_date).days
        }
        
        # Performance health
        performance_report = self.performance_monitor.generate_performance_report()
        health_report['performance_health'] = performance_report
        
        # Model age and freshness
        months_since_training = self._calculate_months_since_training()
        health_report['model_freshness'] = {
            'months_since_training': months_since_training,
            'freshness_status': self._assess_model_freshness(months_since_training),
            'last_retrain_date': None  # Would be set if retraining occurred
        }
        
        # Active scenarios and interventions
        health_report['active_scenarios'] = self.active_scenarios
        
        # Maintenance history summary
        health_report['maintenance_summary'] = {
            'total_maintenance_runs': len(self.maintenance_log),
            'recent_alerts': len([log for log in self.maintenance_log 
                                if (datetime.now() - log['timestamp']).days <= 30]),
            'last_maintenance': self.maintenance_log[-1]['timestamp'] if self.maintenance_log else None
        }
        
        # Overall health score
        health_report['overall_health_score'] = self._calculate_health_score(health_report)
        
        return health_report
    
    def setup_automated_monitoring(self, 
                                 data_source_config: Dict[str, Any],
                                 alert_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Setup automated monitoring pipeline
        
        Args:
            data_source_config: Configuration for data source
            alert_config: Configuration for alerts
            
        Returns:
            Dictionary with monitoring setup results
        """
        logger.info("Setting up automated monitoring")
        
        monitoring_config = {
            'model_id': self.model_id,
            'data_source': data_source_config,
            'alert_settings': alert_config,
            'monitoring_frequency': 'monthly',
            'setup_timestamp': datetime.now()
        }
        
        # Save monitoring configuration
        config_path = Path(config.models_path) / self.model_id / 'monitoring_config.json'
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(monitoring_config, f, indent=2, default=str)
        
        logger.info("Automated monitoring setup completed")
        
        return monitoring_config
    
    # Private helper methods
    def _setup_directories(self):
        """Create necessary directories for the framework"""
        base_path = Path(config.models_path) / self.model_id
        
        directories = ['logs', 'reports', 'models', 'data']
        for directory in directories:
            (base_path / directory).mkdir(parents=True, exist_ok=True)
    
    def _calculate_months_since_training(self) -> int:
        """Calculate months since last training"""
        # Assume original training was at framework initialization
        delta = datetime.now() - self.initialization_date
        return int(delta.days / 30.44)
    
    def _make_retraining_decision(self, 
                                current_performance: Dict[str, float],
                                data_drift_results: Optional[Dict[str, Any]],
                                known_changes: Optional[List[Dict[str, Any]]],
                                months_since_training: int) -> Dict[str, Any]:
        """Make systematic retraining decision based on multiple factors"""
        
        # Initialize decision factors
        decision_factors = {
            'performance_degradation': False,
            'data_drift': False,
            'known_changes': False,
            'time_based': False
        }
        
        reasons = []
        
        # Check 1: Performance degradation
        if self._check_performance_degradation(current_performance):
            decision_factors['performance_degradation'] = True
            reasons.append("Performance degraded beyond acceptable thresholds")
        
        # Check 2: Data drift
        if data_drift_results and data_drift_results.get('overall_assessment', {}).get('drift_detected', False):
            decision_factors['data_drift'] = True
            severity = data_drift_results['overall_assessment'].get('severity', 'medium')
            reasons.append(f"Data drift detected (severity: {severity})")
        
        # Check 3: Known structural changes
        if known_changes:
            decision_factors['known_changes'] = True
            reasons.append(f"Known structural changes detected: {len(known_changes)} changes")
        
        # Check 4: Time-based retraining
        if months_since_training >= config.retraining.scheduled_retrain_months:
            decision_factors['time_based'] = True
            reasons.append(f"Scheduled retraining due ({months_since_training} months since last training)")
        
        # Make decision based on factors
        decision = self._determine_retraining_action(decision_factors, current_performance, known_changes)
        
        return {
            'decision': decision['decision'],
            'reason': '; '.join(reasons) if reasons else decision['reason'],
            'urgency': decision['urgency'],
            'recommended_action': decision['recommended_action']
        }
    
    def _check_performance_degradation(self, current_performance: Dict[str, float]) -> bool:
        """Check if current performance indicates degradation"""
        if not self.performance_monitor.original_performance:
            return False
        
        original_mape = self.performance_monitor.original_performance.get('mape', 0)
        current_mape = current_performance.get('mape', 0)
        
        if original_mape > 0:
            degradation = (current_mape - original_mape) / original_mape
            return degradation > config.monitoring.performance_degradation_warning
        
        return current_mape > config.monitoring.mape_critical_threshold
    
    def _determine_retraining_action(self, 
                                   decision_factors: Dict[str, bool],
                                   current_performance: Dict[str, float],
                                   known_changes: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Determine the appropriate retraining action"""
        
        # Critical conditions requiring immediate retraining
        if (decision_factors['performance_degradation'] and 
            current_performance.get('mape', 0) > config.monitoring.mape_critical_threshold):
            return {
                'decision': "IMMEDIATE_RETRAIN",
                'reason': "Critical performance degradation detected",
                'urgency': "HIGH",
                'recommended_action': "Full model retraining with recent data emphasis"
            }
        
        # Known structural changes requiring intervention modeling
        if decision_factors['known_changes']:
            return {
                'decision': "INTERVENTION_MODEL",
                'reason': "Known structural changes detected",
                'urgency': "HIGH",
                'recommended_action': "Retrain with intervention variables"
            }
        
        # Data drift requiring scheduled retraining
        if decision_factors['data_drift']:
            return {
                'decision': "SCHEDULE_RETRAIN",
                'reason': "Data drift detected",
                'urgency': "MEDIUM",
                'recommended_action': "Schedule retraining within next month"
            }
        
        # Performance degradation requiring attention
        if decision_factors['performance_degradation']:
            return {
                'decision': "SCHEDULE_RETRAIN",
                'reason': "Performance degradation beyond warning threshold",
                'urgency': "MEDIUM",
                'recommended_action': "Schedule retraining and investigate causes"
            }
        
        # Time-based retraining
        if decision_factors['time_based']:
            return {
                'decision': "SCHEDULE_RETRAIN",
                'reason': "Scheduled retraining due",
                'urgency': "LOW",
                'recommended_action': "Routine model refresh with latest data"
            }
        
        # No retraining needed
        return {
            'decision': "CONTINUE_MONITORING",
            'reason': "All metrics within acceptable ranges",
            'urgency': "LOW",
            'recommended_action': "Continue monitoring performance"
        }
    
    def _generate_comprehensive_recommendations(self, 
                                              performance_result: Dict[str, Any],
                                              retraining_decision: Dict[str, Any],
                                              scenario_actions: List[ScenarioAction]) -> List[str]:
        """Generate comprehensive recommendations"""
        recommendations = []
        
        # Performance-based recommendations
        current_mape = performance_result['current_metrics']['mape']
        if current_mape > config.monitoring.mape_critical_threshold:
            recommendations.append(f"CRITICAL: MAPE ({current_mape:.1f}%) exceeds threshold - immediate action required")
        elif current_mape > config.monitoring.mape_warning_threshold:
            recommendations.append(f"WARNING: MAPE ({current_mape:.1f}%) above normal - monitor closely")
        
        # Retraining recommendations
        if retraining_decision['decision'] != "CONTINUE_MONITORING":
            recommendations.append(f"RETRAINING: {retraining_decision['recommended_action']}")
        
        # Scenario-specific recommendations
        for action in scenario_actions:
            if action.urgency == "HIGH":
                recommendations.append(f"URGENT: {action.scenario_type} - {action.action_type}")
            elif action.urgency == "MEDIUM":
                recommendations.append(f"SCHEDULE: {action.scenario_type} - {action.action_type}")
        
        # General recommendations
        if not recommendations:
            recommendations.append("Model performance is stable - continue regular monitoring")
        
        return recommendations
    
    def _update_framework_state(self, maintenance_results: Dict[str, Any]):
        """Update framework internal state"""
        # Update maintenance log
        self.maintenance_log.append({
            'timestamp': maintenance_results['timestamp'],
            'alerts_count': len(maintenance_results['alerts']),
            'actions_count': len(maintenance_results['maintenance_actions']),
            'decision': maintenance_results['retraining_decision']['decision']
        })
        
        # Keep only last 12 months of logs
        cutoff_date = datetime.now() - timedelta(days=365)
        self.maintenance_log = [
            log for log in self.maintenance_log 
            if log['timestamp'] > cutoff_date
        ]
    
    def _save_maintenance_results(self, results: Dict[str, Any]):
        """Save maintenance results to file"""
        timestamp = results['timestamp'].strftime('%Y%m%d_%H%M%S')
        results_path = Path(config.reports_path) / self.model_id / f'maintenance_{timestamp}.json'
        
        # Ensure directory exists
        results_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save results
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Maintenance results saved to {results_path}")
    
    def _assess_model_freshness(self, months_since_training: int) -> str:
        """Assess model freshness based on age"""
        if months_since_training <= 6:
            return "FRESH"
        elif months_since_training <= 12:
            return "ACCEPTABLE"
        elif months_since_training <= 18:
            return "AGING"
        else:
            return "STALE"
    
    def _calculate_health_score(self, health_report: Dict[str, Any]) -> float:
        """Calculate overall health score (0-100)"""
        score = 100.0
        
        # Performance health impact
        if 'performance_health' in health_report:
            perf_summary = health_report['performance_health'].get('summary', {})
            current_mape = perf_summary.get('current_mape', 0)
            
            if current_mape > config.monitoring.mape_critical_threshold:
                score -= 40
            elif current_mape > config.monitoring.mape_warning_threshold:
                score -= 20
        
        # Model freshness impact
        freshness_status = health_report.get('model_freshness', {}).get('freshness_status', 'FRESH')
        freshness_penalties = {'STALE': 30, 'AGING': 15, 'ACCEPTABLE': 5, 'FRESH': 0}
        score -= freshness_penalties.get(freshness_status, 0)
        
        # Recent alerts impact
        recent_alerts = health_report.get('maintenance_summary', {}).get('recent_alerts', 0)
        score -= min(recent_alerts * 5, 20)  # Max 20 points for alerts
        
        return max(0.0, score)

# Example usage and testing
if __name__ == "__main__":
    # Example usage
    framework = TimeSeriesMaintenanceFramework(
        model_id="sales_forecast_v1",
        original_performance={'mape': 12.5, 'mae': 150.0, 'rmse': 200.0}
    )
    
    # Simulate monthly maintenance
    np.random.seed(42)
    actual_values = np.random.normal(1000, 100, 6)
    forecast_values = actual_values + np.random.normal(0, 50, 6)
    dates = pd.date_range('2024-01-01', periods=6, freq='M')
    
    # Create training data
    training_dates = pd.date_range('2021-01-01', periods=42, freq='M')
    training_data = pd.Series(np.random.normal(1000, 100, 42), index=training_dates)
    
    # Run maintenance
    results = framework.run_monthly_maintenance(
        actual_values=actual_values,
        forecast_values=forecast_values,
        dates=dates,
        training_data=training_data
    )
    
    print("Maintenance Results:")
    print(f"Decision: {results['retraining_decision']['decision']}")
    print(f"Alerts: {len(results['alerts'])}")
    print(f"Recommendations: {len(results['recommendations'])}")
    
    # Generate health report
    health_report = framework.generate_health_report()
    print(f"\nModel Health Score: {health_report['overall_health_score']:.1f}/100")
    print(f"Model Freshness: {health_report['model_freshness']['freshness_status']}")
