# src/ai/training.py
import logging
import pickle
import os
import numpy as np
import pandas as pd
from typing import List, Dict, Any
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from datetime import datetime

from src.monitoring.persistence import MetricsDatabase
from config.settings import MODEL_PATH, FEATURES, DB_PATH

logger = logging.getLogger(__name__)

class FailoverModelTrainer:
    def __init__(self, db_path: str = DB_PATH, model_path: str = MODEL_PATH):
        self.db_path = db_path
        self.model_path = model_path
        self.db = MetricsDatabase(db_path)
        self.db.initialize()
        self.min_samples_required = 100
    
    def prepare_training_data(self) -> tuple:
        """
        Prepare data for training the model
        
        Returns:
            tuple: (X_train, X_test, y_train, y_test)
        """
        # Get metrics from database
        metrics = self.db.get_recent_metrics(limit=10000)
        
        # If not enough data, return None
        if len(metrics) < self.min_samples_required:
            logger.warning(f"Not enough data for training. Have {len(metrics)} samples, need at least {self.min_samples_required}")
            return None
        
        # Get failover events to use as labels
        failover_events = self.db.get_recent_failover_events(limit=1000)
        failover_timestamps = [event['timestamp'] for event in failover_events]
        
        # Create DataFrame from metrics
        df = pd.DataFrame(metrics)
        
        # Create features
        X = self._extract_features(df)
        
        # Create labels (1 if a failover occurred within 5 minutes of the metric)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        y = np.zeros(len(df))
        
        for failover_time in failover_timestamps:
            failover_dt = pd.to_datetime(failover_time)
            # Mark samples within 5 minutes before failover as positive samples
            time_diff = (failover_dt - df['timestamp']).dt.total_seconds()
            positive_indices = ((time_diff >= 0) & (time_diff <= 300))
            y[positive_indices] = 1
        
        # Split into training and test sets
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        return X_train, X_test, y_train, y_test
    
    def _extract_features(self, df: pd.DataFrame) -> np.ndarray:
        """
        Extract features from metrics DataFrame
        
        Args:
            df: DataFrame with metrics
            
        Returns:
            numpy array of features
        """
        # Basic features
        features = []
        
        # Add latency
        if 'latency' in df.columns:
            features.append(df['latency'].fillna(1000).values.reshape(-1, 1))
        
        # Add packet loss
        if 'packet_loss' in df.columns:
            features.append(df['packet_loss'].fillna(100).values.reshape(-1, 1))
        
        # Add bandwidth usage if available
        if 'bandwidth_usage' in df.columns:
            features.append(df['bandwidth_usage'].fillna(0).values.reshape(-1, 1))
        
        # Add time of day as cyclical feature
        hour = pd.to_datetime(df['timestamp']).dt.hour
        time_sin = np.sin(2 * np.pi * hour / 24).values.reshape(-1, 1)
        time_cos = np.cos(2 * np.pi * hour / 24).values.reshape(-1, 1)
        features.append(time_sin)
        features.append(time_cos)
        
        # Add day of week if desired
        day = pd.to_datetime(df['timestamp']).dt.dayofweek
        day_sin = np.sin(2 * np.pi * day / 7).values.reshape(-1, 1)
        day_cos = np.cos(2 * np.pi * day / 7).values.reshape(-1, 1)
        features.append(day_sin)
        features.append(day_cos)
        
        # Combine all features
        return np.hstack(features)
    
    def train_model(self) -> RandomForestClassifier:
        """
        Train the failover prediction model
        
        Returns:
            Trained RandomForestClassifier model
        """
        data = self.prepare_training_data()
        
        if data is None:
            logger.warning("Could not prepare training data, returning default model")
            return RandomForestClassifier(n_estimators=10)
        
        X_train, X_test, y_train, y_test = data
        
        # Train the model
        logger.info("Training failover prediction model...")
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        
        model.fit(X_train, y_train)
        
        # Evaluate the model
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        
        logger.info(f"Model performance: Accuracy={accuracy:.4f}, Precision={precision:.4f}, Recall={recall:.4f}, F1={f1:.4f}")
        
        return model
    
    def save_model(self, model: RandomForestClassifier) -> bool:
        """
        Save the trained model to disk
        
        Args:
            model: Trained RandomForestClassifier model
            
        Returns:
            bool: True if save succeeded, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            
            with open(self.model_path, 'wb') as f:
                pickle.dump(model, f)
            
            logger.info(f"Model saved to {self.model_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            return False
    
    def train_and_save(self) -> bool:
        """
        Train the model and save it to disk
        
        Returns:
            bool: True if the process succeeded, False otherwise
        """
        model = self.train_model()
        return self.save_model(model)


def schedule_training(interval_hours=24):
    """
    Schedule periodic model training
    
    Args:
        interval_hours: Hours between training sessions
    """
    import threading
    import time
    
    def training_job():
        while True:
            try:
                trainer = FailoverModelTrainer()
                trainer.train_and_save()
                logger.info(f"Scheduled training completed. Next training in {interval_hours} hours")
            except Exception as e:
                logger.error(f"Error in scheduled training: {e}")
            
            # Sleep for the specified interval
            time.sleep(interval_hours * 3600)
    
    # Start training thread
    training_thread = threading.Thread(target=training_job)
    training_thread.daemon = True
    training_thread.start()
    logger.info(f"Scheduled training every {interval_hours} hours")
