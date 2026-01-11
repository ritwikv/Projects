"""
Scenario Handler Module for Time Series Models
Handles the three specific scenarios: Known impacts, Unknown changes, Source variable changes
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
import warnings

# Import change point detection
try:
    import ruptures as rpt
except ImportError:
    warnings.warn("ruptures not available. Install with: pip install ruptures")
    rpt = None

try:
    from .config import config
    from .performance_monitor import PerformanceMonitor
except ImportError:
    from config import config
    from performance_monitor import PerformanceMonitor

# Set up logging
logging.basicConfig(level=getattr(logging, config.log_level), format=config.log_format)
logger = logging.getLogger(__name__)

@dataclass
class ScenarioAction:
    """Container for scenario-specific actions"""
    scenario_type: str
    action_type: str
    urgency: str
    implementation_steps: List[str]
    timeline_months: int
    validation_required: bool
    fallback_strategy: str

class ScenarioHandler:
    """
    Handles the three main scenarios for time series model maintenance:
    A. Known project impacts on forecasted/independent variables
    B. Unknown changes in data patterns
    C. Dependent variable source changes (components added/removed)
    """
    
    def __init__(self, 
                 performance_monitor: Optional[PerformanceMonitor] = None):
        """
        Initialize scenario handler
        
        Args:
            performance_monitor: PerformanceMonitor instance
        """
        self.performance_monitor = performance_monitor or PerformanceMonitor()
        self.scenario_history = []
        self.active_interventions = {}
        
    # SCENARIO A: Known Project Impacts
    def handle_known_impacts(self, 
                           impact_details: List[Dict[str, Any]],
                           current_data: pd.Series,
                           lead_time_months: Optional[int] = None) -> ScenarioAction:
        """
        Handle known project impacts on forecasted variables
        
        Args:
            impact_details: List of known impacts with details
            current_data: Current time series data
            lead_time_months: Lead time before impact occurs
            
        Returns:
            ScenarioAction with recommended approach
        """
        logger.info(f"Handling known impacts: {len(impact_details)} impacts identified")
        
        lead_time = lead_time_months or config.scenarios.intervention_lead_time_months
        
        # Categorize impacts by type and timing
        immediate_impacts = []
        future_impacts = []
        
        for impact in impact_details:
            impact_date = pd.to_datetime(impact['date'])
            months_until_impact = (impact_date - datetime.now()).days / 30.44
            
            if months_until_impact <= lead_time:
                immediate_impacts.append(impact)
            else:
                future_impacts.append(impact)
        
        # Determine action based on impact timing and severity
        if immediate_impacts:
            return self._handle_immediate_known_impacts(immediate_impacts, current_data)
        elif future_impacts:
            return self._handle_future_known_impacts(future_impacts, current_data)
        else:
            return ScenarioAction(
                scenario_type="KNOWN_IMPACTS",
                action_type="MONITOR",
                urgency="LOW",
                implementation_steps=["Continue monitoring for new impact announcements"],
                timeline_months=1,
                validation_required=False,
                fallback_strategy="Standard monitoring"
            )
    
    def create_intervention_model(self, 
                                training_data: pd.Series,
                                interventions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create SARIMAX model with intervention variables
        
        Args:
            training_data: Historical time series data
            interventions: List of intervention specifications
            
        Returns:
            Dictionary with intervention model and variables
        """
        logger.info(f"Creating intervention model with {len(interventions)} interventions")
        
        # Create intervention variables
        intervention_matrix = self._create_intervention_matrix(training_data.index, interventions)
        
        # Prepare future intervention variables for forecasting
        future_dates = pd.date_range(
            start=training_data.index[-1] + pd.DateOffset(months=1),
            periods=config.model.forecast_horizon,
            freq='M'
        )
        future_intervention_matrix = self._create_intervention_matrix(future_dates, interventions)
        
        return {
            'intervention_matrix': intervention_matrix,
            'future_intervention_matrix': future_intervention_matrix,
            'interventions': interventions,
            'status': 'created'
        }
    
    # SCENARIO B: Unknown Changes
    def handle_unknown_changes(self, 
                             recent_data: pd.Series,
                             historical_data: pd.Series,
                             detection_window_months: Optional[int] = None) -> ScenarioAction:
        """
        Handle unknown changes in data patterns
        
        Args:
            recent_data: Recent time series data
            historical_data: Historical baseline data
            detection_window_months: Window for change detection
            
        Returns:
            ScenarioAction with recommended approach
        """
        logger.info("Detecting and handling unknown changes in data patterns")
        
        detection_window = detection_window_months or config.scenarios.change_detection_window
        
        # Detect change points
        change_points = self.detect_change_points(recent_data, detection_window)
        
        # Assess change significance
        change_assessment = self._assess_change_significance(
            recent_data, historical_data, change_points
        )
        
        # Determine response strategy
        if change_assessment['significant_change']:
            return self._handle_significant_unknown_change(
                recent_data, historical_data, change_assessment
            )
        elif change_assessment['potential_change']:
            return self._handle_potential_unknown_change(
                recent_data, change_assessment
            )
        else:
            return ScenarioAction(
                scenario_type="UNKNOWN_CHANGES",
                action_type="CONTINUE_MONITORING",
                urgency="LOW",
                implementation_steps=["Continue change point monitoring"],
                timeline_months=1,
                validation_required=False,
                fallback_strategy="Standard monitoring"
            )
    
    def detect_change_points(self, 
                           time_series: pd.Series,
                           detection_window: int,
                           method: str = "pelt") -> Dict[str, Any]:
        """
        Detect change points in time series data
        
        Args:
            time_series: Time series data
            detection_window: Window size for detection
            method: Change point detection method
            
        Returns:
            Dictionary with change point detection results
        """
        logger.info(f"Detecting change points using {method} method")
        
        try:
            if rpt is None:
                logger.warning("ruptures package not available, using simple statistical method")
                return self._simple_change_detection(time_series, detection_window)
            
            # Use recent data for change point detection
            recent_data = time_series.tail(detection_window).values
            
            if method == "pelt":
                # PELT (Pruned Exact Linear Time) algorithm
                algo = rpt.Pelt(model="rbf", min_size=config.retraining.min_months_between_changes)
                algo.fit(recent_data)
                change_points = algo.predict(pen=np.log(len(recent_data)) * 2)
                
            elif method == "binseg":
                # Binary Segmentation algorithm
                algo = rpt.Binseg(model="l2", min_size=config.retraining.min_months_between_changes)
                algo.fit(recent_data)
                change_points = algo.predict(n_bkps=3)  # Max 3 change points
                
            else:
                logger.warning(f"Unknown method {method}, using simple detection")
                return self._simple_change_detection(time_series, detection_window)
            
            # Convert to actual dates
            change_dates = []
            if change_points and change_points[0] < len(recent_data):
                for cp in change_points[:-1]:  # Last point is always end of series
                    if cp < len(recent_data):
                        change_date = time_series.tail(detection_window).index[cp]
                        change_dates.append(change_date)
            
            logger.info(f"Detected {len(change_dates)} change points")
            
            return {
                'method': method,
                'change_points_indices': change_points,
                'change_dates': change_dates,
                'detection_window': detection_window,
                'data_length': len(recent_data)
            }
            
        except Exception as e:
            logger.error(f"Change point detection failed: {str(e)}")
            return {
                'method': method,
                'change_points_indices': [],
                'change_dates': [],
                'error': str(e)
            }
    
    def create_adaptive_ensemble(self, 
                               training_data: pd.Series,
                               change_points: List[pd.Timestamp]) -> Dict[str, Any]:
        """
        Create adaptive ensemble for handling unknown changes
        
        Args:
            training_data: Historical training data
            change_points: Detected change points
            
        Returns:
            Dictionary with adaptive ensemble models
        """
        logger.info("Creating adaptive ensemble for unknown changes")
        
        ensemble_models = {}
        
        # Model 1: Full historical data
        ensemble_models['full_history'] = {
            'data': training_data,
            'description': 'Full historical data model'
        }
        
        # Model 2: Recent data emphasis (post-change)
        if change_points:
            latest_change = max(change_points)
            post_change_data = training_data[training_data.index >= latest_change]
            
            if len(post_change_data) >= config.retraining.min_training_window:
                ensemble_models['post_change'] = {
                    'data': post_change_data,
                    'description': 'Post-change data model'
                }
        
        # Model 3: Rolling window (most recent N months)
        recent_window = min(len(training_data), config.model.training_months)
        recent_data = training_data.tail(recent_window)
        ensemble_models['recent_window'] = {
            'data': recent_data,
            'description': 'Recent window model'
        }
        
        # Calculate dynamic weights based on recent performance
        weights = self._calculate_adaptive_weights(ensemble_models, training_data)
        
        return {
            'models': ensemble_models,
            'weights': weights,
            'change_points': change_points
        }
    
    # SCENARIO C: Source Variable Changes
    def handle_source_changes(self, 
                            source_change_details: Dict[str, Any],
                            historical_components: Dict[str, pd.Series],
                            current_total: pd.Series) -> ScenarioAction:
        """
        Handle changes in dependent variable sources (components added/removed)
        
        Args:
            source_change_details: Details about source changes
            historical_components: Historical component time series
            current_total: Current total time series
            
        Returns:
            ScenarioAction with recommended approach
        """
        logger.info(f"Handling source variable changes: {source_change_details['type']}")
        
        change_type = source_change_details['type']  # 'added', 'removed', 'modified'
        
        if change_type == 'added':
            return self._handle_source_addition(source_change_details, historical_components, current_total)
        elif change_type == 'removed':
            return self._handle_source_removal(source_change_details, historical_components, current_total)
        elif change_type == 'modified':
            return self._handle_source_modification(source_change_details, historical_components, current_total)
        else:
            raise ValueError(f"Unknown source change type: {change_type}")
    
    def implement_hierarchical_forecasting(self, 
                                         component_data: Dict[str, pd.Series],
                                         hierarchy_structure: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Implement hierarchical forecasting for source variable changes
        
        Args:
            component_data: Dictionary of component time series
            hierarchy_structure: Hierarchy structure definition
            
        Returns:
            Dictionary with hierarchical forecasting results
        """
        logger.info("Implementing hierarchical forecasting")
        
        try:
            # Prepare data matrix
            data_matrix = pd.DataFrame(component_data)
            
            # Simple bottom-up reconciliation
            component_forecasts = {}
            
            # Forecast each component separately (simplified approach)
            for component_name, component_series in component_data.items():
                # Simple forecast using last value + trend
                if len(component_series) >= 2:
                    trend = component_series.iloc[-1] - component_series.iloc[-2]
                    forecast = [component_series.iloc[-1] + trend * (i+1) for i in range(config.model.forecast_horizon)]
                else:
                    forecast = [component_series.iloc[-1]] * config.model.forecast_horizon
                
                component_forecasts[component_name] = np.array(forecast)
            
            # Bottom-up reconciliation
            total_forecast = sum(component_forecasts.values())
            
            return {
                'component_forecasts': component_forecasts,
                'reconciled_total': total_forecast,
                'method': 'bottom_up',
                'components': list(component_data.keys())
            }
            
        except Exception as e:
            logger.error(f"Hierarchical forecasting failed: {str(e)}")
            raise
    
    # Private helper methods for Scenario A
    def _handle_immediate_known_impacts(self, 
                                      impacts: List[Dict[str, Any]], 
                                      current_data: pd.Series) -> ScenarioAction:
        """Handle impacts that need immediate attention"""
        high_impact_count = sum(1 for impact in impacts if impact.get('severity', 'medium') == 'high')
        
        if high_impact_count > 0:
            return ScenarioAction(
                scenario_type="KNOWN_IMPACTS",
                action_type="IMMEDIATE_INTERVENTION",
                urgency="HIGH",
                implementation_steps=[
                    "Create intervention variables for known impacts",
                    "Retrain SARIMAX model with intervention terms",
                    "Validate model performance with intervention variables",
                    "Deploy updated model immediately"
                ],
                timeline_months=1,
                validation_required=True,
                fallback_strategy="Use ensemble with original model as backup"
            )
        else:
            return ScenarioAction(
                scenario_type="KNOWN_IMPACTS",
                action_type="SCHEDULED_INTERVENTION",
                urgency="MEDIUM",
                implementation_steps=[
                    "Prepare intervention variables",
                    "Schedule model retraining for next month",
                    "Set up monitoring for impact realization"
                ],
                timeline_months=2,
                validation_required=True,
                fallback_strategy="Gradual rollout with performance monitoring"
            )
    
    def _handle_future_known_impacts(self, 
                                   impacts: List[Dict[str, Any]], 
                                   current_data: pd.Series) -> ScenarioAction:
        """Handle impacts that will occur in the future"""
        return ScenarioAction(
            scenario_type="KNOWN_IMPACTS",
            action_type="PREPARE_INTERVENTION",
            urgency="LOW",
            implementation_steps=[
                "Design intervention variables for future impacts",
                "Set up monitoring alerts for impact dates",
                "Prepare retraining pipeline for when impacts occur",
                "Document intervention strategy"
            ],
            timeline_months=config.scenarios.intervention_lead_time_months,
            validation_required=False,
            fallback_strategy="Standard monitoring until impact occurs"
        )
    
    def _create_intervention_matrix(self, 
                                  date_index: pd.DatetimeIndex,
                                  interventions: List[Dict[str, Any]]) -> pd.DataFrame:
        """Create intervention variable matrix"""
        intervention_df = pd.DataFrame(index=date_index)
        
        for i, intervention in enumerate(interventions):
            intervention_date = pd.to_datetime(intervention['date'])
            intervention_type = intervention.get('type', 'step')
            
            if intervention_type == 'step':
                # Permanent change from intervention_date onwards
                intervention_df[f'step_{i}'] = (date_index >= intervention_date).astype(int)
            
            elif intervention_type == 'pulse':
                # One-time impact in specific month
                intervention_df[f'pulse_{i}'] = (date_index == intervention_date).astype(int)
            
            elif intervention_type == 'ramp':
                # Gradual change over specified months
                ramp_months = intervention.get('duration_months', 6)
                months_since = (date_index - intervention_date).days / 30.44
                intervention_df[f'ramp_{i}'] = np.maximum(0, np.minimum(months_since / ramp_months, 1))
            
            elif intervention_type == 'seasonal':
                # Seasonal intervention (e.g., affects only certain months)
                affected_months = intervention.get('affected_months', [])
                seasonal_effect = np.zeros(len(date_index))
                for j, date in enumerate(date_index):
                    if date >= intervention_date and date.month in affected_months:
                        seasonal_effect[j] = intervention.get('magnitude', 1.0)
                intervention_df[f'seasonal_{i}'] = seasonal_effect
        
        return intervention_df
    
    # Private helper methods for Scenario B
    def _simple_change_detection(self, time_series: pd.Series, detection_window: int) -> Dict[str, Any]:
        """Simple change detection using statistical methods"""
        recent_data = time_series.tail(detection_window)
        
        # Split into two halves and compare means
        mid_point = len(recent_data) // 2
        first_half = recent_data.iloc[:mid_point]
        second_half = recent_data.iloc[mid_point:]
        
        # T-test for mean difference
        from scipy import stats
        t_stat, p_value = stats.ttest_ind(first_half, second_half)
        
        change_detected = p_value < 0.05
        change_dates = [recent_data.index[mid_point]] if change_detected else []
        
        return {
            'method': 'simple_statistical',
            'change_points_indices': [mid_point] if change_detected else [],
            'change_dates': change_dates,
            'detection_window': detection_window,
            'p_value': p_value
        }
    
    def _assess_change_significance(self, 
                                  recent_data: pd.Series,
                                  historical_data: pd.Series,
                                  change_points: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the significance of detected changes"""
        assessment = {
            'significant_change': False,
            'potential_change': False,
            'change_magnitude': 0.0,
            'change_persistence': 0,
            'statistical_significance': False
        }
        
        if not change_points['change_dates']:
            return assessment
        
        # Get most recent change point
        latest_change = max(change_points['change_dates'])
        
        # Data before and after change
        pre_change = recent_data[recent_data.index < latest_change]
        post_change = recent_data[recent_data.index >= latest_change]
        
        if len(pre_change) < 3 or len(post_change) < 3:
            return assessment
        
        # Calculate change magnitude
        pre_mean = pre_change.mean()
        post_mean = post_change.mean()
        change_magnitude = abs((post_mean - pre_mean) / pre_mean) if pre_mean != 0 else 0
        
        assessment['change_magnitude'] = change_magnitude
        assessment['change_persistence'] = len(post_change)
        
        # Statistical significance test
        from scipy import stats
        _, p_value = stats.ttest_ind(pre_change, post_change)
        assessment['statistical_significance'] = p_value < 0.05
        
        # Determine significance level
        if (change_magnitude > 0.2 and  # 20% change
            len(post_change) >= config.retraining.change_confirmation_months and
            assessment['statistical_significance']):
            assessment['significant_change'] = True
        elif change_magnitude > 0.1 or assessment['statistical_significance']:
            assessment['potential_change'] = True
        
        return assessment
    
    def _handle_significant_unknown_change(self, 
                                         recent_data: pd.Series,
                                         historical_data: pd.Series,
                                         change_assessment: Dict[str, Any]) -> ScenarioAction:
        """Handle significant unknown changes"""
        return ScenarioAction(
            scenario_type="UNKNOWN_CHANGES",
            action_type="ADAPTIVE_RETRAINING",
            urgency="HIGH",
            implementation_steps=[
                "Create adaptive ensemble with multiple models",
                "Emphasize recent data in model training",
                "Implement online learning approach",
                "Set up enhanced monitoring for continued changes"
            ],
            timeline_months=1,
            validation_required=True,
            fallback_strategy="Ensemble approach with dynamic weighting"
        )
    
    def _handle_potential_unknown_change(self, 
                                       recent_data: pd.Series,
                                       change_assessment: Dict[str, Any]) -> ScenarioAction:
        """Handle potential unknown changes"""
        return ScenarioAction(
            scenario_type="UNKNOWN_CHANGES",
            action_type="ENHANCED_MONITORING",
            urgency="MEDIUM",
            implementation_steps=[
                "Increase monitoring frequency",
                "Prepare adaptive models for potential deployment",
                "Set up automated change confirmation",
                "Monitor for change persistence"
            ],
            timeline_months=2,
            validation_required=False,
            fallback_strategy="Continue with current model while monitoring"
        )
    
    def _calculate_adaptive_weights(self, 
                                  ensemble_models: Dict[str, Any],
                                  validation_data: pd.Series) -> Dict[str, float]:
        """Calculate adaptive weights for ensemble models"""
        weights = {}
        validation_window = min(6, len(validation_data) // 4)  # Use last 25% or 6 months
        
        for model_name, model_info in ensemble_models.items():
            # Simple weight calculation based on data recency
            data_length = len(model_info['data'])
            recency_score = min(data_length / config.model.training_months, 1.0)
            weights[model_name] = recency_score
        
        # Normalize weights
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}
        
        return weights
    
    # Private helper methods for Scenario C
    def _handle_source_addition(self, 
                              change_details: Dict[str, Any],
                              historical_components: Dict[str, pd.Series],
                              current_total: pd.Series) -> ScenarioAction:
        """Handle addition of new source components"""
        return ScenarioAction(
            scenario_type="SOURCE_CHANGES",
            action_type="HIERARCHICAL_EXPANSION",
            urgency="HIGH",
            implementation_steps=[
                "Implement hierarchical forecasting framework",
                "Forecast new component separately",
                "Use bottom-up reconciliation for total forecast",
                "Validate hierarchical model performance"
            ],
            timeline_months=config.scenarios.source_change_retrain_months,
            validation_required=True,
            fallback_strategy="Adjust total forecast by estimated component contribution"
        )
    
    def _handle_source_removal(self, 
                             change_details: Dict[str, Any],
                             historical_components: Dict[str, pd.Series],
                             current_total: pd.Series) -> ScenarioAction:
        """Handle removal of source components"""
        return ScenarioAction(
            scenario_type="SOURCE_CHANGES",
            action_type="HIERARCHICAL_REDUCTION",
            urgency="HIGH",
            implementation_steps=[
                "Remove component from hierarchical structure",
                "Retrain total-level model without removed component",
                "Adjust historical data to exclude removed component",
                "Validate adjusted model performance"
            ],
            timeline_months=config.scenarios.source_change_retrain_months,
            validation_required=True,
            fallback_strategy="Apply adjustment factor to remove component contribution"
        )
    
    def _handle_source_modification(self, 
                                  change_details: Dict[str, Any],
                                  historical_components: Dict[str, pd.Series],
                                  current_total: pd.Series) -> ScenarioAction:
        """Handle modification of existing source components"""
        return ScenarioAction(
            scenario_type="SOURCE_CHANGES",
            action_type="COMPONENT_RETRAINING",
            urgency="MEDIUM",
            implementation_steps=[
                "Retrain affected component models",
                "Update hierarchical reconciliation",
                "Validate component-level forecasts",
                "Monitor total forecast accuracy"
            ],
            timeline_months=config.scenarios.source_change_retrain_months,
            validation_required=True,
            fallback_strategy="Use intervention variables to model component changes"
        )

# Example usage
if __name__ == "__main__":
    # Example usage
    scenario_handler = ScenarioHandler()
    
    # Example: Known impact scenario
    known_impacts = [
        {
            'date': '2024-03-01',
            'type': 'step',
            'severity': 'high',
            'description': 'New product launch affecting demand'
        }
    ]
    
    # Simulate time series data
    dates = pd.date_range('2021-01-01', periods=42, freq='M')
    data = pd.Series(np.random.normal(1000, 100, 42), index=dates)
    
    # Handle known impacts
    action = scenario_handler.handle_known_impacts(known_impacts, data)
    print(f"Known Impact Action: {action.action_type}")
    print(f"Urgency: {action.urgency}")
    print(f"Timeline: {action.timeline_months} months")
