# src/monitoring/persistence.py
import sqlite3
import logging
import json
import os
from typing import Dict, List, Any
from datetime import datetime

from config.settings import DB_PATH

logger = logging.getLogger(__name__)

class MetricsDatabase:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
    
    def initialize(self):
        """Initialize the database and create tables if they don't exist"""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # Create metrics table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            interface TEXT NOT NULL,
            status TEXT NOT NULL,
            latency REAL,
            packet_loss REAL,
            bandwidth_usage REAL
        )
        ''')
        
        # Create failover events table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS failover_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            from_interface TEXT NOT NULL,
            to_interface TEXT NOT NULL,
            reason TEXT NOT NULL
        )
        ''')
        
        self.conn.commit()
        logger.info(f"Database initialized at {self.db_path}")
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def store_metrics(self, metrics: List[Dict[str, Any]]):
        """Store network metrics in the database"""
        if not self.conn:
            self.initialize()
        
        try:
            for metric in metrics:
                self.cursor.execute('''
                INSERT INTO metrics (timestamp, interface, status, latency, packet_loss, bandwidth_usage)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    metric.get('timestamp', datetime.now().isoformat()),
                    metric.get('interface', 'unknown'),
                    metric.get('status', 'unknown'),
                    metric.get('latency'),
                    metric.get('packet_loss'),
                    metric.get('bandwidth_usage')
                ))
            
            self.conn.commit()
            logger.debug(f"Stored {len(metrics)} metric entries")
        except Exception as e:
            logger.error(f"Failed to store metrics: {e}")
    
    def log_failover_event(self, from_interface: str, to_interface: str, reason: str):
        """Log a failover event to the database"""
        if not self.conn:
            self.initialize()
        
        try:
            self.cursor.execute('''
            INSERT INTO failover_events (timestamp, from_interface, to_interface, reason)
            VALUES (?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                from_interface,
                to_interface,
                reason
            ))
            
            self.conn.commit()
            logger.info(f"Logged failover event: {from_interface} -> {to_interface}: {reason}")
        except Exception as e:
            logger.error(f"Failed to log failover event: {e}")
    
    def get_recent_metrics(self, interface: str = None, limit: int = 100):
        """Get recent metrics for an interface or all interfaces"""
        if not self.conn:
            self.initialize()
        
        try:
            if interface:
                self.cursor.execute('''
                SELECT * FROM metrics 
                WHERE interface = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
                ''', (interface, limit))
            else:
                self.cursor.execute('''
                SELECT * FROM metrics 
                ORDER BY timestamp DESC 
                LIMIT ?
                ''', (limit,))
            
            columns = [description[0] for description in self.cursor.description]
            results = []
            
            for row in self.cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results
        except Exception as e:
            logger.error(f"Failed to get recent metrics: {e}")
            return []
    
    def get_recent_failover_events(self, limit: int = 20):
        """Get recent failover events"""
        if not self.conn:
            self.initialize()
        
        try:
            self.cursor.execute('''
            SELECT * FROM failover_events 
            ORDER BY timestamp DESC 
            LIMIT ?
            ''', (limit,))
            
            columns = [description[0] for description in self.cursor.description]
            results = []
            
            for row in self.cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results
        except Exception as e:
            logger.error(f"Failed to get recent failover events: {e}")
            return []