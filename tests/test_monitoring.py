import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import sys
import datetime
import json
import time

# Add the src directory to the path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.monitoring.collector import MetricCollector
from src.monitoring.persistence import MetricStorage


class TestMetricCollector(unittest.TestCase):
    def setUp(self):
        # Create mock for router API
        self.mock_router_api = Mock()
        self.collector = MetricCollector(router_api=self.mock_router_api)
    
    def test_collect_interface_status(self):
        # Mock router API response for interface status
        self.mock_router_api.get_interface_status.return_value = {
            'wan1': 'up',
            'wan2': 'down'
        }
        
        # Call the method
        result = self.collector.collect_interface_status()
        
        # Assertions
        self.assertEqual(result['wan1'], 'up')
        self.assertEqual(result['wan2'], 'down')
        self.mock_router_api.get_interface_status.assert_called_once()
    
    def test_collect_latency_metrics(self):
        # Mock router API response for ping test to Google DNS
        self.mock_router_api.ping.return_value = {
            'wan1': {
                'sent': 10, 
                'received': 10, 
                'avg_latency': 45.6,
                'min_latency': 40.2,
                'max_latency': 52.3
            },
            'wan2': {
                'sent': 10, 
                'received': 9, 
                'avg_latency': 75.3,
                'min_latency': 68.4,
                'max_latency': 89.1
            }
        }
        
        # Call the method
        result = self.collector.collect_latency_metrics()
        
        # Assertions
        self.assertAlmostEqual(result['wan1']['avg_latency'], 45.6)
        self.assertAlmostEqual(result['wan2']['avg_latency'], 75.3)
        self.mock_router_api.ping.assert_called_once()
    
    def test_collect_packet_loss(self):
        # Mock router API response for ping test to Google DNS
        self.mock_router_api.ping.return_value = {
            'wan1': {
                'sent': 10, 
                'received': 10, 
                'avg_latency': 45.6
            },
            'wan2': {
                'sent': 10, 
                'received': 8, 
                'avg_latency': 75.3
            }
        }
        
        # Call the method
        result = self.collector.collect_packet_loss()
        
        # Assertions
        self.assertEqual(result['wan1'], 0.0)  # 0% packet loss
        self.assertEqual(result['wan2'], 20.0)  # 20% packet loss (2/10 packets lost)
        self.mock_router_api.ping.assert_called_once()
    
    def test_collect_all_metrics(self):
        # Setup multiple mocks for different API calls
        self.mock_router_api.get_interface_status.return_value = {
            'wan1': 'up',
            'wan2': 'up'
        }
        
        self.mock_router_api.ping.return_value = {
            'wan1': {
                'sent': 10, 
                'received': 10, 
                'avg_latency': 45.6,
                'min_latency': 40.2,
                'max_latency': 52.3
            },
            'wan2': {
                'sent': 10, 
                'received': 9, 
                'avg_latency': 75.3,
                'min_latency': 68.4,
                'max_latency': 89.1
            }
        }
        
        # Call the method
        result = self.collector.collect_all_metrics()
        
        # Assertions
        self.assertEqual(result['wan1']['status'], 'up')
        self.assertEqual(result['wan2']['status'], 'up')
        self.assertAlmostEqual(result['wan1']['latency'], 45.6)
        self.assertAlmostEqual(result['wan2']['latency'], 75.3)
        self.assertEqual(result['wan1']['packet_loss'], 0.0)
        self.assertEqual(result['wan2']['packet_loss'], 10.0)  # 1/10 packets lost = 10%
        
        # Verify API calls
        self.mock_router_api.get_interface_status.assert_called_once()
        self.assertTrue(self.mock_router_api.ping.call_count >= 1)


class TestMetricStorage(unittest.TestCase):
    def setUp(self):
        # Create a temporary database file for testing
        self.db_file = "test_metrics.db"
        # Create storage instance with test DB
        self.storage = MetricStorage(db_file=self.db_file)
    
    def tearDown(self):
        # Clean up temp DB file after tests
        if os.path.exists(self.db_file):
            os.remove(self.db_file)
    
    def test_store_metrics(self):
        # Test data
        timestamp = datetime.datetime.now()
        metrics = {
            'wan1': {
                'status': 'up',
                'latency': 45.6,
                'packet_loss': 0.0
            },
            'wan2': {
                'status': 'up',
                'latency': 75.3,
                'packet_loss': 10.0
            }
        }
        
        # Store metrics
        result = self.storage.store_metrics(metrics, timestamp)
        
        # Assertions
        self.assertTrue(result)
        
        # Verify we can retrieve the stored metrics
        retrieved = self.storage.get_latest_metrics()
        self.assertEqual(retrieved['wan1']['status'], 'up')
        self.assertAlmostEqual(retrieved['wan1']['latency'], 45.6)
        self.assertEqual(retrieved['wan1']['packet_loss'], 0.0)
    
    def test_get_metrics_history(self):
        # Store multiple metrics at different times
        for i in range(5):
            timestamp = datetime.datetime.now() - datetime.timedelta(minutes=i*5)
            metrics = {
                'wan1': {
                    'status': 'up',
                    'latency': 45.0 + i,
                    'packet_loss': i * 0.5
                },
                'wan2': {
                    'status': 'up' if i % 2 == 0 else 'down',
                    'latency': 75.0 + i,
                    'packet_loss': 10.0 + i
                }
            }
            self.storage.store_metrics(metrics, timestamp)
            time.sleep(0.1)  # Ensure unique timestamps
        
        # Get history for last hour
        history = self.storage.get_metrics_history(hours=1)
        
        # Assertions
        self.assertEqual(len(history), 5)
        # Check timestamps are in order (newest first)
        for i in range(1, len(history)):
            self.assertTrue(history[i-1]['timestamp'] > history[i]['timestamp'])
    
    def test_get_latency_trends(self):
        # Store metrics with varying latency
        for i in range(10):
            timestamp = datetime.datetime.now() - datetime.timedelta(minutes=i*10)
            metrics = {
                'wan1': {
                    'status': 'up',
                    'latency': 40.0 + (i * 2),  # Increasing latency
                    'packet_loss': 0.5
                },
                'wan2': {
                    'status': 'up',
                    'latency': 80.0 - i,  # Decreasing latency
                    'packet_loss': 1.0
                }
            }
            self.storage.store_metrics(metrics, timestamp)
            time.sleep(0.1)  # Ensure unique timestamps
        
        # Get trends for both interfaces
        trends = self.storage.get_latency_trends(hours=2)
        
        # Assertions
        self.assertTrue('wan1' in trends)
        self.assertTrue('wan2' in trends)
        self.assertTrue(trends['wan1']['trend'] > 0)  # Increasing trend
        self.assertTrue(trends['wan2']['trend'] < 0)  # Decreasing trend


if __name__ == '__main__':
    unittest.main()
