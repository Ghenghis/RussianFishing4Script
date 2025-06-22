"""
Connection Monitor Component
Monitors game connection status, network activity, and disconnection events.
"""

import socket
import requests
import time
from typing import Dict, List, Optional, Callable
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
import logging


class ConnectionMonitor(QObject):
    """Monitors game connection status and network connectivity."""
    
    connection_established = pyqtSignal(str)    # connection_type
    connection_lost = pyqtSignal(str)           # reason
    connection_status_changed = pyqtSignal(str, dict)  # status, details
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Connection monitoring
        self.is_monitoring = False
        self.check_interval = 5000  # 5 seconds
        
        # Connection status
        self.is_connected = False
        self.last_check_time = 0
        self.connection_history: List[Dict] = []
        
        # Network targets for connectivity testing
        self.test_targets = [
            ("google.com", 80),
            ("8.8.8.8", 53),
            ("1.1.1.1", 53),
        ]
        
        # Game-specific connection tests
        self.game_servers = [
            "rf4game.com",
            "russianfishing4.com",
            # Add actual RF4 server addresses when known
        ]
        
        # Setup monitoring timer
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._check_connection)
        
        # Network manager for HTTP requests
        self.network_manager = QNetworkAccessManager()
        
        # Connection callbacks
        self.status_callbacks: List[Callable] = []
    
    def start_monitoring(self) -> None:
        """Start monitoring network connection."""
        try:
            if not self.is_monitoring:
                self.is_monitoring = True
                self.monitor_timer.start(self.check_interval)
                self.logger.info("Started connection monitoring")
                
                # Initial check
                self._check_connection()
                
        except Exception as e:
            self.logger.error(f"Failed to start connection monitoring: {e}")
    
    def stop_monitoring(self) -> None:
        """Stop monitoring network connection."""
        try:
            if self.is_monitoring:
                self.is_monitoring = False
                self.monitor_timer.stop()
                self.logger.info("Stopped connection monitoring")
        except Exception as e:
            self.logger.error(f"Failed to stop connection monitoring: {e}")
    
    def _check_connection(self) -> None:
        """Check current connection status."""
        try:
            current_time = time.time()
            connection_results = {}
            
            # Test basic internet connectivity
            internet_status = self._test_internet_connectivity()
            connection_results['internet'] = internet_status
            
            # Test game server connectivity
            game_status = self._test_game_servers()
            connection_results['game_servers'] = game_status
            
            # Determine overall connection status
            overall_connected = internet_status['connected']
            connection_quality = self._assess_connection_quality(connection_results)
            
            # Check for status changes
            if overall_connected != self.is_connected:
                self._handle_connection_change(overall_connected, connection_results)
            
            # Update connection history
            self._update_connection_history(current_time, connection_results)
            
            # Emit status update
            status_info = {
                'connected': overall_connected,
                'quality': connection_quality,
                'last_check': current_time,
                'details': connection_results
            }
            
            self.connection_status_changed.emit(
                "connected" if overall_connected else "disconnected",
                status_info
            )
            
            # Execute callbacks
            for callback in self.status_callbacks:
                try:
                    callback(overall_connected, status_info)
                except Exception as cb_error:
                    self.logger.error(f"Connection callback failed: {cb_error}")
            
            self.last_check_time = current_time
            
        except Exception as e:
            self.logger.error(f"Failed to check connection: {e}")
    
    def _test_internet_connectivity(self) -> Dict:
        """Test basic internet connectivity."""
        try:
            results = {
                'connected': False,
                'response_times': [],
                'failed_targets': []
            }
            
            successful_tests = 0
            
            for host, port in self.test_targets:
                try:
                    start_time = time.time()
                    
                    # Test socket connection
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(3)  # 3 second timeout
                    result = sock.connect_ex((host, port))
                    sock.close()
                    
                    response_time = (time.time() - start_time) * 1000  # ms
                    
                    if result == 0:
                        successful_tests += 1
                        results['response_times'].append(response_time)
                    else:
                        results['failed_targets'].append(f"{host}:{port}")
                        
                except Exception as test_error:
                    results['failed_targets'].append(f"{host}:{port} - {str(test_error)}")
            
            # Consider connected if at least one test succeeds
            results['connected'] = successful_tests > 0
            
            if results['response_times']:
                results['avg_response_time'] = sum(results['response_times']) / len(results['response_times'])
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to test internet connectivity: {e}")
            return {'connected': False, 'error': str(e)}
    
    def _test_game_servers(self) -> Dict:
        """Test connectivity to game servers."""
        try:
            results = {
                'reachable_servers': [],
                'unreachable_servers': [],
                'response_times': {}
            }
            
            for server in self.game_servers:
                try:
                    start_time = time.time()
                    
                    # Try HTTP request to server
                    response = requests.get(f"http://{server}", timeout=5)
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status_code < 500:  # Any response except server error
                        results['reachable_servers'].append(server)
                        results['response_times'][server] = response_time
                    else:
                        results['unreachable_servers'].append(f"{server} - HTTP {response.status_code}")
                        
                except requests.RequestException as req_error:
                    # Try basic socket connection as fallback
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(3)
                        result = sock.connect_ex((server, 80))
                        sock.close()
                        
                        if result == 0:
                            results['reachable_servers'].append(server)
                        else:
                            results['unreachable_servers'].append(f"{server} - {str(req_error)}")
                    except Exception:
                        results['unreachable_servers'].append(f"{server} - {str(req_error)}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to test game servers: {e}")
            return {'reachable_servers': [], 'unreachable_servers': [], 'error': str(e)}
    
    def _assess_connection_quality(self, results: Dict) -> str:
        """Assess overall connection quality."""
        try:
            internet = results.get('internet', {})
            
            if not internet.get('connected', False):
                return "no_connection"
            
            avg_response = internet.get('avg_response_time', 1000)
            
            if avg_response < 50:
                return "excellent"
            elif avg_response < 100:
                return "good"
            elif avg_response < 200:
                return "fair"
            elif avg_response < 500:
                return "poor"
            else:
                return "very_poor"
                
        except Exception as e:
            self.logger.error(f"Failed to assess connection quality: {e}")
            return "unknown"
    
    def _handle_connection_change(self, connected: bool, results: Dict) -> None:
        """Handle connection status changes."""
        try:
            if connected and not self.is_connected:
                # Connection established
                self.is_connected = True
                connection_type = "internet"
                
                if results.get('game_servers', {}).get('reachable_servers'):
                    connection_type = "game_servers"
                
                self.connection_established.emit(connection_type)
                self.logger.info(f"Connection established: {connection_type}")
                
            elif not connected and self.is_connected:
                # Connection lost
                self.is_connected = False
                
                # Determine reason for disconnection
                reason = "unknown"
                if not results.get('internet', {}).get('connected'):
                    reason = "internet_disconnected"
                elif not results.get('game_servers', {}).get('reachable_servers'):
                    reason = "game_servers_unreachable"
                
                self.connection_lost.emit(reason)
                self.logger.warning(f"Connection lost: {reason}")
                
        except Exception as e:
            self.logger.error(f"Failed to handle connection change: {e}")
    
    def _update_connection_history(self, timestamp: float, results: Dict) -> None:
        """Update connection history for analysis."""
        try:
            history_entry = {
                'timestamp': timestamp,
                'connected': results.get('internet', {}).get('connected', False),
                'quality': self._assess_connection_quality(results),
                'response_time': results.get('internet', {}).get('avg_response_time', 0)
            }
            
            self.connection_history.append(history_entry)
            
            # Keep only last 100 entries
            if len(self.connection_history) > 100:
                self.connection_history = self.connection_history[-100:]
                
        except Exception as e:
            self.logger.error(f"Failed to update connection history: {e}")
    
    def get_connection_status(self) -> Dict:
        """Get current connection status."""
        try:
            return {
                'is_connected': self.is_connected,
                'last_check': self.last_check_time,
                'is_monitoring': self.is_monitoring,
                'check_interval': self.check_interval,
                'history_entries': len(self.connection_history)
            }
        except Exception as e:
            self.logger.error(f"Failed to get connection status: {e}")
            return {'is_connected': False, 'error': str(e)}
    
    def get_connection_history(self, limit: int = 50) -> List[Dict]:
        """Get recent connection history."""
        try:
            return self.connection_history[-limit:] if self.connection_history else []
        except Exception as e:
            self.logger.error(f"Failed to get connection history: {e}")
            return []
    
    def add_status_callback(self, callback: Callable) -> None:
        """Add a callback for connection status updates."""
        try:
            if callback not in self.status_callbacks:
                self.status_callbacks.append(callback)
        except Exception as e:
            self.logger.error(f"Failed to add status callback: {e}")
    
    def remove_status_callback(self, callback: Callable) -> None:
        """Remove a connection status callback."""
        try:
            if callback in self.status_callbacks:
                self.status_callbacks.remove(callback)
        except Exception as e:
            self.logger.error(f"Failed to remove status callback: {e}")
    
    def set_check_interval(self, interval_ms: int) -> None:
        """Set the connection check interval."""
        try:
            self.check_interval = max(1000, interval_ms)  # Minimum 1 second
            if self.is_monitoring:
                self.monitor_timer.setInterval(self.check_interval)
            self.logger.info(f"Set connection check interval to {self.check_interval}ms")
        except Exception as e:
            self.logger.error(f"Failed to set check interval: {e}")
    
    def force_check(self) -> None:
        """Force an immediate connection check."""
        try:
            self._check_connection()
        except Exception as e:
            self.logger.error(f"Failed to force connection check: {e}")
