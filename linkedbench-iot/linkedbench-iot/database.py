#!/usr/bin/env python3
"""
Local database for storing LinkedBench events
Uses SQLite for persistent storage
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger('LinkedBench.Database')


class EventDatabase:
    """SQLite database for LinkedBench events"""
    
    def __init__(self, db_path: str = "/var/lib/linkedbench/events.db"):
        self.db_path = db_path
        
        # Create directory if it doesn't exist
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = None
        self._connect()
        self._init_schema()
        
        logger.info(f"Database initialized at {db_path}")
    
    def _connect(self):
        """Connect to database"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def _init_schema(self):
        """Initialize database schema"""
        try:
            cursor = self.conn.cursor()
            
            # Events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bench_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    mode INTEGER,
                    mode_name TEXT,
                    timestamp TEXT NOT NULL,
                    data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_bench_id ON events(bench_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON events(timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_event_type ON events(event_type)
            """)
            
            self.conn.commit()
            logger.info("Database schema initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize schema: {e}")
            raise
    
    def save_event(self, event: Dict[str, Any]) -> int:
        """Save an event to the database"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                INSERT INTO events (bench_id, event_type, mode, mode_name, timestamp, data)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                event.get('bench_id'),
                event.get('event_type'),
                event.get('mode'),
                event.get('mode_name'),
                event.get('timestamp'),
                json.dumps(event)
            ))
            
            self.conn.commit()
            event_id = cursor.lastrowid
            
            logger.debug(f"Event saved with ID {event_id}")
            return event_id
            
        except Exception as e:
            logger.error(f"Failed to save event: {e}", exc_info=True)
            self.conn.rollback()
            return -1
    
    def get_events(self, bench_id: Optional[str] = None, 
                   limit: int = 100, 
                   offset: int = 0,
                   event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve events from database"""
        try:
            cursor = self.conn.cursor()
            
            query = "SELECT * FROM events WHERE 1=1"
            params = []
            
            if bench_id:
                query += " AND bench_id = ?"
                params.append(bench_id)
            
            if event_type:
                query += " AND event_type = ?"
                params.append(event_type)
            
            query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            events = []
            for row in rows:
                event = dict(row)
                if event['data']:
                    try:
                        event['data'] = json.loads(event['data'])
                    except:
                        pass
                events.append(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to retrieve events: {e}")
            return []
    
    def get_event_by_id(self, event_id: int) -> Optional[Dict[str, Any]]:
        """Get a single event by ID"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
            row = cursor.fetchone()
            
            if row:
                event = dict(row)
                if event['data']:
                    try:
                        event['data'] = json.loads(event['data'])
                    except:
                        pass
                return event
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get event: {e}")
            return None
    
    def get_statistics(self, bench_id: Optional[str] = None, 
                       days: int = 7) -> Dict[str, Any]:
        """Get usage statistics"""
        try:
            cursor = self.conn.cursor()
            
            query_filter = ""
            params = []
            
            if bench_id:
                query_filter = "AND bench_id = ?"
                params.append(bench_id)
            
            # Total events
            cursor.execute(f"""
                SELECT COUNT(*) as total 
                FROM events 
                WHERE datetime(timestamp) > datetime('now', '-{days} days')
                {query_filter}
            """, params)
            total_events = cursor.fetchone()['total']
            
            # Events by type
            cursor.execute(f"""
                SELECT event_type, COUNT(*) as count
                FROM events
                WHERE datetime(timestamp) > datetime('now', '-{days} days')
                {query_filter}
                GROUP BY event_type
            """, params)
            events_by_type = {row['event_type']: row['count'] for row in cursor.fetchall()}
            
            # Mode distribution
            cursor.execute(f"""
                SELECT mode_name, COUNT(*) as count
                FROM events
                WHERE datetime(timestamp) > datetime('now', '-{days} days')
                AND mode_name IS NOT NULL
                {query_filter}
                GROUP BY mode_name
            """, params)
            mode_distribution = {row['mode_name']: row['count'] for row in cursor.fetchall()}
            
            return {
                'total_events': total_events,
                'events_by_type': events_by_type,
                'mode_distribution': mode_distribution,
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
    
    def cleanup_old_events(self, days: int = 30):
        """Delete events older than specified days"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                DELETE FROM events
                WHERE datetime(timestamp) < datetime('now', '-' || ? || ' days')
            """, (days,))
            
            deleted = cursor.rowcount
            self.conn.commit()
            
            logger.info(f"Cleaned up {deleted} old events")
            return deleted
            
        except Exception as e:
            logger.error(f"Failed to cleanup events: {e}")
            self.conn.rollback()
            return 0
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
