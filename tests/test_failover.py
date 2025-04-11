import unittest
from unittest.mock import Mock, patch
import os
import sys

# Add the src directory to the path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.failover.controller import FailoverController
from src.failover.decision import DecisionEngine
from src.router.interfaces import InterfaceManager

class TestDecisionEngine(unittest.TestCase):
    def setUp(self):
        self.decision_engine = DecisionEngine()
    
    def test_should_failover_with_high_latency(self):
        # Test case: High latency should trigger failover
        metrics = {
            'wan1': {
                'status': 'up',
                'latency': 500.0,  # High latency
                'packet_loss': 0.5
            },
            'wan2': {
                'status': 'up',
                'latency': 50.0,
                'packet_loss': 0.0
            }
        }
        
        result, reason = self.decision_engine.should_failover('wan1', 'wan2', metrics)
        self.assertTrue(result)
        self.assertIn('latency', reason.lower())
    
    def test_should_failover_with_high_packet_loss(self):
        # Test case: High packet loss should trigger failover
        metrics = {
            'wan1': {
                'status': 'up',
                'latency': 50.0,
                'packet_loss': 20.0  # High packet loss
            },
            'wan2': {
                'status': 'up',
                'latency': 60.0,
                'packet_loss': 0.5
            }
        }
        
        result, reason = self.decision_engine.should_failover('wan1', 'wan2', metrics)
        self.assertTrue(result)
        self.assertIn('packet loss', reason.lower())
    
    def test_should_failover_with_interface_down(self):
        # Test case: Primary interface down should trigger failover
        metrics = {
            'wan1': {
                'status': 'down',  # Interface down
                'latency': None,
                'packet_loss': None
            },
            'wan2': {
                'status': 'up',
                'latency': 60.0,
                'packet_loss': 0.5
            }
        }
        
        result, reason = self.decision_engine.should_failover('wan1', 'wan2', metrics)
        self.assertTrue(result)
        self.assertIn('down', reason.lower())
    
    def test_should_not_failover_when_all_metrics_good(self):
        # Test case: Good metrics should not trigger failover
        metrics = {
            'wan1': {
                'status': 'up',
                'latency': 30.0,
                'packet_loss': 0.1
            },
            'wan2': {
                'status': 'up',
                'latency': 40.0,
                'packet_loss': 0.2
            }
        }
        
        result, reason = self.decision_engine.should_failover('wan1', 'wan2', metrics)
        self.assertFalse(result)
    
    def test_should_not_failover_when_backup_worse(self):
        # Test case: Don't failover if backup is worse than primary
        metrics = {
            'wan1': {
                'status': 'up',
                'latency': 100.0,  # High but not terrible
                'packet_loss': 2.0
            },
            'wan2': {
                'status': 'up',
                'latency': 200.0,  # Worse than primary
                'packet_loss': 5.0  # Worse than primary
            }
        }
        
        result, reason = self.decision_engine.should_failover('wan1', 'wan2', metrics)
        self.assertFalse(result)
        self.assertIn('backup interface', reason.lower())


class TestFailoverController(unittest.TestCase):
    def setUp(self):
        # Create mocks for dependencies
        self.mock_interface_manager = Mock(spec=InterfaceManager)
        self.mock_decision_engine = Mock(spec=DecisionEngine)
        
        # Create the controller with mocked dependencies
        self.controller = FailoverController(
            self.mock_interface_manager,
            self.mock_decision_engine
        )
    
    def test_check_and_handle_failover_performs_failover_when_needed(self):
        # Setup mocks
        self.mock_interface_manager.get_primary_interface.return_value = 'wan1'
        self.mock_interface_manager.get_backup_interface.return_value = 'wan2'
        self.mock_interface_manager.get_active_interface.return_value = 'wan1'
        self.mock_interface_manager.get_metrics.return_value = {
            'wan1': {'status': 'up', 'latency': 500.0, 'packet_loss': 5.0},
            'wan2': {'status': 'up', 'latency': 50.0, 'packet_loss': 0.5}
        }
        
        # Mock decision engine to recommend failover
        self.mock_decision_engine.should_failover.return_value = (True, "High latency on primary")
        
        # Call the method
        result = self.controller.check_and_handle_failover()
        
        # Assertions
        self.assertTrue(result)
        self.mock_decision_engine.should_failover.assert_called_once()
        self.mock_interface_manager.failover.assert_called_once_with('wan1', 'wan2')
    
    def test_check_and_handle_failover_does_nothing_when_not_needed(self):
        # Setup mocks
        self.mock_interface_manager.get_primary_interface.return_value = 'wan1'
        self.mock_interface_manager.get_backup_interface.return_value = 'wan2'
        self.mock_interface_manager.get_active_interface.return_value = 'wan1'
        self.mock_interface_manager.get_metrics.return_value = {
            'wan1': {'status': 'up', 'latency': 30.0, 'packet_loss': 0.1},
            'wan2': {'status': 'up', 'latency': 40.0, 'packet_loss': 0.2}
        }
        
        # Mock decision engine to not recommend failover
        self.mock_decision_engine.should_failover.return_value = (False, "All metrics good")
        
        # Call the method
        result = self.controller.check_and_handle_failover()
        
        # Assertions
        self.assertFalse(result)
        self.mock_decision_engine.should_failover.assert_called_once()
        self.mock_interface_manager.failover.assert_not_called()
    
    def test_force_failover(self):
        # Setup mocks
        self.mock_interface_manager.get_primary_interface.return_value = 'wan1'
        self.mock_interface_manager.get_backup_interface.return_value = 'wan2'
        self.mock_interface_manager.get_active_interface.return_value = 'wan1'
        
        # Call the method
        self.controller.force_failover()
        
        # Assertions
        self.mock_interface_manager.failover.assert_called_once_with('wan1', 'wan2')
    
    def test_restore_primary(self):
        # Setup mocks
        self.mock_interface_manager.get_primary_interface.return_value = 'wan1'
        self.mock_interface_manager.get_backup_interface.return_value = 'wan2'
        self.mock_interface_manager.get_active_interface.return_value = 'wan2'
        
        # Mock metrics to show primary is healthy
        self.mock_interface_manager.get_metrics.return_value = {
            'wan1': {'status': 'up', 'latency': 30.0, 'packet_loss': 0.1},
            'wan2': {'status': 'up', 'latency': 40.0, 'packet_loss': 0.2}
        }
        
        # Call the method
        result = self.controller.restore_primary()
        
        # Assertions
        self.assertTrue(result)
        self.mock_interface_manager.failover.assert_called_once_with('wan2', 'wan1')


if __name__ == '__main__':
    unittest.main()
