#!/usr/bin/env python3
"""
RF4S Process Bridge - Non-invasive Process Communication

This bridge provides process monitoring and communication capabilities with RF4S
without modifying its source code. It handles process detection, status monitoring,
and inter-process communication.

Features:
- RF4S process detection and monitoring
- Process status and health checking
- Inter-process communication (IPC)
- Process lifecycle management
- Performance monitoring
- Non-invasive process interaction
"""

import json
import logging
import os
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import psutil


@dataclass
class ProcessInfo:
    """Information about a running process"""

    pid: int
    name: str
    exe: str
    cmdline: List[str]
    status: str
    cpu_percent: float
    memory_percent: float
    memory_info: Dict[str, int]
    create_time: datetime
    cwd: str


class ProcessBridge:
    """
    Non-invasive bridge for RF4S process management

    This bridge allows the UI to monitor and communicate with RF4S processes
    without modifying the RF4S source code. It provides process detection,
    monitoring, and communication capabilities.
    """

    def __init__(self):
        self.rf4s_processes = {}
        self.monitoring_active = False
        self.monitor_thread = None
        self.status_callbacks = {}
        self.logger = logging.getLogger(__name__)
        self.ipc_server = None
        self.ipc_port = 12345  # Default IPC port

    def find_rf4s_processes(self) -> List[ProcessInfo]:
        """Find all running RF4S processes"""
        rf4s_processes = []

        try:
            for proc in psutil.process_iter(
                ["pid", "name", "exe", "cmdline", "status", "cwd"]
            ):
                try:
                    proc_info = proc.info

                    # Check if this is an RF4S process
                    if self._is_rf4s_process(proc_info):
                        # Get additional process information
                        cpu_percent = proc.cpu_percent()
                        memory_percent = proc.memory_percent()
                        memory_info = proc.memory_info()._asdict()
                        create_time = datetime.fromtimestamp(proc.create_time())

                        process_info = ProcessInfo(
                            pid=proc_info["pid"],
                            name=proc_info["name"],
                            exe=proc_info["exe"] or "",
                            cmdline=proc_info["cmdline"] or [],
                            status=proc_info["status"],
                            cpu_percent=cpu_percent,
                            memory_percent=memory_percent,
                            memory_info=memory_info,
                            create_time=create_time,
                            cwd=proc_info["cwd"] or "",
                        )

                        rf4s_processes.append(process_info)

                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.ZombieProcess,
                ):
                    continue

        except Exception as e:
            self.logger.error(f"Error finding RF4S processes: {e}")

        return rf4s_processes

    def _is_rf4s_process(self, proc_info: Dict[str, Any]) -> bool:
        """Check if a process is related to RF4S"""
        try:
            name = proc_info.get("name", "").lower()
            exe = proc_info.get("exe", "").lower()
            cmdline = " ".join(proc_info.get("cmdline", [])).lower()
            cwd = proc_info.get("cwd", "").lower()

            # RF4S process indicators
            rf4s_indicators = [
                "rf4s",
                "russianfishing",
                "fishing4",
                "russian_fishing",
                "rf4script",
            ]

            # Check process name, executable, command line, and working directory
            for indicator in rf4s_indicators:
                if (
                    indicator in name
                    or indicator in exe
                    or indicator in cmdline
                    or indicator in cwd
                ):
                    return True

            # Check for Python processes running RF4S scripts
            if "python" in name and any(
                indicator in cmdline for indicator in rf4s_indicators
            ):
                return True

            return False

        except Exception:
            return False

    def get_process_status(self, pid: int) -> Optional[Dict[str, Any]]:
        """Get detailed status of a specific process"""
        try:
            proc = psutil.Process(pid)

            # Get process information
            status = {
                "pid": pid,
                "name": proc.name(),
                "status": proc.status(),
                "cpu_percent": proc.cpu_percent(),
                "memory_percent": proc.memory_percent(),
                "memory_info": proc.memory_info()._asdict(),
                "num_threads": proc.num_threads(),
                "create_time": datetime.fromtimestamp(proc.create_time()),
                "cwd": proc.cwd(),
                "exe": proc.exe(),
                "cmdline": proc.cmdline(),
                "connections": [],
                "open_files": [],
            }

            # Get network connections (if accessible)
            try:
                connections = proc.connections()
                status["connections"] = [
                    {
                        "fd": conn.fd,
                        "family": conn.family.name
                        if hasattr(conn.family, "name")
                        else str(conn.family),
                        "type": conn.type.name
                        if hasattr(conn.type, "name")
                        else str(conn.type),
                        "laddr": f"{conn.laddr.ip}:{conn.laddr.port}"
                        if conn.laddr
                        else None,
                        "raddr": f"{conn.raddr.ip}:{conn.raddr.port}"
                        if conn.raddr
                        else None,
                        "status": conn.status,
                    }
                    for conn in connections
                ]
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass

            # Get open files (if accessible)
            try:
                open_files = proc.open_files()
                status["open_files"] = [
                    {
                        "path": f.path,
                        "fd": f.fd,
                        "position": getattr(f, "position", None),
                        "mode": getattr(f, "mode", None),
                        "flags": getattr(f, "flags", None),
                    }
                    for f in open_files[:10]  # Limit to first 10 files
                ]
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass

            return status

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            self.logger.warning(f"Cannot get status for process {pid}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error getting process status for {pid}: {e}")
            return None

    def start_monitoring(self, callback: Optional[Callable] = None, interval: int = 5):
        """Start monitoring RF4S processes"""
        if self.monitoring_active:
            self.logger.warning("Process monitoring is already active")
            return

        self.monitoring_active = True
        if callback:
            self.status_callbacks["default"] = callback

        self.monitor_thread = threading.Thread(
            target=self._monitor_processes, args=(interval,), daemon=True
        )
        self.monitor_thread.start()

        self.logger.info("Started RF4S process monitoring")

    def stop_monitoring(self):
        """Stop monitoring RF4S processes"""
        self.monitoring_active = False

        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)

        self.logger.info("Stopped RF4S process monitoring")

    def _monitor_processes(self, interval: int):
        """Monitor RF4S processes in background thread"""
        while self.monitoring_active:
            try:
                current_processes = self.find_rf4s_processes()

                # Update process registry
                current_pids = {proc.pid for proc in current_processes}
                previous_pids = set(self.rf4s_processes.keys())

                # Detect new processes
                new_pids = current_pids - previous_pids
                for proc in current_processes:
                    if proc.pid in new_pids:
                        self.rf4s_processes[proc.pid] = proc
                        self._notify_process_event("started", proc)

                # Detect terminated processes
                terminated_pids = previous_pids - current_pids
                for pid in terminated_pids:
                    if pid in self.rf4s_processes:
                        proc = self.rf4s_processes[pid]
                        del self.rf4s_processes[pid]
                        self._notify_process_event("terminated", proc)

                # Update existing processes
                for proc in current_processes:
                    if proc.pid in previous_pids:
                        old_proc = self.rf4s_processes[proc.pid]
                        self.rf4s_processes[proc.pid] = proc

                        # Check for status changes
                        if old_proc.status != proc.status:
                            self._notify_process_event("status_changed", proc)

                # Notify callbacks with current status
                self._notify_status_callbacks(current_processes)

            except Exception as e:
                self.logger.error(f"Error in process monitoring: {e}")

            time.sleep(interval)

    def _notify_process_event(self, event_type: str, process: ProcessInfo):
        """Notify callbacks of process events"""
        try:
            for callback in self.status_callbacks.values():
                callback(
                    {
                        "type": "process_event",
                        "event": event_type,
                        "process": process,
                        "timestamp": datetime.now(),
                    }
                )
        except Exception as e:
            self.logger.error(f"Error notifying process event: {e}")

    def _notify_status_callbacks(self, processes: List[ProcessInfo]):
        """Notify callbacks with current process status"""
        try:
            status_data = {
                "type": "status_update",
                "processes": processes,
                "count": len(processes),
                "timestamp": datetime.now(),
            }

            for callback in self.status_callbacks.values():
                callback(status_data)

        except Exception as e:
            self.logger.error(f"Error notifying status callbacks: {e}")

    def send_signal(self, pid: int, signal_name: str) -> bool:
        """Send signal to RF4S process"""
        try:
            proc = psutil.Process(pid)

            # Map signal names to signal numbers
            signal_map = {
                "terminate": 15,  # SIGTERM
                "kill": 9,  # SIGKILL
                "interrupt": 2,  # SIGINT
                "stop": 19,  # SIGSTOP
                "continue": 18,  # SIGCONT
            }

            if signal_name.lower() in signal_map:
                if signal_name.lower() == "terminate":
                    proc.terminate()
                elif signal_name.lower() == "kill":
                    proc.kill()
                else:
                    # For other signals, use send_signal
                    proc.send_signal(signal_map[signal_name.lower()])

                self.logger.info(f"Sent {signal_name} signal to process {pid}")
                return True
            else:
                self.logger.error(f"Unknown signal: {signal_name}")
                return False

        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            self.logger.error(f"Cannot send signal to process {pid}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error sending signal to process {pid}: {e}")
            return False

    def launch_rf4s(self, rf4s_path: Path, args: List[str] = None) -> Optional[int]:
        """Launch RF4S process"""
        try:
            if not rf4s_path.exists():
                self.logger.error(f"RF4S executable not found: {rf4s_path}")
                return None

            # Prepare command
            cmd = [str(rf4s_path)]
            if args:
                cmd.extend(args)

            # Launch process
            process = subprocess.Popen(
                cmd,
                cwd=rf4s_path.parent,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                if sys.platform == "win32"
                else 0,
            )

            self.logger.info(f"Launched RF4S process with PID: {process.pid}")
            return process.pid

        except Exception as e:
            self.logger.error(f"Error launching RF4S: {e}")
            return None

    def get_performance_metrics(self, pid: int) -> Optional[Dict[str, Any]]:
        """Get performance metrics for RF4S process"""
        try:
            proc = psutil.Process(pid)

            # Get CPU and memory usage over time
            cpu_percent = proc.cpu_percent(interval=1)
            memory_info = proc.memory_info()
            memory_percent = proc.memory_percent()

            # Get I/O statistics if available
            io_counters = None
            try:
                io_counters = proc.io_counters()._asdict()
            except (psutil.AccessDenied, AttributeError):
                pass

            metrics = {
                "pid": pid,
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "memory_rss": memory_info.rss,
                "memory_vms": memory_info.vms,
                "num_threads": proc.num_threads(),
                "num_fds": proc.num_fds() if hasattr(proc, "num_fds") else None,
                "io_counters": io_counters,
                "timestamp": datetime.now(),
            }

            return metrics

        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            self.logger.warning(f"Cannot get metrics for process {pid}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error getting performance metrics for {pid}: {e}")
            return None

    def start_ipc_server(self, port: int = None) -> bool:
        """Start IPC server for communication with RF4S"""
        try:
            if port:
                self.ipc_port = port

            # TODO: Implement IPC server (could use sockets, named pipes, etc.)
            # This is a placeholder for future IPC implementation
            self.logger.info(f"IPC server would start on port {self.ipc_port}")
            return True

        except Exception as e:
            self.logger.error(f"Error starting IPC server: {e}")
            return False

    def stop_ipc_server(self):
        """Stop IPC server"""
        try:
            if self.ipc_server:
                # TODO: Implement IPC server shutdown
                self.ipc_server = None
                self.logger.info("IPC server stopped")
        except Exception as e:
            self.logger.error(f"Error stopping IPC server: {e}")

    def send_ipc_message(self, pid: int, message: Dict[str, Any]) -> bool:
        """Send IPC message to RF4S process"""
        try:
            # TODO: Implement IPC message sending
            # This could use various methods like:
            # - Named pipes
            # - Sockets
            # - Shared memory
            # - File-based communication

            self.logger.info(f"Would send IPC message to process {pid}: {message}")
            return True

        except Exception as e:
            self.logger.error(f"Error sending IPC message to {pid}: {e}")
            return False

    def register_status_callback(self, name: str, callback: Callable):
        """Register callback for process status updates"""
        self.status_callbacks[name] = callback
        self.logger.info(f"Registered status callback: {name}")

    def unregister_status_callback(self, name: str):
        """Unregister status callback"""
        if name in self.status_callbacks:
            del self.status_callbacks[name]
            self.logger.info(f"Unregistered status callback: {name}")

    def get_system_resources(self) -> Dict[str, Any]:
        """Get system resource usage"""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory": psutil.virtual_memory()._asdict(),
                "disk": psutil.disk_usage("/")._asdict(),
                "network": psutil.net_io_counters()._asdict(),
                "boot_time": datetime.fromtimestamp(psutil.boot_time()),
                "timestamp": datetime.now(),
            }
        except Exception as e:
            self.logger.error(f"Error getting system resources: {e}")
            return {}

    def cleanup(self):
        """Clean up resources"""
        try:
            self.stop_monitoring()
            self.stop_ipc_server()
            self.status_callbacks.clear()
            self.rf4s_processes.clear()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
