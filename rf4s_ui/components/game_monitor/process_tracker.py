"""
Process Tracker Component
Monitors Russian Fishing 4 game process (PID tracking, status monitoring).
"""

import psutil
import time
from typing import Dict, List, Optional, Callable
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
import logging


class ProcessTracker(QObject):
    """Tracks Russian Fishing 4 game process and status."""
    
    process_found = pyqtSignal(int, str)      # PID, process_name
    process_lost = pyqtSignal(int)            # PID
    status_changed = pyqtSignal(str, dict)    # status, process_info
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Process tracking
        self.target_processes = [
            "RussianFishing4.exe",
            "rf4.exe", 
            "fishing4.exe",
            "russian_fishing_4.exe"
        ]
        
        self.current_pid: Optional[int] = None
        self.current_process: Optional[psutil.Process] = None
        self.process_info: Dict = {}
        
        # Monitoring settings
        self.scan_interval = 2000  # 2 seconds
        self.is_monitoring = False
        
        # Setup monitoring timer
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._scan_processes)
        
        # Process callbacks
        self.status_callbacks: List[Callable] = []
    
    def start_monitoring(self) -> None:
        """Start monitoring for game processes."""
        try:
            if not self.is_monitoring:
                self.is_monitoring = True
                self.monitor_timer.start(self.scan_interval)
                self.logger.info("Started game process monitoring")
                
                # Initial scan
                self._scan_processes()
                
        except Exception as e:
            self.logger.error(f"Failed to start monitoring: {e}")
    
    def stop_monitoring(self) -> None:
        """Stop monitoring game processes."""
        try:
            if self.is_monitoring:
                self.is_monitoring = False
                self.monitor_timer.stop()
                self.logger.info("Stopped game process monitoring")
        except Exception as e:
            self.logger.error(f"Failed to stop monitoring: {e}")
    
    def _scan_processes(self) -> None:
        """Scan for target game processes."""
        try:
            found_processes = []
            
            # Scan all running processes
            for proc in psutil.process_iter(['pid', 'name', 'exe', 'create_time']):
                try:
                    proc_info = proc.info
                    proc_name = proc_info.get('name', '').lower()
                    
                    # Check if this is a target process
                    for target in self.target_processes:
                        if target.lower() in proc_name:
                            found_processes.append((proc, proc_info))
                            break
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Handle found processes
            if found_processes:
                self._handle_found_processes(found_processes)
            else:
                self._handle_no_processes()
                
        except Exception as e:
            self.logger.error(f"Failed to scan processes: {e}")
    
    def _handle_found_processes(self, processes: List) -> None:
        """Handle when game processes are found."""
        try:
            # Use the first found process (or most recent)
            proc, proc_info = processes[0]
            new_pid = proc_info['pid']
            
            # Check if this is a new process
            if self.current_pid != new_pid:
                # Lost old process
                if self.current_pid is not None:
                    self.process_lost.emit(self.current_pid)
                
                # Found new process
                self.current_pid = new_pid
                self.current_process = proc
                self.process_info = self._get_detailed_process_info(proc)
                
                self.process_found.emit(new_pid, proc_info.get('name', 'Unknown'))
                self.logger.info(f"Found game process: PID {new_pid}")
            
            # Update process status
            self._update_process_status()
            
        except Exception as e:
            self.logger.error(f"Failed to handle found processes: {e}")
    
    def _handle_no_processes(self) -> None:
        """Handle when no game processes are found."""
        try:
            if self.current_pid is not None:
                # Process was lost
                lost_pid = self.current_pid
                self.current_pid = None
                self.current_process = None
                self.process_info = {}
                
                self.process_lost.emit(lost_pid)
                self.logger.info(f"Lost game process: PID {lost_pid}")
                
                # Update status to indicate no process
                self.status_changed.emit("not_running", {})
                
        except Exception as e:
            self.logger.error(f"Failed to handle no processes: {e}")
    
    def _get_detailed_process_info(self, proc: psutil.Process) -> Dict:
        """Get detailed information about the process."""
        try:
            info = {
                'pid': proc.pid,
                'name': proc.name(),
                'create_time': proc.create_time(),
                'status': proc.status(),
            }
            
            # Try to get additional info (may fail due to permissions)
            try:
                info.update({
                    'exe': proc.exe(),
                    'cwd': proc.cwd(),
                    'memory_info': proc.memory_info()._asdict(),
                    'cpu_percent': proc.cpu_percent(),
                    'num_threads': proc.num_threads(),
                })
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass
            
            return info
            
        except Exception as e:
            self.logger.error(f"Failed to get process info: {e}")
            return {'pid': proc.pid if proc else 0}
    
    def _update_process_status(self) -> None:
        """Update current process status."""
        try:
            if self.current_process and self.current_process.is_running():
                # Update process info
                updated_info = self._get_detailed_process_info(self.current_process)
                self.process_info.update(updated_info)
                
                # Determine status
                status = self.current_process.status()
                if status == psutil.STATUS_RUNNING:
                    status_str = "running"
                elif status == psutil.STATUS_SLEEPING:
                    status_str = "idle"
                elif status == psutil.STATUS_STOPPED:
                    status_str = "stopped"
                else:
                    status_str = "unknown"
                
                self.status_changed.emit(status_str, self.process_info)
                
                # Execute callbacks
                for callback in self.status_callbacks:
                    try:
                        callback(status_str, self.process_info)
                    except Exception as cb_error:
                        self.logger.error(f"Status callback failed: {cb_error}")
                        
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # Process no longer exists
            self._handle_no_processes()
        except Exception as e:
            self.logger.error(f"Failed to update process status: {e}")
    
    def get_current_status(self) -> Dict:
        """Get current process status information."""
        try:
            if self.current_pid and self.current_process:
                return {
                    'is_running': True,
                    'pid': self.current_pid,
                    'process_info': self.process_info,
                    'uptime': time.time() - self.process_info.get('create_time', time.time()),
                }
            else:
                return {
                    'is_running': False,
                    'pid': None,
                    'process_info': {},
                    'uptime': 0,
                }
        except Exception as e:
            self.logger.error(f"Failed to get current status: {e}")
            return {'is_running': False, 'pid': None, 'process_info': {}, 'uptime': 0}
    
    def add_status_callback(self, callback: Callable) -> None:
        """Add a callback for status updates."""
        try:
            if callback not in self.status_callbacks:
                self.status_callbacks.append(callback)
        except Exception as e:
            self.logger.error(f"Failed to add status callback: {e}")
    
    def remove_status_callback(self, callback: Callable) -> None:
        """Remove a status callback."""
        try:
            if callback in self.status_callbacks:
                self.status_callbacks.remove(callback)
        except Exception as e:
            self.logger.error(f"Failed to remove status callback: {e}")
    
    def set_scan_interval(self, interval_ms: int) -> None:
        """Set the process scanning interval."""
        try:
            self.scan_interval = max(500, interval_ms)  # Minimum 500ms
            if self.is_monitoring:
                self.monitor_timer.setInterval(self.scan_interval)
            self.logger.info(f"Set scan interval to {self.scan_interval}ms")
        except Exception as e:
            self.logger.error(f"Failed to set scan interval: {e}")
    
    def force_refresh(self) -> None:
        """Force an immediate process scan."""
        try:
            self._scan_processes()
        except Exception as e:
            self.logger.error(f"Failed to force refresh: {e}")
    
    def is_game_running(self) -> bool:
        """Check if the game is currently running."""
        return self.current_pid is not None and self.current_process is not None
