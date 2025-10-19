"""
System Monitoring and Performance Optimization for F1 Dual Twin System.

This module implements comprehensive system monitoring, health checks, error reporting,
and performance optimization features as required by task 7.2.
"""

import psutil
import threading
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Callable
from collections import deque, defaultdict
from dataclasses import dataclass
from enum import Enum
import logging
import json
from pathlib import Path

from utils.config import get_config


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    ERROR = "error"


class HealthStatus(Enum):
    """System health status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    OFFLINE = "offline"


@dataclass
class PerformanceAlert:
    """Performance alert data structure."""
    timestamp: datetime
    severity: AlertSeverity
    component: str
    metric: str
    value: float
    threshold: float
    message: str
    resolved: bool = False
    resolution_timestamp: Optional[datetime] = None


@dataclass
class SystemMetrics:
    """System-wide metrics data structure."""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    process_count: int
    thread_count: int
    uptime_seconds: float


@dataclass
class ComponentHealth:
    """Component health status data structure."""
    name: str
    status: HealthStatus
    last_update: datetime
    response_time_ms: float
    error_count: int
    performance_score: float
    issues: List[str]
    recommendations: List[str]


class PerformanceOptimizer:
    """Handles performance optimization based on monitoring data."""
    
    def __init__(self):
        self.optimization_rules: Dict[str, Callable] = {}
        self.optimization_history: List[Dict[str, Any]] = []
        self.auto_optimization_enabled = get_config("monitoring.auto_optimization_enabled", True)
        
        # Register default optimization rules
        self._register_default_optimizations()
    
    def register_optimization_rule(self, name: str, rule_func: Callable) -> None:
        """
        Register a performance optimization rule.
        
        Args:
            name: Rule name
            rule_func: Function that takes metrics and returns optimization actions
        """
        self.optimization_rules[name] = rule_func
    
    def apply_optimizations(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Apply performance optimizations based on current metrics.
        
        Args:
            metrics: Current system metrics
            
        Returns:
            List of optimization actions taken
        """
        if not self.auto_optimization_enabled:
            return []
        
        actions = []
        
        for rule_name, rule_func in self.optimization_rules.items():
            try:
                optimization = rule_func(metrics)
                if optimization:
                    optimization["rule"] = rule_name
                    optimization["timestamp"] = datetime.now(timezone.utc).isoformat()
                    actions.append(optimization)
                    
                    # Record optimization history
                    self.optimization_history.append(optimization)
                    
                    # Keep only recent history
                    if len(self.optimization_history) > 100:
                        self.optimization_history.pop(0)
                        
            except Exception as e:
                logging.error(f"Error applying optimization rule {rule_name}: {e}")
        
        return actions
    
    def _register_default_optimizations(self) -> None:
        """Register default performance optimization rules."""
        
        def memory_optimization(metrics: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            """Optimize memory usage when high."""
            system_metrics = metrics.get("system", {})
            memory_usage = system_metrics.get("memory_usage", 0)
            
            if memory_usage > 85.0:  # Above 85% memory usage
                return {
                    "type": "memory_optimization",
                    "action": "garbage_collection",
                    "reason": f"High memory usage: {memory_usage:.1f}%",
                    "priority": "high"
                }
            return None
        
        def cpu_optimization(metrics: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            """Optimize CPU usage when high."""
            system_metrics = metrics.get("system", {})
            cpu_usage = system_metrics.get("cpu_usage", 0)
            
            if cpu_usage > 90.0:  # Above 90% CPU usage
                return {
                    "type": "cpu_optimization",
                    "action": "reduce_update_frequency",
                    "reason": f"High CPU usage: {cpu_usage:.1f}%",
                    "priority": "high"
                }
            return None
        
        def latency_optimization(metrics: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            """Optimize when latency requirements are violated."""
            performance = metrics.get("performance", {})
            
            # Check for consistent latency violations
            violations = []
            for metric_name, stats in performance.items():
                if isinstance(stats, dict) and "violations" in stats:
                    if stats["violations"] > 5:  # More than 5 violations
                        violations.append(metric_name)
            
            if violations:
                return {
                    "type": "latency_optimization",
                    "action": "optimize_processing_pipeline",
                    "reason": f"Latency violations in: {', '.join(violations)}",
                    "priority": "medium",
                    "affected_metrics": violations
                }
            return None
        
        # Register the optimization rules
        self.register_optimization_rule("memory_optimization", memory_optimization)
        self.register_optimization_rule("cpu_optimization", cpu_optimization)
        self.register_optimization_rule("latency_optimization", latency_optimization)


class SystemHealthChecker:
    """Performs comprehensive system health checks."""
    
    def __init__(self):
        self.health_checks: Dict[str, Callable] = {}
        self.health_history: deque = deque(maxlen=100)
        
        # Register default health checks
        self._register_default_health_checks()
    
    def register_health_check(self, name: str, check_func: Callable) -> None:
        """
        Register a health check function.
        
        Args:
            name: Health check name
            check_func: Function that returns ComponentHealth
        """
        self.health_checks[name] = check_func
    
    def perform_health_checks(self, components: Dict[str, Any]) -> Dict[str, ComponentHealth]:
        """
        Perform all registered health checks.
        
        Args:
            components: Dictionary of system components
            
        Returns:
            Dictionary of component health status
        """
        health_results = {}
        
        for check_name, check_func in self.health_checks.items():
            try:
                health = check_func(components)
                if health:
                    health_results[check_name] = health
            except Exception as e:
                logging.error(f"Health check {check_name} failed: {e}")
                health_results[check_name] = ComponentHealth(
                    name=check_name,
                    status=HealthStatus.ERROR,
                    last_update=datetime.now(timezone.utc),
                    response_time_ms=0.0,
                    error_count=1,
                    performance_score=0.0,
                    issues=[f"Health check failed: {str(e)}"],
                    recommendations=["Investigate health check implementation"]
                )
        
        # Record health history
        overall_health = self._calculate_overall_health(health_results)
        self.health_history.append({
            "timestamp": datetime.now(timezone.utc),
            "overall_status": overall_health,
            "component_count": len(health_results),
            "healthy_components": len([h for h in health_results.values() if h.status == HealthStatus.HEALTHY])
        })
        
        return health_results
    
    def _register_default_health_checks(self) -> None:
        """Register default health check functions."""
        
        def telemetry_health_check(components: Dict[str, Any]) -> Optional[ComponentHealth]:
            """Check telemetry ingestor health."""
            telemetry_ingestor = components.get("telemetry_ingestor")
            if not telemetry_ingestor:
                return None
            
            issues = []
            recommendations = []
            status = HealthStatus.HEALTHY
            
            # Check if telemetry is running
            if not hasattr(telemetry_ingestor, 'running') or not telemetry_ingestor.running:
                status = HealthStatus.CRITICAL
                issues.append("Telemetry ingestion not running")
                recommendations.append("Restart telemetry ingestor")
            
            # Check performance metrics
            if hasattr(telemetry_ingestor, 'get_performance_metrics'):
                metrics = telemetry_ingestor.get_performance_metrics()
                if metrics:
                    avg_time = metrics.get("avg_processing_time_ms", 0)
                    if avg_time > 250:  # Exceeds 250ms requirement
                        status = HealthStatus.WARNING if status == HealthStatus.HEALTHY else status
                        issues.append(f"High processing time: {avg_time:.1f}ms")
                        recommendations.append("Optimize telemetry processing pipeline")
                    
                    failure_rate = metrics.get("failure_rate", 0)
                    if failure_rate > 0.05:  # Above 5% failure rate
                        status = HealthStatus.WARNING if status == HealthStatus.HEALTHY else status
                        issues.append(f"High failure rate: {failure_rate:.1%}")
                        recommendations.append("Investigate telemetry validation issues")
            
            return ComponentHealth(
                name="telemetry_ingestor",
                status=status,
                last_update=datetime.now(timezone.utc),
                response_time_ms=0.0,  # Would measure actual response time
                error_count=len(issues),
                performance_score=1.0 - (len(issues) * 0.2),
                issues=issues,
                recommendations=recommendations
            )
        
        def state_handler_health_check(components: Dict[str, Any]) -> Optional[ComponentHealth]:
            """Check state handler health."""
            state_handler = components.get("state_handler")
            if not state_handler:
                return None
            
            issues = []
            recommendations = []
            status = HealthStatus.HEALTHY
            
            # Check state consistency
            try:
                if hasattr(state_handler, 'ensure_twin_consistency'):
                    consistent = state_handler.ensure_twin_consistency()
                    if not consistent:
                        status = HealthStatus.WARNING
                        issues.append("Twin state consistency issues detected")
                        recommendations.append("Perform state recovery")
            except Exception as e:
                status = HealthStatus.ERROR
                issues.append(f"Consistency check failed: {str(e)}")
                recommendations.append("Investigate state handler errors")
            
            # Check storage health
            try:
                if hasattr(state_handler, 'storage_path'):
                    storage_path = Path(state_handler.storage_path)
                    if not storage_path.exists():
                        status = HealthStatus.CRITICAL
                        issues.append("Storage path not accessible")
                        recommendations.append("Check storage permissions and availability")
            except Exception as e:
                issues.append(f"Storage check failed: {str(e)}")
            
            return ComponentHealth(
                name="state_handler",
                status=status,
                last_update=datetime.now(timezone.utc),
                response_time_ms=0.0,
                error_count=len(issues),
                performance_score=1.0 - (len(issues) * 0.25),
                issues=issues,
                recommendations=recommendations
            )
        
        def twin_models_health_check(components: Dict[str, Any]) -> Optional[ComponentHealth]:
            """Check twin models health."""
            car_twin = components.get("car_twin")
            field_twin = components.get("field_twin")
            
            issues = []
            recommendations = []
            status = HealthStatus.HEALTHY
            
            # Check Car Twin
            if car_twin:
                if hasattr(car_twin, 'get_performance_metrics'):
                    try:
                        metrics = car_twin.get_performance_metrics()
                        if metrics and metrics.get("avg_update_time_ms", 0) > 200:
                            status = HealthStatus.WARNING
                            issues.append("Car Twin update time exceeds 200ms requirement")
                            recommendations.append("Optimize Car Twin processing algorithms")
                    except Exception as e:
                        issues.append(f"Car Twin metrics error: {str(e)}")
            else:
                status = HealthStatus.CRITICAL
                issues.append("Car Twin not available")
                recommendations.append("Initialize Car Twin component")
            
            # Check Field Twin
            if field_twin:
                if hasattr(field_twin, 'get_performance_metrics'):
                    try:
                        metrics = field_twin.get_performance_metrics()
                        if metrics and metrics.get("avg_update_time_ms", 0) > 300:
                            status = HealthStatus.WARNING if status == HealthStatus.HEALTHY else status
                            issues.append("Field Twin update time exceeds 300ms requirement")
                            recommendations.append("Optimize Field Twin competitor analysis")
                    except Exception as e:
                        issues.append(f"Field Twin metrics error: {str(e)}")
            else:
                status = HealthStatus.CRITICAL if status != HealthStatus.CRITICAL else status
                issues.append("Field Twin not available")
                recommendations.append("Initialize Field Twin component")
            
            return ComponentHealth(
                name="twin_models",
                status=status,
                last_update=datetime.now(timezone.utc),
                response_time_ms=0.0,
                error_count=len(issues),
                performance_score=1.0 - (len(issues) * 0.2),
                issues=issues,
                recommendations=recommendations
            )
        
        # Register health checks
        self.register_health_check("telemetry_health", telemetry_health_check)
        self.register_health_check("state_handler_health", state_handler_health_check)
        self.register_health_check("twin_models_health", twin_models_health_check)
    
    def _calculate_overall_health(self, health_results: Dict[str, ComponentHealth]) -> HealthStatus:
        """Calculate overall system health from component health."""
        if not health_results:
            return HealthStatus.OFFLINE
        
        status_counts = defaultdict(int)
        for health in health_results.values():
            status_counts[health.status] += 1
        
        total_components = len(health_results)
        
        # Determine overall status based on component statuses
        if status_counts[HealthStatus.CRITICAL] > 0:
            return HealthStatus.CRITICAL
        elif status_counts[HealthStatus.ERROR] > 0:
            return HealthStatus.CRITICAL
        elif status_counts[HealthStatus.DEGRADED] > 0:
            return HealthStatus.DEGRADED
        elif status_counts[HealthStatus.WARNING] > total_components * 0.3:  # More than 30% warnings
            return HealthStatus.WARNING
        else:
            return HealthStatus.HEALTHY


class SystemMonitor:
    """
    Comprehensive system monitoring for F1 Dual Twin System.
    
    Implements performance monitoring, health checks, error reporting,
    and optimization as required by requirements 1.1, 2.1, 3.1, 5.3.
    """
    
    def __init__(self):
        """Initialize system monitor."""
        self.logger = logging.getLogger(__name__)
        
        # Monitoring configuration
        self.monitoring_enabled = get_config("monitoring.enabled", True)
        self.monitoring_interval = get_config("monitoring.interval_seconds", 10)
        self.alert_retention_hours = get_config("monitoring.alert_retention_hours", 24)
        
        # Performance tracking
        self.performance_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.system_metrics_history: deque = deque(maxlen=1000)
        
        # Alert management
        self.active_alerts: List[PerformanceAlert] = []
        self.alert_history: deque = deque(maxlen=1000)
        
        # Component monitoring
        self.monitored_components: Dict[str, Any] = {}
        self.component_health: Dict[str, ComponentHealth] = {}
        
        # Monitoring subsystems
        self.health_checker = SystemHealthChecker()
        self.performance_optimizer = PerformanceOptimizer()
        
        # Monitoring thread
        self.monitoring_thread: Optional[threading.Thread] = None
        self.monitoring_stop_event = threading.Event()
        self.running = False
        
        # Performance thresholds (from requirements)
        self.performance_thresholds = {
            "telemetry_processing_time_ms": 250.0,  # Requirement 1.1
            "car_twin_update_time_ms": 200.0,       # Requirement 2.1
            "field_twin_update_time_ms": 300.0,     # Requirement 3.1
            "api_response_time_ms": 50.0,           # Requirement 5.3
            "state_persistence_time_ms": 1000.0,    # 5-second cycle tolerance
            "cpu_usage_percent": 85.0,
            "memory_usage_percent": 90.0,
            "disk_usage_percent": 95.0
        }
    
    def start_monitoring(self) -> None:
        """Start system monitoring."""
        if self.running:
            self.logger.warning("System monitoring already running")
            return
        
        if not self.monitoring_enabled:
            self.logger.info("System monitoring disabled in configuration")
            return
        
        self.running = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        self.logger.info("System monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop system monitoring."""
        if not self.running:
            return
        
        self.running = False
        self.monitoring_stop_event.set()
        
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5.0)
        
        self.logger.info("System monitoring stopped")
    
    def register_component(self, name: str, component: Any) -> None:
        """
        Register a component for monitoring.
        
        Args:
            name: Component name
            component: Component instance
        """
        self.monitored_components[name] = component
        self.logger.info(f"Registered component for monitoring: {name}")
    
    def record_performance_metric(self, metric_name: str, value: float, timestamp: Optional[datetime] = None) -> None:
        """
        Record a performance metric.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            timestamp: Optional timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        # Store metric
        self.performance_metrics[metric_name].append({
            "timestamp": timestamp,
            "value": value
        })
        
        # Check for threshold violations
        threshold = self.performance_thresholds.get(metric_name)
        if threshold and value > threshold:
            self._create_performance_alert(metric_name, value, threshold)
    
    def get_system_health_report(self) -> Dict[str, Any]:
        """
        Get comprehensive system health report.
        
        Returns:
            System health report dictionary
        """
        # Perform health checks
        health_results = self.health_checker.perform_health_checks(self.monitored_components)
        
        # Get system metrics
        system_metrics = self._collect_system_metrics()
        
        # Get performance summary
        performance_summary = self._get_performance_summary()
        
        # Get active alerts
        active_alerts = [self._alert_to_dict(alert) for alert in self.active_alerts if not alert.resolved]
        
        # Calculate overall health score
        health_score = self._calculate_health_score(health_results, system_metrics, performance_summary)
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_health": self._get_overall_health_status(health_results),
            "health_score": health_score,
            "component_health": {name: self._health_to_dict(health) for name, health in health_results.items()},
            "system_metrics": self._system_metrics_to_dict(system_metrics),
            "performance_summary": performance_summary,
            "active_alerts": active_alerts,
            "alert_count": len(active_alerts),
            "recommendations": self._generate_recommendations(health_results, system_metrics)
        }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """
        Get detailed performance report.
        
        Returns:
            Performance report dictionary
        """
        performance_summary = self._get_performance_summary()
        
        # Apply performance optimizations
        optimization_actions = self.performance_optimizer.apply_optimizations({
            "system": self._system_metrics_to_dict(self._collect_system_metrics()),
            "performance": performance_summary,
            "components": {name: self._get_component_metrics(component) 
                          for name, component in self.monitored_components.items()}
        })
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "performance_metrics": performance_summary,
            "threshold_violations": self._get_threshold_violations(),
            "optimization_actions": optimization_actions,
            "optimization_history": self.performance_optimizer.optimization_history[-10:],  # Last 10
            "trends": self._calculate_performance_trends(),
            "bottlenecks": self._identify_performance_bottlenecks()
        }
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        self.logger.info("Starting monitoring loop")
        
        while self.running and not self.monitoring_stop_event.is_set():
            try:
                # Collect system metrics
                system_metrics = self._collect_system_metrics()
                self.system_metrics_history.append(system_metrics)
                
                # Record system performance metrics
                self.record_performance_metric("cpu_usage_percent", system_metrics.cpu_usage)
                self.record_performance_metric("memory_usage_percent", system_metrics.memory_usage)
                self.record_performance_metric("disk_usage_percent", system_metrics.disk_usage)
                
                # Perform health checks
                health_results = self.health_checker.perform_health_checks(self.monitored_components)
                self.component_health.update(health_results)
                
                # Clean up old alerts
                self._cleanup_old_alerts()
                
                # Log health summary periodically
                if len(self.system_metrics_history) % 6 == 0:  # Every 6 cycles (1 minute if 10s interval)
                    self._log_health_summary(health_results, system_metrics)
                
                # Wait for next monitoring cycle
                if self.monitoring_stop_event.wait(self.monitoring_interval):
                    break
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(1)  # Brief pause before retry
        
        self.logger.info("Monitoring loop stopped")
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect system-wide metrics."""
        try:
            # CPU usage
            cpu_usage = psutil.cpu_percent(interval=0.1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100
            
            # Network I/O
            network = psutil.net_io_counters()
            network_io = {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            }
            
            # Process information
            process = psutil.Process()
            process_count = len(psutil.pids())
            thread_count = process.num_threads()
            
            # System uptime
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            
            return SystemMetrics(
                timestamp=datetime.now(timezone.utc),
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                network_io=network_io,
                process_count=process_count,
                thread_count=thread_count,
                uptime_seconds=uptime_seconds
            )
            
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
            return SystemMetrics(
                timestamp=datetime.now(timezone.utc),
                cpu_usage=0.0,
                memory_usage=0.0,
                disk_usage=0.0,
                network_io={},
                process_count=0,
                thread_count=0,
                uptime_seconds=0.0
            )
    
    def _create_performance_alert(self, metric_name: str, value: float, threshold: float) -> None:
        """Create a performance alert for threshold violation."""
        # Check if similar alert already exists
        for alert in self.active_alerts:
            if (alert.metric == metric_name and not alert.resolved and 
                (datetime.now(timezone.utc) - alert.timestamp).seconds < 300):  # Within 5 minutes
                return  # Don't create duplicate alerts
        
        # Determine severity
        severity = AlertSeverity.WARNING
        if value > threshold * 1.5:
            severity = AlertSeverity.CRITICAL
        elif value > threshold * 1.2:
            severity = AlertSeverity.ERROR
        
        alert = PerformanceAlert(
            timestamp=datetime.now(timezone.utc),
            severity=severity,
            component="system",
            metric=metric_name,
            value=value,
            threshold=threshold,
            message=f"{metric_name} ({value:.2f}) exceeded threshold ({threshold:.2f})"
        )
        
        self.active_alerts.append(alert)
        self.alert_history.append(alert)
        
        self.logger.warning(f"Performance alert: {alert.message}")
    
    def _get_performance_summary(self) -> Dict[str, Any]:
        """Get performance metrics summary."""
        summary = {}
        
        for metric_name, measurements in self.performance_metrics.items():
            if not measurements:
                continue
            
            values = [m["value"] for m in measurements]
            threshold = self.performance_thresholds.get(metric_name)
            
            summary[metric_name] = {
                "current": values[-1] if values else 0.0,
                "average": sum(values) / len(values),
                "minimum": min(values),
                "maximum": max(values),
                "count": len(values),
                "threshold": threshold,
                "violations": len([v for v in values if threshold and v > threshold]) if threshold else 0,
                "trend": self._calculate_trend(values[-10:]) if len(values) >= 10 else "stable"
            }
        
        return summary
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction for a series of values."""
        if len(values) < 2:
            return "stable"
        
        # Simple trend calculation
        first_half = sum(values[:len(values)//2]) / (len(values)//2)
        second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
        
        change_percent = ((second_half - first_half) / first_half) * 100 if first_half > 0 else 0
        
        if change_percent > 10:
            return "increasing"
        elif change_percent < -10:
            return "decreasing"
        else:
            return "stable"
    
    def _get_component_metrics(self, component: Any) -> Dict[str, Any]:
        """Get metrics from a component if available."""
        metrics = {}
        
        if hasattr(component, 'get_performance_metrics'):
            try:
                metrics = component.get_performance_metrics()
            except Exception as e:
                self.logger.error(f"Error getting component metrics: {e}")
        
        return metrics
    
    def _cleanup_old_alerts(self) -> None:
        """Clean up old alerts based on retention policy."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=self.alert_retention_hours)
        
        # Remove old alerts from active list
        self.active_alerts = [alert for alert in self.active_alerts 
                             if alert.timestamp > cutoff_time or not alert.resolved]
    
    def _log_health_summary(self, health_results: Dict[str, ComponentHealth], system_metrics: SystemMetrics) -> None:
        """Log periodic health summary."""
        healthy_count = len([h for h in health_results.values() if h.status == HealthStatus.HEALTHY])
        total_count = len(health_results)
        
        self.logger.info(f"Health Summary: {healthy_count}/{total_count} components healthy, "
                        f"CPU: {system_metrics.cpu_usage:.1f}%, "
                        f"Memory: {system_metrics.memory_usage:.1f}%, "
                        f"Active alerts: {len([a for a in self.active_alerts if not a.resolved])}")
    
    def _calculate_health_score(self, health_results: Dict[str, ComponentHealth], 
                               system_metrics: SystemMetrics, performance_summary: Dict[str, Any]) -> float:
        """Calculate overall system health score (0.0 to 1.0)."""
        score = 1.0
        
        # Component health factor
        if health_results:
            healthy_components = len([h for h in health_results.values() if h.status == HealthStatus.HEALTHY])
            component_factor = healthy_components / len(health_results)
            score *= component_factor
        
        # System resource factor
        resource_factor = 1.0
        if system_metrics.cpu_usage > 90:
            resource_factor *= 0.7
        elif system_metrics.cpu_usage > 75:
            resource_factor *= 0.9
        
        if system_metrics.memory_usage > 95:
            resource_factor *= 0.6
        elif system_metrics.memory_usage > 85:
            resource_factor *= 0.8
        
        score *= resource_factor
        
        # Performance factor
        violation_count = sum(stats.get("violations", 0) for stats in performance_summary.values())
        if violation_count > 10:
            score *= 0.7
        elif violation_count > 5:
            score *= 0.85
        
        return max(0.0, min(1.0, score))
    
    def _get_overall_health_status(self, health_results: Dict[str, ComponentHealth]) -> HealthStatus:
        """Get overall system health status."""
        return self.health_checker._calculate_overall_health(health_results)
    
    def _generate_recommendations(self, health_results: Dict[str, ComponentHealth], 
                                 system_metrics: SystemMetrics) -> List[str]:
        """Generate system recommendations based on health and metrics."""
        recommendations = []
        
        # Collect recommendations from component health
        for health in health_results.values():
            recommendations.extend(health.recommendations)
        
        # Add system-level recommendations
        if system_metrics.cpu_usage > 85:
            recommendations.append("Consider reducing system load or scaling resources")
        
        if system_metrics.memory_usage > 90:
            recommendations.append("Memory usage is high - consider memory optimization")
        
        if system_metrics.disk_usage > 95:
            recommendations.append("Disk space is critically low - clean up old files")
        
        # Remove duplicates and return
        return list(set(recommendations))
    
    def _get_threshold_violations(self) -> Dict[str, int]:
        """Get count of threshold violations by metric."""
        violations = {}
        
        for metric_name, measurements in self.performance_metrics.items():
            threshold = self.performance_thresholds.get(metric_name)
            if threshold:
                violation_count = len([m for m in measurements if m["value"] > threshold])
                if violation_count > 0:
                    violations[metric_name] = violation_count
        
        return violations
    
    def _calculate_performance_trends(self) -> Dict[str, str]:
        """Calculate performance trends for all metrics."""
        trends = {}
        
        for metric_name, measurements in self.performance_metrics.items():
            if len(measurements) >= 10:
                values = [m["value"] for m in measurements[-20:]]  # Last 20 measurements
                trends[metric_name] = self._calculate_trend(values)
        
        return trends
    
    def _identify_performance_bottlenecks(self) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks in the system."""
        bottlenecks = []
        
        for metric_name, measurements in self.performance_metrics.items():
            if not measurements:
                continue
            
            threshold = self.performance_thresholds.get(metric_name)
            if not threshold:
                continue
            
            recent_values = [m["value"] for m in measurements[-10:]]
            avg_recent = sum(recent_values) / len(recent_values)
            
            if avg_recent > threshold:
                severity = "critical" if avg_recent > threshold * 1.5 else "warning"
                bottlenecks.append({
                    "metric": metric_name,
                    "average_value": avg_recent,
                    "threshold": threshold,
                    "severity": severity,
                    "impact": f"{((avg_recent - threshold) / threshold) * 100:.1f}% over threshold"
                })
        
        return sorted(bottlenecks, key=lambda x: x["average_value"], reverse=True)
    
    # Helper methods for serialization
    
    def _alert_to_dict(self, alert: PerformanceAlert) -> Dict[str, Any]:
        """Convert PerformanceAlert to dictionary."""
        return {
            "timestamp": alert.timestamp.isoformat(),
            "severity": alert.severity.value,
            "component": alert.component,
            "metric": alert.metric,
            "value": alert.value,
            "threshold": alert.threshold,
            "message": alert.message,
            "resolved": alert.resolved,
            "resolution_timestamp": alert.resolution_timestamp.isoformat() if alert.resolution_timestamp else None
        }
    
    def _health_to_dict(self, health: ComponentHealth) -> Dict[str, Any]:
        """Convert ComponentHealth to dictionary."""
        return {
            "name": health.name,
            "status": health.status.value,
            "last_update": health.last_update.isoformat(),
            "response_time_ms": health.response_time_ms,
            "error_count": health.error_count,
            "performance_score": health.performance_score,
            "issues": health.issues,
            "recommendations": health.recommendations
        }
    
    def _system_metrics_to_dict(self, metrics: SystemMetrics) -> Dict[str, Any]:
        """Convert SystemMetrics to dictionary."""
        return {
            "timestamp": metrics.timestamp.isoformat(),
            "cpu_usage": metrics.cpu_usage,
            "memory_usage": metrics.memory_usage,
            "disk_usage": metrics.disk_usage,
            "network_io": metrics.network_io,
            "process_count": metrics.process_count,
            "thread_count": metrics.thread_count,
            "uptime_seconds": metrics.uptime_seconds
        }


# Global system monitor instance
system_monitor: Optional[SystemMonitor] = None


def get_system_monitor() -> SystemMonitor:
    """Get the global system monitor instance."""
    global system_monitor
    if system_monitor is None:
        system_monitor = SystemMonitor()
    return system_monitor


def start_system_monitoring() -> None:
    """Start system monitoring."""
    monitor = get_system_monitor()
    monitor.start_monitoring()


def stop_system_monitoring() -> None:
    """Stop system monitoring."""
    global system_monitor
    if system_monitor:
        system_monitor.stop_monitoring()
        system_monitor = None