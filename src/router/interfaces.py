"""
Modul untuk pengelolaan interface router.
"""
import logging
import time
from src.router.mikrotik import MikrotikClient
from config.router_config import INTERFACES, PING_TARGETS, THRESHOLDS

# Set up logging
logger = logging.getLogger(__name__)

class InterfaceManager:
    """Manager for handling router interfaces and failover."""
    
    def __init__(self, router_client):
        """
        Initialize interface manager.
        
        Args:
            router_client (MikrotikClient): MikroTik client instance
        """
        self.router = router_client
        self.primary_interface = INTERFACES['primary']
        self.secondary_interface = INTERFACES['secondary']
        self.current_active = self.primary_interface
        self.failover_timestamp = None
    
    def check_interfaces(self):
        """
        Check the status of all configured interfaces.
        
        Returns:
            dict: Dictionary with interface status results
        """
        results = {}
        
        # melakukan primary cek interface
        primary_status = self.get_interface_metrics(self.primary_interface)
        results[self.primary_interface] = primary_status
        
        # melakukan secondary cek interface
        secondary_status = self.get_interface_metrics(self.secondary_interface)
        results[self.secondary_interface] = secondary_status
        
        return results
    
    def get_interface_metrics(self, interface_name):
        """
        Get connectivity metrics for an interface.
        
        Args:
            interface_name (str): Name of the interface
            
        Returns:
            dict: Dictionary with interface metrics
        """
        # langkah awal pengecekan apakah interface down
        interface_status = self.router.get_interface_status(interface_name)
        
        if not interface_status or interface_status.get('running') != 'true':
            logger.warning(f"Interface {interface_name} is down or not found")
            return {
                'interface': interface_name,
                'status': 'down',
                'latency': float('inf'),
                'packet_loss': 100.0,
                'timestamp': time.time()
            }
        
        # mengumpulkan metric dengan melakukan ping setiap target
        latencies = []
        packet_losses = []
        
        for target in PING_TARGETS:
            ping_result = self.router.check_interface_connectivity(
                interface_name, target, count=5
            )
            
            if ping_result:
                latencies.append(ping_result['avg_latency'])
                packet_losses.append(ping_result['packet_loss'])
        
        # menghitung rata2 metric
        avg_latency = sum(latencies) / len(latencies) if latencies else float('inf')
        avg_packet_loss = sum(packet_losses) / len(packet_losses) if packet_losses else 100.0
        
        return {
            'interface': interface_name,
            'status': 'up',
            'latency': avg_latency,
            'packet_loss': avg_packet_loss,
            'timestamp': time.time()
        }
    
    def is_interface_healthy(self, metrics):
        """
        Determine if interface is healthy based on metrics.
        
        Args:
            metrics (dict): Interface metrics dictionary
            
        Returns:
            bool: True if interface is healthy, False otherwise
        """
        if not metrics or metrics['status'] == 'down':
            return False
        
        # pengecekan kembali trashold fail over
        latency_ok = metrics['latency'] < THRESHOLDS['latency_max']
        packet_loss_ok = metrics['packet_loss'] < THRESHOLDS['packet_loss_max']
        
        return latency_ok and packet_loss_ok
    
    def perform_failover(self, from_interface, to_interface):
        """
        Perform failover from one interface to another.
        
        Args:
            from_interface (str): Interface to fail over from
            to_interface (str): Interface to fail over to
            
        Returns:
            bool: True if failover successful, False otherwise
        """
        logger.info(f"Performing failover from {from_interface} to {to_interface}")
        
        # perbarui prioritas routing
        self.router.update_routing_priority(from_interface, new_distance=10)
        
        # meningkatkan prioritas untuk latency yg lebih rendah
        success = self.router.update_routing_priority(to_interface, new_distance=1)
        
        if success:
            self.current_active = to_interface
            self.failover_timestamp = time.time()
            logger.info(f"Failover successful. {to_interface} is now active")
            return True
        else:
            logger.error(f"Failover failed while switching to {to_interface}")
            return False
    
    def evaluate_failover_need(self, metrics):
        """
        Evaluate if failover is needed based on current metrics.
        
        Args:
            metrics (dict): Dictionary with interface metrics
            
        Returns:
            tuple: (need_failover, target_interface)
        """
        # mendapatkan metric untuk setiap interface
        primary_metrics = metrics.get(self.primary_interface)
        secondary_metrics = metrics.get(self.secondary_interface)
        
        # cek kesehatan pada primary interface
        primary_healthy = self.is_interface_healthy(primary_metrics)
        secondary_healthy = self.is_interface_healthy(secondary_metrics)
        
        # interface aktif saat ini
        current_interface = self.current_active
        current_metrics = metrics.get(current_interface)
        current_healthy = self.is_interface_healthy(current_metrics)
        
        # jika interface saat ini sehat maka tidak perlu tindakan fail over
        if current_healthy:
            # jika primary interface sehat maka, 
            # cek kembali jika sudah beberapa saat
            if (current_interface == self.secondary_interface and 
                primary_healthy and 
                self.failover_timestamp):
                
                time_since_failover = time.time() - self.failover_timestamp
                if time_since_failover > THRESHOLDS['failover_timeout']:
                    logger.info("Primary interface is healthy again. Switching back.")
                    return True, self.primary_interface
            
            return False, current_interface
        
        # interface aktif saat ini terdeteksi down, membutuhkan failover
        if current_interface == self.primary_interface and secondary_healthy:
            # Failover untuk secondary interface
            return True, self.secondary_interface
        elif current_interface == self.secondary_interface and primary_healthy:
            # Failover untuk primary interfaces
            return True, self.primary_interface
        
        # jika kedua interface terdeteksi down
        if not primary_healthy and not secondary_healthy:
            logger.warning("kedua interfaces terdeteksi down")
            return False, current_interface
        
       
        return False, current_interface