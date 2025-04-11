import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import sys

# Add the src directory to the path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.router.mikrotik import MikrotikAPI
from src.router.interfaces import InterfaceManager

class TestMikrotikAPI(unittest.TestCase):
    def setUp(self):
        # Use mock for API client to avoid actual network connections
        self.patcher = patch('routeros_api.RouterOsApiPool')
        self.mock_router_api_pool = self.patcher.start()
        
        # Setup the mock connection and API object
        self.mock_connection = Mock()
        self.mock_api = Mock()
        self.mock_router_api_pool.return_value.get_api.return_value = self.mock_api
        self.mock_router_api_pool.return_value.disconnect.return_value = None
        
        # Create api instance with mock dependencies
        self.api = MikrotikAPI(
            host='192.168.1.1',
            username='admin',
            password='password'
        )
    
    def tearDown(self):
        self.patcher.stop()
    
    def test_connect(self):
        # Test connection to router
        result = self.api.connect()
        
        # Assertions
        self.assertTrue(result)
        self.mock_router_api_pool.assert_called_once_with('192.168.1.1', username='admin', password='password', plaintext_login=True)
        self.mock_router_api_pool.return_value.get_api.assert_called_once()
    
    @patch('routeros_api.RouterOsApiPool')
    def test_connect_failure(self, mock_api_pool):
        # Simulate connection failure
        mock_api_pool.side_effect = Exception("Connection failed")
        
        # Create new API with this mock
        api = MikrotikAPI(
            host='192.168.1.1',
            username='admin',
            password='password'
        )
        
        # Test connection
        result = api.connect()
        
        # Assertions
        self.assertFalse(result)
    
    def test_get_interface_status(self):
        # Prepare mock data for interface list
        mock_interface_path = self.mock_api.get_resource.return_value
        mock_interface_path.get.return_value = [
            {'name': 'wan1', 'running': 'true', 'disabled': 'false'},
            {'name': 'wan2', 'running': 'false', 'disabled': 'false'}
        ]
        
        # Call method
        result = self.api.get_interface_status()
        
        # Assertions
        self.mock_api.get_resource.assert_called_with('/interface')
        self.assertEqual(result['wan1'], 'up')
        self.assertEqual(result['wan2'], 'down')
    
    def test_ping(self):
        # Prepare mock data for ping command
        mock_ping_path = self.mock_api.get_resource.return_value
        mock_ping_path.call.side_effect = [
            # Result for ping through wan1
            [
                {'status': 'echo reply', 'time': '45.6ms'},
                {'status': 'echo reply', 'time': '47.2ms'},
                {'status': 'echo reply', 'time': '42.3ms'},
                {'status': 'echo reply', 'time': '46.8ms'}
            ],
            # Result for ping through wan2
            [
                {'status': 'echo reply', 'time': '75.3ms'},
                {'status': 'timeout', 'time': '0ms'},
                {'status': 'echo reply', 'time': '72.1ms'},
                {'status': 'echo reply', 'time': '78.5ms'}
            ]
        ]
        
        # Call method
        result = self.api.ping(target='8.8.8.8', count=4)
        
        # Assertions
        self.mock_api.get_resource.assert_called_with('/ping')
        self.assertEqual(result['wan1']['sent'], 4)
        self.assertEqual(result['wan1']['received'], 4)
        self.assertAlmostEqual(result['wan1']['avg_latency'], 45.475)  # Average of all pings
        
        self.assertEqual(result['wan2']['sent'], 4)
        self.assertEqual(result['wan2']['received'], 3)  # One timeout
        self.assertAlmostEqual(result['wan2']['avg_latency'], 75.3)  # Average of successful pings
    
    def test_set_route(self):
        # Prepare mock for route resource
        mock_route_resource = self.mock_api.get_resource.return_value
        
        # Mock the update method
        mock_route_resource.update.return_value = None
        
        # Call the method
        result = self.api.set_route(interface='wan2')
        
        # Assertions
        self.mock_api.get_resource.assert_called_with('/ip/route')
        mock_route_resource.update.assert_called_once()
        self.assertTrue(result)
    
    def test_get_active_route(self):
        # Prepare mock for route resource
        mock_route_resource = self.mock_api.get_resource.return_value
        mock_route_resource.get.return_value = [
            {
                'dst-address': '0.0.0.0/0',
                'gateway': '192.168.1.1',
                'gateway-status': 'reachable',
                'active': 'true',
                'interface': 'wan1'
            }
        ]
        
        # Call the method
        result = self.api.get_active_route()
        
        # Assertions
        self.mock_api.get_resource.assert_called_with('/ip/route')
        self.assertEqual(result, 'wan1')
    
    def test_disconnect(self):
        # Call the method
        self.api.disconnect()
        
        # Assertions
        self.mock_router_api_pool.return_value.disconnect.assert_called_once()


class TestInterfaceManager(unittest.TestCase):
    def setUp(self):
        # Mock the MikrotikAPI
        self.mock_mikrotik_api = Mock(spec=MikrotikAPI)
        
        # Create interface manager with mock API
        self.interface_manager = InterfaceManager(
            router_api=self.mock_mikrotik_api,
            primary_interface='wan1',
            backup_interface='wan2'
        )
    
    def test_get_primary_interface(self):
        # Simple test to get primary interface
        self.assertEqual(self.interface_manager.get_primary_interface(), 'wan1')
    
    def test_get_backup_interface(self):
        # Simple test to get backup interface
        self.assertEqual(self.interface_manager.get_backup_interface(), 'wan2')
    
    def test_get_active_interface(self):
        # Mock API call
        self.mock_mikrotik_api.get_active_route.return_value = 'wan1'
        
        # Call the method
        result = self.interface_manager.get_active_interface()
        
        # Assertions
        self.assertEqual(result, 'wan1')
        self.mock_mikrotik_api.get_active_route.assert_called_once()
    
    def test_get_metrics(self):
        # Mock API calls
        self.mock_mikrotik_api.get_interface_status.return_value = {
            'wan1': 'up',
            'wan2': 'up'
        }
        
        self.mock_mikrotik_api.ping.return_value = {
            'wan1': {
                'sent': 5,
                'received': 5,
                'avg_latency': 45.5
            },
            'wan2': {
                'sent': 5,
                'received': 4,
                'avg_latency': 75.0
            }
        }
        
        # Call the method
        result = self.interface_manager.get_metrics()
        
        # Assertions
        self.assertEqual(result['wan1']['status'], 'up')
        self.assertEqual(result['wan1']['latency'], 45.5)
        self.assertEqual(result['wan1']['packet_loss'], 0.0)
        
        self.assertEqual(result['wan2']['status'], 'up')
        self.assertEqual(result['wan2']['latency'], 75.0)
        self.assertEqual(result['wan2']['packet_loss'], 20.0)  # 1 out of 5 = 20%
    
    def test_failover(self):
        # Mock API calls
        self.mock_mikrotik_api.set_route.return_value = True
        self.mock_mikrotik_api.get_active_route.return_value = 'wan1'
        
        # Call the method to failover from wan1 to wan2
        result = self.interface_manager.failover('wan1', 'wan2')
        
        # Assertions
        self.assertTrue(result)
        self.mock_mikrotik_api.set_route.assert_called_once_with(interface='wan2')
    
    def test_failover_to_current_does_nothing(self):
        # Mock API call to show wan2 is already active
        self.mock_mikrotik_api.get_active_route.return_value = 'wan2'
        
        # Call the method to "failover" from wan1 to wan2 (which is already active)
        result = self.interface_manager.failover('wan1', 'wan2')
        
        # Assertions - shouldn't call set_route since wan2 is already active
        self.assertTrue(result)
        self.mock_mikrotik_api.set_route.assert_not_called()
    
    def test_check_interface_health(self):
        # Mock API calls
        self.mock_mikrotik_api.get_interface_status.return_value = {
            'wan1': 'up',
            'wan2': 'up'
        }
        
        self.mock_mikrotik_api.ping.return_value = {
            'wan1': {
                'sent': 5,
                'received': 5,
                'avg_latency': 45.5
            },
            'wan2': {
                'sent': 5,
                'received': 4,
                'avg_latency': 75.0
            }
        }
        
        # Call the method
        primary_health = self.interface_manager.check_interface_health('wan1')
        backup_health = self.interface_manager.check_interface_health('wan2')
        
        # Assertions
        self.assertTrue(primary_health['is_healthy'])
        self.assertEqual(primary_health['status'], 'up')
        self.assertEqual(primary_health['latency'], 45.5)
        self.assertEqual(primary_health['packet_loss'], 0.0)
        
        # Backup is still technically healthy but has some packet loss
        self.assertTrue(backup_health['is_healthy'])
        self.assertEqual(backup_health['status'], 'up')
        self.assertEqual(backup_health['latency'], 75.0)
        self.assertEqual(backup_health['packet_loss'], 20.0)
    
    def test_check_unhealthy_interface(self):
        # Mock API calls for a down interface
        self.mock_mikrotik_api.get_interface_status.return_value = {
            'wan1': 'down',
            'wan2': 'up'
        }
        
        # Ping wouldn't work for down interface
        self.mock_mikrotik_api.ping.return_value = {
            'wan1': {
                'sent': 5,
                'received': 0,
                'avg_latency': None
            },
            'wan2': {
                'sent': 5,
                'received': 5,
                'avg_latency': 75.0
            }
        }
        
        # Call the method
        health = self.interface_manager.check_interface_health('wan1')
        
        # Assertions
        self.assertFalse(health['is_healthy'])
        self.assertEqual(health['status'], 'down')
        self.assertIsNone(health['latency'])
        self.assertEqual(health['packet_loss'], 100.0)


if __name__ == '__main__':
    unittest.main()
