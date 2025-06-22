"""
Game Monitor Component
Central coordinator for game process and connection monitoring.
"""

from typing import Dict, Optional, Callable, List
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
import logging

from .process_tracker import ProcessTracker
from .connection_monitor import ConnectionMonitor


class GameMonitor(QObject):
    """Central game monitoring coordinator."""
    
    game_status_changed = pyqtSignal(str, dict)  # status, full_info
    alert_triggered = pyqtSignal(str, str)       # alert_type, message
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Core monitors
        self.process_tracker = ProcessTracker()
        self.connection_monitor = ConnectionMonitor()
        
        # Current status
        self.game_running = False
        self.connection_active = False
        self.last_status_update = 0
        
        # Alert settings
        self.alerts_enabled = True
        self.alert_callbacks: List[Callable] = []
        
        # Data logging
        self.log_data = True
        self.status_history: List[Dict] = []
        
        self._setup_connections()
    
    def _setup_connections(self) -> None:
        """Setup signal connections between monitors."""
        try:
            # Process tracker signals
            self.process_tracker.process_found.connect(self._on_process_found)
            self.process_tracker.process_lost.connect(self._on_process_lost)
            self.process_tracker.status_changed.connect(self._on_process_status_changed)
            
            # Connection monitor signals
            self.connection_monitor.connection_established.connect(self._on_connection_established)
            self.connection_monitor.connection_lost.connect(self._on_connection_lost)
            self.connection_monitor.connection_status_changed.connect(self._on_connection_status_changed)
            
        except Exception as e:
            self.logger.error(f"Failed to setup monitor connections: {e}")
    
    def start_monitoring(self) -> None:
        """Start all monitoring systems."""
        try:
            self.process_tracker.start_monitoring()
            self.connection_monitor.start_monitoring()
            self.logger.info("Started comprehensive game monitoring")
        except Exception as e:
            self.logger.error(f"Failed to start monitoring: {e}")
    
    def stop_monitoring(self) -> None:
        """Stop all monitoring systems."""
        try:
            self.process_tracker.stop_monitoring()
            self.connection_monitor.stop_monitoring()
            self.logger.info("Stopped comprehensive game monitoring")
        except Exception as e:
            self.logger.error(f"Failed to stop monitoring: {e}")
    
    def _on_process_found(self, pid: int, process_name: str) -> None:
        """Handle game process found."""
        try:
            self.game_running = True
            self._trigger_alert("process_found", f"Game process found: {process_name} (PID: {pid})")
            self._update_status()
        except Exception as e:
            self.logger.error(f"Failed to handle process found: {e}")
    
    def _on_process_lost(self, pid: int) -> None:
        """Handle game process lost."""
        try:
            self.game_running = False
            self._trigger_alert("process_lost", f"Game process lost (PID: {pid})")
            self._update_status()
        except Exception as e:
            self.logger.error(f"Failed to handle process lost: {e}")
    
    def _on_process_status_changed(self, status: str, process_info: Dict) -> None:
        """Handle process status changes."""
        try:
            self._update_status()
        except Exception as e:
            self.logger.error(f"Failed to handle process status change: {e}")
    
    def _on_connection_established(self, connection_type: str) -> None:
        """Handle connection established."""
        try:
            self.connection_active = True
            self._trigger_alert("connection_established", f"Connection established: {connection_type}")
            self._update_status()
        except Exception as e:
            self.logger.error(f"Failed to handle connection established: {e}")
    
    def _on_connection_lost(self, reason: str) -> None:
        """Handle connection lost."""
        try:
            self.connection_active = False
            self._trigger_alert("connection_lost", f"Connection lost: {reason}")
            self._update_status()
        except Exception as e:
            self.logger.error(f"Failed to handle connection lost: {e}")
    
    def _on_connection_status_changed(self, status: str, details: Dict) -> None:
        """Handle connection status changes."""
        try:
            self.connection_active = details.get('connected', False)
            self._update_status()
        except Exception as e:
            self.logger.error(f"Failed to handle connection status change: {e}")
    
    def _update_status(self) -> None:
        """Update overall game status."""
        try:
            import time
            current_time = time.time()
            
            # Gather comprehensive status
            process_status = self.process_tracker.get_current_status()
            connection_status = self.connection_monitor.get_connection_status()
            
            # Determine overall status
            if self.game_running and self.connection_active:
                overall_status = "running_connected"
            elif self.game_running and not self.connection_active:
                overall_status = "running_disconnected"
            elif not self.game_running and self.connection_active:
                overall_status = "not_running_connected"
            else:
                overall_status = "not_running_disconnected"
            
            # Create comprehensive status info
            status_info = {
                'overall_status': overall_status,
                'timestamp': current_time,
                'game_running': self.game_running,
                'connection_active': self.connection_active,
                'process_info': process_status,
                'connection_info': connection_status,
            }
            
            # Log status if enabled
            if self.log_data:
                self._log_status_data(status_info)
            
            # Emit status change
            self.game_status_changed.emit(overall_status, status_info)
            self.last_status_update = current_time
            
        except Exception as e:
            self.logger.error(f"Failed to update status: {e}")
    
    def _trigger_alert(self, alert_type: str, message: str) -> None:
        """Trigger an alert if alerts are enabled."""
        try:
            if self.alerts_enabled:
                self.alert_triggered.emit(alert_type, message)
                self.logger.info(f"Alert: {alert_type} - {message}")
                
                # Execute alert callbacks
                for callback in self.alert_callbacks:
                    try:
                        callback(alert_type, message)
                    except Exception as cb_error:
                        self.logger.error(f"Alert callback failed: {cb_error}")
                        
        except Exception as e:
            self.logger.error(f"Failed to trigger alert: {e}")
    
    def _log_status_data(self, status_info: Dict) -> None:
        """Log status data for analysis."""
        try:
            self.status_history.append(status_info.copy())
            
            # Keep only last 1000 entries
            if len(self.status_history) > 1000:
                self.status_history = self.status_history[-1000:]
                
        except Exception as e:
            self.logger.error(f"Failed to log status data: {e}")
    
    def get_comprehensive_status(self) -> Dict:
        """Get comprehensive monitoring status."""
        try:
            return {
                'monitoring_active': (
                    self.process_tracker.is_monitoring and 
                    self.connection_monitor.is_monitoring
                ),
                'game_running': self.game_running,
                'connection_active': self.connection_active,
                'last_update': self.last_status_update,
                'alerts_enabled': self.alerts_enabled,
                'data_logging': self.log_data,
                'history_entries': len(self.status_history),
                'process_status': self.process_tracker.get_current_status(),
                'connection_status': self.connection_monitor.get_connection_status(),
            }
        except Exception as e:
            self.logger.error(f"Failed to get comprehensive status: {e}")
            return {'error': str(e)}
    
    def get_status_history(self, limit: int = 100) -> List[Dict]:
        """Get recent status history."""
        try:
            return self.status_history[-limit:] if self.status_history else []
        except Exception as e:
            self.logger.error(f"Failed to get status history: {e}")
            return []
    
    def add_alert_callback(self, callback: Callable) -> None:
        """Add an alert callback."""
        try:
            if callback not in self.alert_callbacks:
                self.alert_callbacks.append(callback)
        except Exception as e:
            self.logger.error(f"Failed to add alert callback: {e}")
    
    def set_alerts_enabled(self, enabled: bool) -> None:
        """Enable or disable alerts."""
        try:
            self.alerts_enabled = enabled
            self.logger.info(f"Alerts {'enabled' if enabled else 'disabled'}")
        except Exception as e:
            self.logger.error(f"Failed to set alerts enabled: {e}")
    
    def set_data_logging(self, enabled: bool) -> None:
        """Enable or disable data logging."""
        try:
            self.log_data = enabled
            self.logger.info(f"Data logging {'enabled' if enabled else 'disabled'}")
        except Exception as e:
            self.logger.error(f"Failed to set data logging: {e}")
    
    def force_refresh(self) -> None:
        """Force refresh of all monitoring systems."""
        try:
            self.process_tracker.force_refresh()
            self.connection_monitor.force_check()
            self.logger.info("Forced refresh of all monitors")
        except Exception as e:
            self.logger.error(f"Failed to force refresh: {e}")
