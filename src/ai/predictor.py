# src/ai/predictor.py
import logging
import pickle
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from sklearn.ensemble import RandomForestClassifier
from datetime import datetime

from config.settings import MODEL_PATH, FEATURES, MAX_LATENCY, MAX_PACKET_LOSS

logger = logging.getLogger(__name__)

class FailoverPredictor:
    def __init__(self, model_path: str = MODEL_PATH):
        self.model_path = model_path
        self.model = self._load_model()
        
        # If model doesn't exist, create a simple rule-based model
        if self.model is None:
            self.model = self._create_basic_model()
    
    def _load_model(self) -> Optional[RandomForestClassifier]:
        """Load the trained model from disk"""
        try:
            with open(self.model_path, 'rb') as f:
                model = pickle.load(f)
            logger.info(f"Model loaded from {self.model_path}")
            return model
        except (FileNotFoundError, IOError):
            logger.warning(f"Model file not found at {self.model_path}, will use rule-based approach")
            return None
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return None
    
    def _create_basic_model(self) -> RandomForestClassifier:
        """Create a simple model for initial use"""
        model = RandomForestClassifier(n_estimators=10)
        # We don't have data yet, so this is just a placeholder
        # The actual prediction will use rules until we have enough data to train
        return model
    
    def _extract_features(self, metrics: Dict[str, Any]) -> List[float]:
        """Extract features from metrics for prediction"""
        features = []
        
        # Add latency (default to high value if None)
        features.append(metrics.get('latency', MAX_LATENCY * 2) if metrics.get('latency') is not None else MAX_LATENCY * 2)
        
        # Add packet loss (default to high value if None)
        features.append(metrics.get('packet_loss', 100) if metrics.get('packet_loss') is not None else 100)
        
        # Add bandwidth usage (default to 0 if None)
        features.append(metrics.get('bandwidth_usage', 0) if metrics.get('bandwidth_usage') is not None else 0)
        
        # Add time of day as a cyclical feature (hour of day converted to sin/cos)
        if 'timestamp' in metrics:
            try:
                dt = datetime.fromisoformat(metrics['timestamp'])
                hour = dt.hour
                # Convert hour to value between 0 and 2π then take sin/cos
                hour_rad = 2 * np.pi * hour / 24
                features.append(np.sin(hour_rad))
                features.append(np.cos(hour_rad))
            except (ValueError, TypeError):
                # Default values if timestamp is invalid
                features.extend([0, 0])
        else:
            # Default values if no timestamp
            features.extend([0, 0])
        
        return features
    
    def predict_failover_need(self, primary_metrics: Dict[str, Any], 
                              secondary_metrics: List[Dict[str, Any]]) -> Tuple[bool, Optional[str], str]:
        """
        Determine if failover is needed and which interface to use
        
        Returns:
            Tuple of (failover_needed, best_interface, reason)
        """
        # Check if primary interface is down
        if primary_metrics.get('status') != 'up':
            logger.warning(f"Primary interface is down")
            best_interface = self._select_best_secondary(secondary_metrics)
            return True, best_interface, "Primary interface is down"
        
        # Check if primary interface exceeds threshold values
        primary_latency = primary_metrics.get('latency')
        primary_packet_loss = primary_metrics.get('packet_loss')
        
        if primary_latency is not None and primary_latency > MAX_LATENCY:
            logger.warning(f"Primary interface latency ({primary_latency}ms) exceeds threshold ({MAX_LATENCY}ms)")
            best_interface = self._select_best_secondary(secondary_metrics)
            return True, best_interface, f"Primary interface latency ({primary_latency}ms) exceeds threshold"
        
        if primary_packet_loss is not None and primary_packet_loss > MAX_PACKET_LOSS:
            logger.warning(f"Primary interface packet loss ({primary_packet_loss}%) exceeds threshold ({MAX_PACKET_LOSS}%)")
            best_interface = self._select_best_secondary(secondary_metrics)
            return True, best_interface, f"Primary interface packet loss ({primary_packet_loss}%) exceeds threshold"
        
        # If we have a trained model, use it for more sophisticated prediction
        if hasattr(self.model, 'predict'):
            try:
                features = self._extract_features(primary_metrics)
                # Reshape for sklearn (expects 2D array)
                prediction = self.model.predict(np.array(features).reshape(1, -1))
                
                if prediction[0] == 1:  # Assuming 1 means failover needed
                    best_interface = self._select_best_secondary(secondary_metrics)
                    return True, best_interface, "AI model predicted failover needed"
            except Exception as e:
                logger.error(f"Error using AI model for prediction: {e}")
        
        # Default: no failover needed
        return False, None, "Primary interface is operating normally"
    
    def _select_best_secondary(self, secondary_metrics: List[Dict[str, Any]]) -> Optional[str]:
        """Select the best secondary interface based on metrics"""
        # Filter to only up interfaces
        available_interfaces = [m for m in secondary_metrics if m.get('status') == 'up']
        
        if not available_interfaces:
            logger.error("No secondary interfaces are available")
            return None
        
        # Sort by latency (if available) and packet loss
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