#!/usr/bin/env python3
"""
RF4S Memory Manager - Automated Context and State Management
Non-invasive memory integration for preserving application context

This module provides comprehensive memory management for the RF4S UI:
- Application state persistence
- Configuration history tracking
- Error and event logging
- Session data management
- Cross-session context preservation
"""

import json
import pickle
import sqlite3
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class MemoryEntry:
    """Structured memory entry for consistent storage"""

    id: str
    type: str
    timestamp: str
    data: Dict[str, Any]
    tags: List[str]
    priority: int = 1  # 1=low, 2=medium, 3=high, 4=critical


class MemoryManager:
    """
    Comprehensive memory management system for RF4S UI

    Features:
    - Persistent storage using SQLite
    - Automatic context preservation
    - Configuration history tracking
    - Error and event logging
    - Session analytics
    - Memory cleanup and optimization
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or str(Path.home() / ".rf4s_ui" / "memory.db")
        self.db_lock = threading.Lock()

        # Ensure database directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._initialize_database()

        # Memory categories
        self.categories = {
            "application_state": "Application state and settings",
            "configuration": "RF4S configuration changes",
            "errors": "Error logs and diagnostics",
            "events": "Application events and actions",
            "session": "Session data and analytics",
            "user_preferences": "User interface preferences",
            "bridge_status": "Communication bridge status",
            "widget_state": "Widget states and layouts",
        }

        # Start cleanup scheduler
        self._schedule_cleanup()

    def _initialize_database(self):
        """Initialize SQLite database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Main memory table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS memory_entries (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    data TEXT NOT NULL,
                    tags TEXT,
                    priority INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Configuration history table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS config_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    config_data TEXT NOT NULL,
                    changes TEXT,
                    source TEXT
                )
            """
            )

            # Error tracking table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS error_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    error_type TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    traceback TEXT,
                    context TEXT,
                    resolved BOOLEAN DEFAULT FALSE
                )
            """
            )

            # Session tracking table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    duration INTEGER,
                    events_count INTEGER DEFAULT 0,
                    errors_count INTEGER DEFAULT 0,
                    session_data TEXT
                )
            """
            )

            # Create indexes for performance
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_memory_type ON memory_entries(type)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_memory_timestamp ON memory_entries(timestamp)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_config_timestamp ON config_history(timestamp)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_error_timestamp ON error_log(timestamp)"
            )

            conn.commit()

    def store_memory(
        self,
        entry_id: str,
        entry_type: str,
        data: Dict[str, Any],
        tags: List[str] = None,
        priority: int = 1,
    ) -> bool:
        """Store a memory entry with automatic documentation"""
        try:
            with self.db_lock:
                entry = MemoryEntry(
                    id=entry_id,
                    type=entry_type,
                    timestamp=datetime.now().isoformat(),
                    data=data,
                    tags=tags or [],
                    priority=priority,
                )

                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO memory_entries 
                        (id, type, timestamp, data, tags, priority)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,
                        (
                            entry.id,
                            entry.type,
                            entry.timestamp,
                            json.dumps(entry.data),
                            json.dumps(entry.tags),
                            entry.priority,
                        ),
                    )
                    conn.commit()

                return True

        except Exception as e:
            print(f"Error storing memory entry: {e}")
            return False

    def retrieve_memory(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieve a specific memory entry"""
        try:
            with self.db_lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        SELECT id, type, timestamp, data, tags, priority
                        FROM memory_entries WHERE id = ?
                    """,
                        (entry_id,),
                    )

                    row = cursor.fetchone()
                    if row:
                        return MemoryEntry(
                            id=row[0],
                            type=row[1],
                            timestamp=row[2],
                            data=json.loads(row[3]),
                            tags=json.loads(row[4]) if row[4] else [],
                            priority=row[5],
                        )
                    return None

        except Exception as e:
            print(f"Error retrieving memory entry: {e}")
            return None

    def search_memories(
        self,
        entry_type: str = None,
        tags: List[str] = None,
        since: datetime = None,
        limit: int = 100,
    ) -> List[MemoryEntry]:
        """Search memory entries with filters"""
        try:
            with self.db_lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    query = "SELECT id, type, timestamp, data, tags, priority FROM memory_entries WHERE 1=1"
                    params = []

                    if entry_type:
                        query += " AND type = ?"
                        params.append(entry_type)

                    if since:
                        query += " AND timestamp >= ?"
                        params.append(since.isoformat())

                    query += " ORDER BY timestamp DESC LIMIT ?"
                    params.append(limit)

                    cursor.execute(query, params)
                    rows = cursor.fetchall()

                    entries = []
                    for row in rows:
                        entry = MemoryEntry(
                            id=row[0],
                            type=row[1],
                            timestamp=row[2],
                            data=json.loads(row[3]),
                            tags=json.loads(row[4]) if row[4] else [],
                            priority=row[5],
                        )

                        # Filter by tags if specified
                        if tags:
                            if any(tag in entry.tags for tag in tags):
                                entries.append(entry)
                        else:
                            entries.append(entry)

                    return entries

        except Exception as e:
            print(f"Error searching memories: {e}")
            return []

    def store_configuration(self, config: Dict[str, Any], source: str = "ui") -> bool:
        """Store configuration with change tracking"""
        try:
            # Get previous configuration for change detection
            previous_config = self.get_latest_configuration()
            changes = (
                self._detect_config_changes(previous_config, config)
                if previous_config
                else "Initial configuration"
            )

            with self.db_lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        INSERT INTO config_history 
                        (timestamp, config_data, changes, source)
                        VALUES (?, ?, ?, ?)
                    """,
                        (
                            datetime.now().isoformat(),
                            json.dumps(config),
                            json.dumps(changes)
                            if isinstance(changes, dict)
                            else changes,
                            source,
                        ),
                    )
                    conn.commit()

            # Also store in main memory
            self.store_memory(
                f"config_{datetime.now().timestamp()}",
                "configuration",
                {"config": config, "source": source, "changes": changes},
                ["configuration", source],
                priority=2,
            )

            return True

        except Exception as e:
            print(f"Error storing configuration: {e}")
            return False

    def get_latest_configuration(self) -> Optional[Dict[str, Any]]:
        """Get the most recent configuration"""
        try:
            with self.db_lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        SELECT config_data FROM config_history 
                        ORDER BY timestamp DESC LIMIT 1
                    """
                    )

                    row = cursor.fetchone()
                    if row:
                        return json.loads(row[0])
                    return None

        except Exception as e:
            print(f"Error retrieving latest configuration: {e}")
            return None

    def store_error(self, error_details: Dict[str, Any]) -> bool:
        """Store error with detailed context"""
        try:
            with self.db_lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        INSERT INTO error_log 
                        (timestamp, error_type, error_message, traceback, context)
                        VALUES (?, ?, ?, ?, ?)
                    """,
                        (
                            error_details.get("timestamp", datetime.now().isoformat()),
                            error_details.get("type", "unknown"),
                            error_details.get("error", "No message"),
                            error_details.get("traceback", ""),
                            json.dumps(error_details.get("context", {})),
                        ),
                    )
                    conn.commit()

            # Also store in main memory
            self.store_memory(
                f"error_{datetime.now().timestamp()}",
                "error",
                error_details,
                ["error", error_details.get("type", "unknown")],
                priority=3,
            )

            return True

        except Exception as e:
            print(f"Error storing error log: {e}")
            return False

    def store_event(self, event_details: Dict[str, Any]) -> bool:
        """Store application event"""
        return self.store_memory(
            f"event_{datetime.now().timestamp()}",
            "event",
            event_details,
            ["event", event_details.get("type", "unknown")],
            priority=1,
        )

    def store_session_data(self, session_data: Dict[str, Any]) -> bool:
        """Store session information"""
        return self.store_memory(
            f"session_{datetime.now().timestamp()}",
            "session",
            session_data,
            ["session"],
            priority=2,
        )

    def store_application_state(self, state: Dict[str, Any]) -> bool:
        """Store current application state"""
        return self.store_memory(
            "application_state",
            "application_state",
            state,
            ["state", "application"],
            priority=2,
        )

    def get_application_state(self) -> Optional[Dict[str, Any]]:
        """Retrieve current application state"""
        entry = self.retrieve_memory("application_state")
        return entry.data if entry else None

    def store_setting(self, key: str, value: Any) -> bool:
        """Store a single setting"""
        return self.store_memory(
            f"setting_{key}",
            "setting",
            {"key": key, "value": value},
            ["setting", key],
            priority=1,
        )

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Retrieve a single setting"""
        entry = self.retrieve_memory(f"setting_{key}")
        return entry.data.get("value", default) if entry else default

    def store_issues(self, issues: List[Dict[str, Any]]) -> bool:
        """Store detected issues"""
        return self.store_memory(
            f"issues_{datetime.now().timestamp()}",
            "issues",
            {"issues": issues, "count": len(issues)},
            ["issues", "diagnostics"],
            priority=3,
        )

    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent error entries"""
        try:
            with self.db_lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        SELECT timestamp, error_type, error_message, traceback, context, resolved
                        FROM error_log ORDER BY timestamp DESC LIMIT ?
                    """,
                        (limit,),
                    )

                    return [
                        {
                            "timestamp": row[0],
                            "type": row[1],
                            "message": row[2],
                            "traceback": row[3],
                            "context": json.loads(row[4]) if row[4] else {},
                            "resolved": bool(row[5]),
                        }
                        for row in cursor.fetchall()
                    ]

        except Exception as e:
            print(f"Error retrieving recent errors: {e}")
            return []

    def _detect_config_changes(
        self, old_config: Dict[str, Any], new_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Detect changes between configurations"""
        changes = {"added": {}, "modified": {}, "removed": {}}

        # Find added and modified keys
        for key, value in new_config.items():
            if key not in old_config:
                changes["added"][key] = value
            elif old_config[key] != value:
                changes["modified"][key] = {"old": old_config[key], "new": value}

        # Find removed keys
        for key in old_config:
            if key not in new_config:
                changes["removed"][key] = old_config[key]

        return changes

    def _schedule_cleanup(self):
        """Schedule periodic memory cleanup"""
        # This would be implemented with a background thread
        # For now, just a placeholder
        pass

    def cleanup_old_entries(self, days_to_keep: int = 30) -> int:
        """Clean up old memory entries"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)

            with self.db_lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    # Clean up low priority entries older than cutoff
                    cursor.execute(
                        """
                        DELETE FROM memory_entries 
                        WHERE timestamp < ? AND priority = 1
                    """,
                        (cutoff_date.isoformat(),),
                    )

                    deleted_count = cursor.rowcount
                    conn.commit()

                    return deleted_count

        except Exception as e:
            print(f"Error during cleanup: {e}")
            return 0

    def export_memory(self, file_path: str, entry_type: str = None) -> bool:
        """Export memory entries to file"""
        try:
            entries = self.search_memories(entry_type=entry_type, limit=10000)

            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "entry_count": len(entries),
                "entries": [asdict(entry) for entry in entries],
            }

            with open(file_path, "w") as f:
                json.dump(export_data, f, indent=2)

            return True

        except Exception as e:
            print(f"Error exporting memory: {e}")
            return False

    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        try:
            with self.db_lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    # Count entries by type
                    cursor.execute(
                        """
                        SELECT type, COUNT(*) FROM memory_entries GROUP BY type
                    """
                    )
                    type_counts = dict(cursor.fetchall())

                    # Total entries
                    cursor.execute("SELECT COUNT(*) FROM memory_entries")
                    total_entries = cursor.fetchone()[0]

                    # Recent activity (last 24 hours)
                    yesterday = (datetime.now() - timedelta(days=1)).isoformat()
                    cursor.execute(
                        """
                        SELECT COUNT(*) FROM memory_entries WHERE timestamp >= ?
                    """,
                        (yesterday,),
                    )
                    recent_activity = cursor.fetchone()[0]

                    # Error count
                    cursor.execute("SELECT COUNT(*) FROM error_log")
                    error_count = cursor.fetchone()[0]

                    return {
                        "total_entries": total_entries,
                        "entries_by_type": type_counts,
                        "recent_activity_24h": recent_activity,
                        "total_errors": error_count,
                        "database_path": self.db_path,
                    }

        except Exception as e:
            print(f"Error getting memory statistics: {e}")
            return {}
