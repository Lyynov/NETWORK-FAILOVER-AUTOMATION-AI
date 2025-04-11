# src/monitoring/collector.py
import time
import logging
from typing import Dict, List, Any
from datetime import datetime

from src.router.mikrotik import MikrotikRouter
from config.settings import (
    PRIMARY_INTERFACE, 
    SECONDARY_INTERFACES, 
    PING_COUNT, 
    PING_TIMEOUT,
    POLLING_INTERVAL
)

logger = logging.getLogger(__name__)

class NetworkMetricsCollector:
    def __init__(self, router: MikrotikRouter = None):
        self.router = router or MikrotikRouter()
        self.targets = ["8.8.8.8", "1.1.1.1"]  # Default ping targets
    
    def collect_interface_metrics(self, interface_name: str) -> Dict[str, Any]:
        """Collect metrics for a specific interface"""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'interface': interface_name,
            'status': 'unknown',
            'latency': None,
            'packet_loss': None,
            'bandwidth_usage': None
        }
        
        try:
            # Get interface status
            interface_status = self.router.get_interface_status(interface_name)
            metrics['status'] = 'up' if interface_status.get('running', 'false') == 'true' and \
                                       interface_status.get('disabled', 'true') == 'false' else 'down'
            
            # If interface is up, collect performance metrics
            if metrics['status'] == 'up':
                # Ping through this interface
                for target in self.targets:
                    ping_results = self.router.ping(target, count=PING_COUNT, interface=interface_name)
                    
                    # Use the best result from multiple targets
                    if metrics['latency'] is None or (ping_results['avg_rtt'] < metrics['latency'] and 
                                                     ping_results['received'] > 0):
                        metrics['latency'] = ping_results['avg_rtt']
                        metrics['packet_loss'] = ping_results['packet_loss']
                
                # TODO: Implement bandwidth usage collection
                # This would typically involve getting rx/tx bytes and calculating the rate
                metrics['bandwidth_usage'] = 0  # Placeholder
            
            return metrics
        
        except Exception as e:
            logger.error(f"Error collecting metrics for interface {interface_name}: {e}")
            metrics['status'] = 'error'
            return metrics
    
    def collect_all_interfaces_metrics(self) -> List[Dict[str, Any]]:
        """Collect metrics for all monitored interfaces"""
        metrics = []
        
        # Collect metrics for primary interface
        primary_metrics = self.collect_interface_metrics(PRIMARY_INTERFACE)
        metrics.append(primary_metrics)
        
        # Collect metrics for secondary interfaces
        for interface in SECONDARY_INTERFACES:
            secondary_metrics = self.collect_interface_metrics(interface)
            metrics.append(secondary_metrics)
        
        return metrics
    
    def start_monitoring(self, callback=None):
        """Start continuous monitoring of all interfaces"""
        logger.info("Starting network metrics collection...")
        
        try:
            while True:
                metrics = self.collect_all_interfaces_metrics()
                
                if callback:
                    callback(metrics)
                
                logger.debug(f"Collected metrics: {metrics}")
                time.sleep(POLLING_INTERVAL)
        
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Error in monitoring: {e}")
        finally:
            self.router.close()