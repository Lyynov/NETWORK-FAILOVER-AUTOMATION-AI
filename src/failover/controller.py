# src/failover/controller.py
import logging
import time
from typing import Dict, List, Any, Optional

from src.router.mikrotik import MikrotikRouter
from src.monitoring.collector import NetworkMetricsCollector
from src.monitoring.persistence import MetricsDatabase
from src.ai.predictor import FailoverPredictor
from config.settings import PRIMARY_INTERFACE, SECONDARY_INTERFACES, POLLING_INTERVAL

logger = logging.getLogger(__name__)

class FailoverController:
    def __init__(self):
        self.router = MikrotikRouter()
        self.collector = NetworkMetricsCollector(self.router)
        self.predictor = FailoverPredictor()
        self.db = MetricsDatabase()
        self.current_active_interface = PRIMARY_INTERFACE
        self.failover_active = False
    
    def process_metrics(self, metrics: List[Dict[str, Any]]):
        """Process collected metrics and decide if failover is needed"""
        # Store metrics in database
        self.db.store_metrics(metrics)
        
        # Extract primary and secondary metrics
        primary_metrics = next((m for m in metrics if m['interface'] == PRIMARY_INTERFACE), {})
        secondary_metrics = [m for m in metrics if m['interface'] in SECONDARY_INTERFACES]
        
        # Make failover decision
        failover_needed, best_interface, reason = self.predictor.predict_failover_need(
            primary_metrics, secondary_metrics
        )
        
        # Execute failover if needed
        if failover_needed and best_interface and best_interface != self.current_active_interface:
            self.execute_failover(best_interface, reason)
        elif not failover_needed and self.failover_active:
            self.restore_primary(reason)
    
    def execute_failover(self, target_interface: str, reason: str):
        """Execute failover to the target interface"""
        logger.info(f"Executing failover to {target_interface}: {reason}")
        
        try:
            # Update routing to use the target interface
            # This is simplified - actual implementation would depend on your routing setup
            if self.current_active_interface != target_interface:
                # Disable current active interface in routing
                if self.current_active_interface == PRIMARY_INTERFACE:
                    self.failover_active = True
                
                # Enable target interface in routing
                logger.info(f"Switching active interface from {self.current_active_interface} to {target_interface}")
                self.current_active_interface = target_interface
                
                # Log the failover event
                self.db.log_failover_event(
                    from_interface=self.current_active_interface,
                    to_interface=target_interface,
                    reason=reason
                )
        except Exception as e:
            logger.error(f"Failed to execute failover: {e}")
    
    def restore_primary(self, reason: str):
        """Restore connection to primary interface"""
        if self.current_active_interface != PRIMARY_INTERFACE:
            logger.info(f"Restoring connection to primary interface: {reason}")
            
            try:
                # Re-enable primary interface in routing
                self.current_active_interface = PRIMARY_INTERFACE
                self.failover_active = False
                
                # Log the restore event
                self.db.log_failover_event(
                    from_interface=self.current_active_interface,
                    to_interface=PRIMARY_INTERFACE,
                    reason=reason
                )
            except Exception as e:
                logger.error(f"Failed to restore primary interface: {e}")
    
    def start(self):
        """Start the failover controller"""
        logger.info("Starting failover controller...")
        
        # Initialize database
        self.db.initialize()
        
        # Start monitoring with callback
        self.collector.start_monitoring(callback=self.process_metrics)