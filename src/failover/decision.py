# src/failover/decision.py
import logging
import time
from typing import Dict, List, Any, Tuple, Optional

from config.settings import (
    PRIMARY_INTERFACE, 
    SECONDARY_INTERFACES, 
    MAX_LATENCY, 
    MAX_PACKET_LOSS
)

logger = logging.getLogger(__name__)

class FailoverDecisionMaker:
    """Decision maker for network failover based on metrics and thresholds"""
    
    def __init__(self):
        self.primary_interface = PRIMARY_INTERFACE
        self.secondary_interfaces = SECONDARY_INTERFACES
        self.max_latency = MAX_LATENCY
        self.max_packet_loss = MAX_PACKET_LOSS
        self.consecutive_failures = {}
        self.recovery_times = {}
        self.failover_state = False
        self.current_active_interface = PRIMARY_INTERFACE
        self.required_consecutive_failures = 3
        self.recovery_check_time = 60  # seconds
    
    def evaluate_metrics(self, primary_metrics: Dict[str, Any], 
                          secondary_metrics: List[Dict[str, Any]]) -> Tuple[bool, Optional[str], str]:
        """
        Evaluate metrics and decide if failover is needed
        
        Args:
            primary_metrics: Metrics for primary interface
            secondary_metrics: List of metrics for secondary interfaces
        
        Returns:
            Tuple of (failover_needed, target_interface, reason)
        """
        # Check if primary interface is down
        if primary_metrics.get('status') != 'up':
            self._record_failure(self.primary_interface)
            
            if self._has_consecutive_failures(self.primary_interface):
                best_secondary = self._select_best_secondary(secondary_metrics)
                return True, best_secondary, "Primary interface is down"
            
            return False, None, "Monitoring primary interface failure"
        else:
            self._reset_failures(self.primary_interface)
        
        # Check if primary interface exceeds thresholds
        primary_latency = primary_metrics.get('latency')
        primary_packet_loss = primary_metrics.get('packet_loss')
        
        # Check latency threshold
        if primary_latency is not None and primary_latency > self.max_latency:
            self._record_failure(self.primary_interface, f"High latency: {primary_latency}ms")
            
            if self._has_consecutive_failures(self.primary_interface):
                best_secondary = self._select_best_secondary(secondary_metrics)
                return True, best_secondary, f"Primary interface latency ({primary_latency}ms) exceeds threshold"
            
            return False, None, "Monitoring primary interface latency issue"
        
        # Check packet loss threshold
        if primary_packet_loss is not None and primary_packet_loss > self.max_packet_loss:
            self._record_failure(self.primary_interface, f"High packet loss: {primary_packet_loss}%")
            
            if self._has_consecutive_failures(self.primary_interface):
                best_secondary = self._select_best_secondary(secondary_metrics)
                return True, best_secondary, f"Primary interface packet loss ({primary_packet_loss}%) exceeds threshold"
            
            return False, None, "Monitoring primary interface packet loss issue"
        
        # Check if we need to recover to primary
        if self.failover_state and self.current_active_interface != self.primary_interface:
            recovery_time = self.recovery_times.get(self.primary_interface, 0)
            
            if recovery_time == 0:
                # Start recovery timer
                self.recovery_times[self.primary_interface] = time.time()
                return False, None, "Started recovery timer for primary interface"
            elif time.time() - recovery_time > self.recovery_check_time:
                # Recovery time has passed, switch back to primary
                return True, self.primary_interface, "Primary interface has recovered"
        
        # Default: no failover needed
        return False, None, "No failover action needed"
    
    def _record_failure(self, interface: str, reason: str = "Unknown"):
        """Record a failure for an interface"""
        if interface not in self.consecutive_failures:
            self.consecutive_failures[interface] = []
        
        self.consecutive_failures[interface].append({
            'timestamp': time.time(),
            'reason': reason
        })
        
        # Keep only the most recent failures
        self.consecutive_failures[interface] = self.consecutive_failures[interface][-self.required_consecutive_failures:]
    
    def _reset_failures(self, interface: str):
        """Reset failure counter for an interface"""
        self.consecutive_failures[interface] = []
    
    def _has_consecutive_failures(self, interface: str) -> bool:
        """Check if an interface has had consecutive failures"""
        if interface not in self.consecutive_failures:
            return False
        
        return len(self.consecutive_failures[interface]) >= self.required_consecutive_failures
    
    def _select_best_secondary(self, secondary_metrics: List[Dict[str, Any]]) -> Optional[str]:
        """Select the best secondary interface based on metrics"""
        available_interfaces = [m for m in secondary_metrics if m.get('status') == 'up']
        
        if not available_interfaces:
            logger.error("No secondary interfaces are available")
            return None
        
        # Sort by latency and packet loss (lowest values first)
        sorted_interfaces = sorted(
            available_interfaces,
            key=lambda x: (
                float('inf') if x.get('latency') is None else x.get('latency', float('inf')),
                float('inf') if x.get('packet_loss') is None else x.get('packet_loss', float('inf'))
            )
        )
        
        if sorted_interfaces:
            best_interface = sorted_interfaces[0]['interface']
            logger.info(f"Selected {best_interface} as best secondary interface")
            return best_interface
        
        return None
    
    def record_failover(self, interface: str):
        """Record that a failover has occurred"""
        self.failover_state = True
        self.current_active_interface = interface
        # Reset recovery timer
        self.recovery_times = {}
    
    def record_restore(self):
        """Record that primary interface has been restored"""
        self.failover_state = False
        self.current_active_interface = self.primary_interface
        self.recovery_times = {}
