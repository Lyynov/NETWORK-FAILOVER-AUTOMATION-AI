# src/router/mikrotik.py
import logging
from typing import List, Dict, Any, Union
import routeros_api

from config.settings import ROUTER_CONFIG

logger = logging.getLogger(__name__)

class MikrotikRouter:
    def __init__(self):
        self.connection = None
        self.api = None
        self._connect()
    
    def _connect(self) -> None:
        """Establish connection to MikroTik router"""
        try:
            self.connection = routeros_api.RouterOsApiPool(
                ROUTER_CONFIG['host'],
                username=ROUTER_CONFIG['username'],
                password=ROUTER_CONFIG['password'],
                port=ROUTER_CONFIG['port'],
                plaintext_login=True
            )
            self.api = self.connection.get_api()
            logger.info(f"Successfully connected to MikroTik router at {ROUTER_CONFIG['host']}")
        except Exception as e:
            logger.error(f"Failed to connect to MikroTik router: {e}")
            raise
    
    def close(self) -> None:
        """Close connection to router"""
        if self.connection:
            self.connection.disconnect()
            logger.info("Disconnected from MikroTik router")
    
    def get_interfaces(self) -> List[Dict[str, Any]]:
        """Get all interfaces and their status"""
        try:
            interfaces = self.api.get_resource('/interface')
            return interfaces.get()
        except Exception as e:
            logger.error(f"Failed to get interfaces: {e}")
            return []
    
    def get_interface_status(self, interface_name: str) -> Dict[str, Any]:
        """Get status of a specific interface"""
        try:
            interfaces = self.api.get_resource('/interface')
            return interfaces.get(name=interface_name)[0]
        except Exception as e:
            logger.error(f"Failed to get status for interface {interface_name}: {e}")
            return {}
    
    def enable_interface(self, interface_name: str) -> bool:
        """Enable a specific interface"""
        try:
            interfaces = self.api.get_resource('/interface')
            interfaces.set(name=interface_name, disabled='no')
            logger.info(f"Interface {interface_name} has been enabled")
            return True
        except Exception as e:
            logger.error(f"Failed to enable interface {interface_name}: {e}")
            return False
    
    def disable_interface(self, interface_name: str) -> bool:
        """Disable a specific interface"""
        try:
            interfaces = self.api.get_resource('/interface')
            interfaces.set(name=interface_name, disabled='yes')
            logger.info(f"Interface {interface_name} has been disabled")
            return True
        except Exception as e:
            logger.error(f"Failed to disable interface {interface_name}: {e}")
            return False
    
    def ping(self, target: str, count: int = 5, interface: str = None) -> Dict[str, Any]:
        """Ping a target from the router"""
        try:
            ping = self.api.get_resource('/ping')
            params = {
                'address': target,
                'count': count
            }
            if interface:
                params['interface'] = interface
            
            results = ping.call(**params)
            
            # Parse results
            ping_stats = {
                'sent': count,
                'received': 0,
                'min_rtt': float('inf'),
                'max_rtt': 0,
                'avg_rtt': 0
            }
            
            for result in results:
                if 'time' in result:
                    ping_stats['received'] += 1
                    rtt = float(result['time'].replace('ms', ''))
                    ping_stats['min_rtt'] = min(ping_stats['min_rtt'], rtt)
                    ping_stats['max_rtt'] = max(ping_stats['max_rtt'], rtt)
                    ping_stats['avg_rtt'] += rtt
            
            if ping_stats['received'] > 0:
                ping_stats['avg_rtt'] /= ping_stats['received']
                if ping_stats['min_rtt'] == float('inf'):
                    ping_stats['min_rtt'] = 0
            else:
                ping_stats['min_rtt'] = 0
            
            ping_stats['packet_loss'] = (1 - ping_stats['received'] / ping_stats['sent']) * 100
            
            return ping_stats
        except Exception as e:
            logger.error(f"Failed to ping {target}: {e}")
            return {
                'sent': count,
                'received': 0,
                'min_rtt': 0,
                'max_rtt': 0,
                'avg_rtt': 0,
                'packet_loss': 100
            }