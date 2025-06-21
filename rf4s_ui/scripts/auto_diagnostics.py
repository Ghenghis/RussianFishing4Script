#!/usr/bin/env python3
"""
RF4S Auto Diagnostics - Automated System Diagnostics and Repair
Comprehensive system validation and auto-repair capabilities

This module provides automated diagnostics for:
- System requirements validation
- RF4S installation detection
- Dependency verification
- Configuration validation
- Performance optimization
- Auto-repair of common issues
"""

import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import psutil


class AutoDiagnostics:
    """
    Comprehensive auto-diagnostics and repair system

    Features:
    - System requirements checking
    - RF4S installation detection
    - Dependency validation
    - Configuration verification
    - Performance optimization
    - Automated issue repair
    """

    def __init__(self):
        self.system_info = self._get_system_info()
        self.requirements = self._get_requirements()
        self.repair_log = []

    def _get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        try:
            return {
                "platform": platform.platform(),
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "python_version": platform.python_version(),
                "python_executable": sys.executable,
                "memory_total_gb": round(
                    psutil.virtual_memory().total / (1024**3), 2
                ),
                "cpu_count": psutil.cpu_count(),
                "disk_free_gb": round(shutil.disk_usage(".").free / (1024**3), 2),
            }
        except Exception as e:
            return {"error": str(e)}

    def _get_requirements(self) -> Dict[str, Any]:
        """Get system requirements for RF4S UI"""
        return {
            "python_min_version": (3, 8),
            "memory_min_gb": 2,
            "disk_min_gb": 1,
            "required_packages": [
                "PyQt6",
                "PyQt-Fluent-Widgets",
                "watchdog",
                "psutil",
                "Pillow",
                "numpy",
            ],
            "optional_packages": ["opencv-python", "requests", "pyyaml"],
        }

    def check_system_requirements(self) -> List[Dict[str, Any]]:
        """Check system requirements and return issues"""
        issues = []

        try:
            issues.extend(self._check_python_version())
            issues.extend(self._check_memory_requirements())
            issues.extend(self._check_disk_space())
            issues.extend(self._check_required_packages())
            issues.extend(self._check_optional_packages())

        except Exception as e:
            issues.append(
                {
                    "type": "system_check_error",
                    "severity": "high",
                    "title": "System Check Error",
                    "description": f"Error during system requirements check: {e}",
                    "auto_repairable": False,
                    "suggested_fix": "Review system configuration and try again",
                }
            )

        return issues

    def _check_python_version(self) -> List[Dict[str, Any]]:
        """Check Python version requirements"""
        issues = []
        current_python = sys.version_info[:2]
        required_python = self.requirements["python_min_version"]

        if current_python < required_python:
            issues.append(
                {
                    "type": "python_version",
                    "severity": "critical",
                    "title": "Python Version Too Old",
                    "description": f"Python {required_python[0]}.{required_python[1]}+ required, found {current_python[0]}.{current_python[1]}",
                    "auto_repairable": False,
                    "suggested_fix": f"Upgrade Python to {required_python[0]}.{required_python[1]} or higher",
                }
            )

        return issues

    def _check_memory_requirements(self) -> List[Dict[str, Any]]:
        """Check system memory requirements"""
        issues = []
        memory_gb = self.system_info.get("memory_total_gb", 0)

        if memory_gb < self.requirements["memory_min_gb"]:
            issues.append(
                {
                    "type": "insufficient_memory",
                    "severity": "high",
                    "title": "Insufficient System Memory",
                    "description": f'At least {self.requirements["memory_min_gb"]}GB RAM required, found {memory_gb}GB',
                    "auto_repairable": False,
                    "suggested_fix": "Add more system memory or close other applications",
                }
            )

        return issues

    def _check_disk_space(self) -> List[Dict[str, Any]]:
        """Check disk space requirements"""
        issues = []
        disk_gb = self.system_info.get("disk_free_gb", 0)

        if disk_gb < self.requirements["disk_min_gb"]:
            issues.append(
                {
                    "type": "insufficient_disk",
                    "severity": "medium",
                    "title": "Low Disk Space",
                    "description": f'At least {self.requirements["disk_min_gb"]}GB free space recommended, found {disk_gb}GB',
                    "auto_repairable": False,
                    "suggested_fix": "Free up disk space",
                }
            )

        return issues

    def _check_required_packages(self) -> List[Dict[str, Any]]:
        """Check required packages"""
        issues = []

        for package in self.requirements["required_packages"]:
            if not self._check_package_installed(package):
                issues.append(
                    {
                        "type": "missing_package",
                        "severity": "critical",
                        "title": f"Missing Required Package: {package}",
                        "description": f"Required package {package} is not installed",
                        "auto_repairable": True,
                        "suggested_fix": f"pip install {package}",
                        "package_name": package,
                    }
                )

        return issues

    def _check_optional_packages(self) -> List[Dict[str, Any]]:
        """Check optional packages"""
        issues = []

        for package in self.requirements["optional_packages"]:
            if not self._check_package_installed(package):
                issues.append(
                    {
                        "type": "missing_optional_package",
                        "severity": "low",
                        "title": f"Missing Optional Package: {package}",
                        "description": f"Optional package {package} is not installed",
                        "auto_repairable": True,
                        "suggested_fix": f"pip install {package}",
                        "package_name": package,
                    }
                )

        return issues

    def check_rf4s_installation(self) -> List[Dict[str, Any]]:
        """Check RF4S installation and configuration"""
        issues = []

        try:
            # Common RF4S installation paths
            possible_paths = [
                Path("C:/RF4S"),
                Path("C:/RussianFishing4Script"),
                Path.home() / "RF4S",
                Path.cwd().parent / "rf4s",
                Path("C:/Users") / os.getenv("USERNAME", "") / "RF4S",
            ]

            rf4s_found = False
            rf4s_path = None

            for path in possible_paths:
                if path.exists() and (path / "rf4s").exists():
                    rf4s_found = True
                    rf4s_path = path
                    break

            if not rf4s_found:
                issues.append(
                    {
                        "type": "rf4s_not_found",
                        "severity": "high",
                        "title": "RF4S Installation Not Found",
                        "description": "RF4S installation could not be detected",
                        "auto_repairable": False,
                        "suggested_fix": "Install RF4S or specify installation path manually",
                    }
                )
            else:
                # Check RF4S configuration
                config_issues = self._check_rf4s_config(rf4s_path)
                issues.extend(config_issues)

                # Check RF4S permissions
                permission_issues = self._check_rf4s_permissions(rf4s_path)
                issues.extend(permission_issues)

        except Exception as e:
            issues.append(
                {
                    "type": "rf4s_check_error",
                    "severity": "medium",
                    "title": "RF4S Check Error",
                    "description": f"Error checking RF4S installation: {e}",
                    "auto_repairable": False,
                    "suggested_fix": "Review RF4S installation and permissions",
                }
            )

        return issues

    def _check_rf4s_config(self, rf4s_path: Path) -> List[Dict[str, Any]]:
        """Check RF4S configuration files"""
        issues = []

        try:
            config_path = rf4s_path / "config"

            if not config_path.exists():
                issues.append(
                    {
                        "type": "missing_config_dir",
                        "severity": "medium",
                        "title": "Missing RF4S Config Directory",
                        "description": f"Config directory not found at {config_path}",
                        "auto_repairable": True,
                        "suggested_fix": "Create config directory structure",
                        "config_path": str(config_path),
                    }
                )
            else:
                # Check for essential config files
                essential_configs = ["config.json", "settings.ini"]

                for config_file in essential_configs:
                    config_file_path = config_path / config_file
                    if not config_file_path.exists():
                        issues.append(
                            {
                                "type": "missing_config_file",
                                "severity": "low",
                                "title": f"Missing Config File: {config_file}",
                                "description": f"Config file {config_file} not found",
                                "auto_repairable": True,
                                "suggested_fix": f"Create default {config_file}",
                                "config_file": config_file,
                                "config_path": str(config_path),
                            }
                        )

        except Exception as e:
            issues.append(
                {
                    "type": "config_check_error",
                    "severity": "low",
                    "title": "Config Check Error",
                    "description": f"Error checking RF4S config: {e}",
                    "auto_repairable": False,
                    "suggested_fix": "Review RF4S configuration manually",
                }
            )

        return issues

    def _check_rf4s_permissions(self, rf4s_path: Path) -> List[Dict[str, Any]]:
        """Check RF4S file permissions"""
        issues = []

        try:
            # Check read permissions
            if not os.access(rf4s_path, os.R_OK):
                issues.append(
                    {
                        "type": "rf4s_read_permission",
                        "severity": "high",
                        "title": "RF4S Read Permission Denied",
                        "description": f"Cannot read RF4S directory: {rf4s_path}",
                        "auto_repairable": False,
                        "suggested_fix": "Run as administrator or check file permissions",
                    }
                )

            # Check write permissions for config
            config_path = rf4s_path / "config"
            if config_path.exists() and not os.access(config_path, os.W_OK):
                issues.append(
                    {
                        "type": "rf4s_write_permission",
                        "severity": "medium",
                        "title": "RF4S Config Write Permission Denied",
                        "description": f"Cannot write to RF4S config directory: {config_path}",
                        "auto_repairable": False,
                        "suggested_fix": "Run as administrator or adjust file permissions",
                    }
                )

        except Exception as e:
            issues.append(
                {
                    "type": "permission_check_error",
                    "severity": "low",
                    "title": "Permission Check Error",
                    "description": f"Error checking RF4S permissions: {e}",
                    "auto_repairable": False,
                    "suggested_fix": "Review file permissions manually",
                }
            )

        return issues

    def auto_repair_issues(self, issues: List[Dict[str, Any]]) -> int:
        """Attempt to automatically repair issues"""
        repaired_count = 0

        for issue in issues:
            if issue.get("auto_repairable", False):
                try:
                    if self._repair_issue(issue):
                        repaired_count += 1
                        issue["repaired"] = True
                        self.repair_log.append(
                            {
                                "issue": issue["title"],
                                "repair_time": datetime.now().isoformat(),
                                "status": "success",
                            }
                        )
                    else:
                        issue["repaired"] = False
                        self.repair_log.append(
                            {
                                "issue": issue["title"],
                                "repair_time": datetime.now().isoformat(),
                                "status": "failed",
                            }
                        )
                except Exception as e:
                    issue["repaired"] = False
                    self.repair_log.append(
                        {
                            "issue": issue["title"],
                            "repair_time": datetime.now().isoformat(),
                            "status": "error",
                            "error": str(e),
                        }
                    )

        return repaired_count

    def _repair_issue(self, issue: Dict[str, Any]) -> bool:
        """Repair a specific issue"""
        try:
            issue_type = issue.get("type", "")

            if issue_type == "missing_package":
                return self._repair_missing_package(issue)
            elif issue_type == "missing_optional_package":
                return self._repair_missing_package(issue)
            elif issue_type == "missing_config_dir":
                return self._repair_missing_config_dir(issue)
            elif issue_type == "missing_config_file":
                return self._repair_missing_config_file(issue)
            else:
                print(f"No auto-repair available for issue type: {issue_type}")
                return False

        except Exception as e:
            print(f"Error repairing issue {issue.get('title', 'Unknown')}: {e}")
            return False

    def _repair_missing_package(self, issue: Dict[str, Any]) -> bool:
        """Repair missing package by installing it"""
        try:
            package_name = issue.get("package_name", "")
            if not package_name:
                return False

            print(f"Installing package: {package_name}")

            # Use pip to install the package
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package_name],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode == 0:
                print(f"Successfully installed {package_name}")
                return True
            else:
                print(f"Failed to install {package_name}: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print(f"Timeout installing {package_name}")
            return False
        except Exception as e:
            print(f"Error installing {package_name}: {e}")
            return False

    def _repair_missing_config_dir(self, issue: Dict[str, Any]) -> bool:
        """Repair missing config directory"""
        try:
            config_path = Path(issue.get("config_path", ""))
            if not config_path:
                return False

            config_path.mkdir(parents=True, exist_ok=True)
            print(f"Created config directory: {config_path}")
            return True

        except Exception as e:
            print(f"Error creating config directory: {e}")
            return False

    def _repair_missing_config_file(self, issue: Dict[str, Any]) -> bool:
        """Repair missing config file by creating default"""
        try:
            config_file = issue.get("config_file", "")
            config_path = Path(issue.get("config_path", ""))

            if not config_file or not config_path:
                return False

            config_file_path = config_path / config_file

            # Create default config content
            if config_file.endswith(".json"):
                default_content = json.dumps(
                    {
                        "created_by": "RF4S UI Auto-Repair",
                        "created_at": datetime.now().isoformat(),
                        "version": "1.0.0",
                    },
                    indent=2,
                )
            elif config_file.endswith(".ini"):
                default_content = f"""# RF4S Configuration File
# Created by RF4S UI Auto-Repair on {datetime.now().isoformat()}

[general]
version = 1.0.0
created_by = RF4S UI Auto-Repair
"""
            else:
                default_content = f"# Default config file created by RF4S UI Auto-Repair\n# {datetime.now().isoformat()}\n"

            with open(config_file_path, "w", encoding="utf-8") as f:
                f.write(default_content)

            print(f"Created default config file: {config_file_path}")
            return True

        except Exception as e:
            print(f"Error creating config file: {e}")
            return False

    def _check_package_installed(self, package_name: str) -> bool:
        """Check if a package is installed"""
        try:
            # Handle package name variations
            import_name = package_name.replace("-", "_").lower()

            # Special cases for package names
            if package_name == "PyQt6":
                import_name = "PyQt6"
            elif package_name == "PyQt-Fluent-Widgets":
                import_name = "qfluentwidgets"
            elif package_name == "opencv-python":
                import_name = "cv2"

            __import__(import_name)
            return True
        except ImportError:
            return False

    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        return self.system_info.copy()

    def get_repair_log(self) -> List[Dict[str, Any]]:
        """Get the repair log"""
        return self.repair_log.copy()

    def generate_diagnostic_report(self) -> str:
        """Generate a comprehensive diagnostic report"""
        try:
            system_issues = self.check_system_requirements()
            rf4s_issues = self.check_rf4s_installation()
            all_issues = system_issues + rf4s_issues

            report_header = self._generate_report_header()
            system_info_section = self._generate_system_info_section()
            issues_summary = self._generate_issues_summary(all_issues)
            issues_details = self._generate_issues_details(all_issues)
            repair_log_section = self._generate_repair_log_section()

            return f"{report_header}\n{system_info_section}\n{issues_summary}\n{issues_details}\n{repair_log_section}"

        except Exception as e:
            return f"Error generating diagnostic report: {e}"

    def _generate_report_header(self) -> str:
        """Generate report header"""
        return f"""# RF4S UI Diagnostic Report

## Generated
{datetime.now().isoformat()}"""

    def _generate_system_info_section(self) -> str:
        """Generate system information section"""
        return f"""
## System Information
- **Platform**: {self.system_info.get('platform', 'Unknown')}
- **Python Version**: {self.system_info.get('python_version', 'Unknown')}
- **Memory**: {self.system_info.get('memory_total_gb', 0)}GB
- **CPU Cores**: {self.system_info.get('cpu_count', 0)}
- **Free Disk Space**: {self.system_info.get('disk_free_gb', 0)}GB"""

    def _generate_issues_summary(self, all_issues: List[Dict[str, Any]]) -> str:
        """Generate issues summary section"""
        return f"""
## Issues Summary
- **Total Issues**: {len(all_issues)}
- **Critical**: {len([i for i in all_issues if i.get('severity') == 'critical'])}
- **High**: {len([i for i in all_issues if i.get('severity') == 'high'])}
- **Medium**: {len([i for i in all_issues if i.get('severity') == 'medium'])}
- **Low**: {len([i for i in all_issues if i.get('severity') == 'low'])}
- **Auto-repairable**: {len([i for i in all_issues if i.get('auto_repairable', False)])}

## Issues Details"""

    def _generate_issues_details(self, all_issues: List[Dict[str, Any]]) -> str:
        """Generate detailed issues section"""
        details = ""

        for i, issue in enumerate(all_issues, 1):
            severity_icon = self._get_severity_icon(issue.get("severity", "low"))
            auto_repair = "🔧" if issue.get("auto_repairable", False) else "🔨"

            details += f"""
### {i}. {severity_icon} {issue.get('title', 'Unknown Issue')}
- **Severity**: {issue.get('severity', 'unknown').title()}
- **Type**: {issue.get('type', 'unknown')}
- **Auto-repair**: {auto_repair} {'Available' if issue.get('auto_repairable', False) else 'Manual'}
- **Description**: {issue.get('description', 'No description')}
- **Suggested Fix**: {issue.get('suggested_fix', 'No suggestion')}
"""

        return details

    def _generate_repair_log_section(self) -> str:
        """Generate repair log section"""
        if not self.repair_log:
            return ""

        section = "\n## Repair Log\n"
        for repair in self.repair_log:
            status_icon = "✅" if repair["status"] == "success" else "❌"
            section += f"- {status_icon} {repair['issue']} - {repair['status']} at {repair['repair_time']}\n"

        section += "\n---\n*Generated by RF4S UI Auto-Diagnostics*"
        return section

    def _get_severity_icon(self, severity: str) -> str:
        """Get icon for severity level"""
        return {"critical": "🚨", "high": "🔴", "medium": "🟠", "low": "🟡"}.get(
            severity, "⚪"
        )
