#!/usr/bin/env python3
"""
RF4S Issue Detector - Automated Issue Detection and Flagging System
Proactive issue identification with placeholder generation

This module provides comprehensive issue detection for:
- Code quality problems
- Configuration errors
- Missing dependencies
- Performance bottlenecks
- Integration failures
- UI responsiveness issues
"""

import ast
import json
import os
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import psutil


@dataclass
class Issue:
    """Structured issue representation"""

    id: str
    title: str
    description: str
    category: str
    severity: str  # low, medium, high, critical
    location: str
    suggested_fix: str
    auto_repairable: bool
    detected_at: str
    resolved: bool = False
    placeholder_created: bool = False


class IssueDetector:
    """
    Comprehensive issue detection and flagging system

    Features:
    - Real-time code quality analysis
    - Performance monitoring
    - Configuration validation
    - Dependency checking
    - UI responsiveness monitoring
    - Automatic placeholder generation
    - Auto-repair suggestions
    """

    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.issues_db = {}
        self.placeholders_dir = self.project_root / "placeholders"
        self.placeholders_dir.mkdir(exist_ok=True)

        # Issue categories
        self.categories = {
            "code_quality": "Code Quality Issues",
            "performance": "Performance Issues",
            "configuration": "Configuration Problems",
            "dependencies": "Dependency Issues",
            "ui_responsiveness": "UI Responsiveness",
            "integration": "Integration Problems",
            "security": "Security Concerns",
            "documentation": "Documentation Issues",
        }

        # Severity levels
        self.severity_levels = {"low": 1, "medium": 2, "high": 3, "critical": 4}

        # Detection patterns
        self.detection_patterns = self._initialize_detection_patterns()

        # Performance baselines
        self.performance_baselines = {
            "memory_usage_mb": 500,  # MB
            "cpu_usage_percent": 80,  # %
            "ui_response_time_ms": 100,  # ms
            "file_load_time_ms": 50,  # ms
        }

        # Thread safety
        self.detection_lock = threading.Lock()

        # Initialize issue tracking
        self._initialize_issue_tracking()

    def _initialize_detection_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize detection patterns for various issue types"""
        return {
            "code_quality": [
                {
                    "pattern": r"TODO|FIXME|HACK|XXX",
                    "description": "Code contains TODO or FIXME comments",
                    "severity": "medium",
                    "auto_repairable": False,
                },
                {
                    "pattern": r"print\(",
                    "description": "Debug print statements found",
                    "severity": "low",
                    "auto_repairable": True,
                },
                {
                    "pattern": r"except\s*:",
                    "description": "Bare except clause found",
                    "severity": "high",
                    "auto_repairable": True,
                },
            ],
            "performance": [
                {
                    "pattern": r"time\.sleep\(",
                    "description": "Blocking sleep calls found",
                    "severity": "medium",
                    "auto_repairable": False,
                }
            ],
            "security": [
                {
                    "pattern": r"eval\(",
                    "description": "Unsafe eval() usage found",
                    "severity": "critical",
                    "auto_repairable": False,
                }
            ],
        }

    def _initialize_issue_tracking(self):
        """Initialize issue tracking system"""
        try:
            # Load existing issues if available
            issues_file = self.project_root / "issues_db.json"
            if issues_file.exists():
                with open(issues_file, "r") as f:
                    data = json.load(f)
                    for issue_data in data.get("issues", []):
                        issue = Issue(**issue_data)
                        self.issues_db[issue.id] = issue
        except Exception as e:
            print(f"Warning: Could not load existing issues: {e}")

    def scan_for_issues(self) -> List[Issue]:
        """Comprehensive issue scanning"""
        try:
            with self.detection_lock:
                issues = []

                # Code quality issues
                issues.extend(self._scan_code_quality())

                # Performance issues
                issues.extend(self._scan_performance())

                # Configuration issues
                issues.extend(self._scan_configuration())

                # Dependency issues
                issues.extend(self._scan_dependencies())

                # UI responsiveness issues
                issues.extend(self._scan_ui_responsiveness())

                # Integration issues
                issues.extend(self._scan_integration())

                # Update issues database
                for issue in issues:
                    self.issues_db[issue.id] = issue

                # Save issues to file
                self._save_issues_db()

                return issues

        except Exception as e:
            print(f"Error during issue scanning: {e}")
            return []

    def _scan_code_quality(self) -> List[Issue]:
        """Scan for code quality issues"""
        issues = []

        try:
            # Scan Python files
            for py_file in self.project_root.rglob("*.py"):
                if self._should_skip_file(py_file):
                    continue

                try:
                    with open(py_file, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Check for syntax errors
                    try:
                        ast.parse(content)
                    except SyntaxError as e:
                        issues.append(
                            Issue(
                                id=f"syntax_error_{py_file.name}_{int(time.time())}",
                                title=f"Syntax Error in {py_file.name}",
                                description=f"Syntax error at line {e.lineno}: {e.msg}",
                                category="code_quality",
                                severity="critical",
                                location=str(py_file),
                                suggested_fix="Fix syntax error and validate Python code",
                                auto_repairable=False,
                                detected_at=datetime.now().isoformat(),
                            )
                        )

                    # Check for code quality patterns
                    lines = content.split("\n")
                    for line_num, line in enumerate(lines, 1):
                        for pattern_info in self.detection_patterns["code_quality"]:
                            import re

                            if re.search(pattern_info["pattern"], line):
                                issues.append(
                                    Issue(
                                        id=f"code_quality_{py_file.name}_{line_num}_{int(time.time())}",
                                        title=f"Code Quality Issue in {py_file.name}",
                                        description=f"Line {line_num}: {pattern_info['description']}",
                                        category="code_quality",
                                        severity=pattern_info["severity"],
                                        location=f"{py_file}:{line_num}",
                                        suggested_fix=self._get_code_quality_fix(
                                            pattern_info["pattern"]
                                        ),
                                        auto_repairable=pattern_info["auto_repairable"],
                                        detected_at=datetime.now().isoformat(),
                                    )
                                )

                except Exception as e:
                    print(f"Error scanning {py_file}: {e}")

        except Exception as e:
            print(f"Error in code quality scan: {e}")

        return issues

    def _scan_performance(self) -> List[Issue]:
        """Scan for performance issues"""
        issues = []

        try:
            # Check system performance
            process = psutil.Process()

            # Memory usage
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024

            if memory_mb > self.performance_baselines["memory_usage_mb"]:
                issues.append(
                    Issue(
                        id=f"high_memory_usage_{int(time.time())}",
                        title="High Memory Usage Detected",
                        description=f"Application using {memory_mb:.1f}MB (baseline: {self.performance_baselines['memory_usage_mb']}MB)",
                        category="performance",
                        severity="medium"
                        if memory_mb
                        < self.performance_baselines["memory_usage_mb"] * 1.5
                        else "high",
                        location="Application Process",
                        suggested_fix="Optimize memory usage, check for memory leaks",
                        auto_repairable=False,
                        detected_at=datetime.now().isoformat(),
                    )
                )

            # CPU usage
            cpu_percent = process.cpu_percent()
            if cpu_percent > self.performance_baselines["cpu_usage_percent"]:
                issues.append(
                    Issue(
                        id=f"high_cpu_usage_{int(time.time())}",
                        title="High CPU Usage Detected",
                        description=f"Application using {cpu_percent:.1f}% CPU (baseline: {self.performance_baselines['cpu_usage_percent']}%)",
                        category="performance",
                        severity="medium" if cpu_percent < 90 else "high",
                        location="Application Process",
                        suggested_fix="Optimize CPU-intensive operations, check for infinite loops",
                        auto_repairable=False,
                        detected_at=datetime.now().isoformat(),
                    )
                )

        except Exception as e:
            print(f"Error in performance scan: {e}")

        return issues

    def _scan_configuration(self) -> List[Issue]:
        """Scan for configuration issues"""
        issues = []

        try:
            # Check for missing configuration files
            config_files = ["requirements.txt", "config.json", "settings.ini"]

            for config_file in config_files:
                config_path = self.project_root / config_file
                if not config_path.exists() and config_file == "requirements.txt":
                    issues.append(
                        Issue(
                            id=f"missing_config_{config_file}_{int(time.time())}",
                            title=f"Missing Configuration File: {config_file}",
                            description=f"Required configuration file {config_file} not found",
                            category="configuration",
                            severity="high"
                            if config_file == "requirements.txt"
                            else "medium",
                            location=str(config_path),
                            suggested_fix=f"Create {config_file} with appropriate configuration",
                            auto_repairable=True,
                            detected_at=datetime.now().isoformat(),
                        )
                    )

            # Validate requirements.txt if it exists
            req_file = self.project_root / "requirements.txt"
            if req_file.exists():
                try:
                    with open(req_file, "r") as f:
                        requirements = f.read().strip()

                    if not requirements:
                        issues.append(
                            Issue(
                                id=f"empty_requirements_{int(time.time())}",
                                title="Empty Requirements File",
                                description="requirements.txt exists but is empty",
                                category="configuration",
                                severity="medium",
                                location=str(req_file),
                                suggested_fix="Add required dependencies to requirements.txt",
                                auto_repairable=True,
                                detected_at=datetime.now().isoformat(),
                            )
                        )

                except Exception as e:
                    issues.append(
                        Issue(
                            id=f"invalid_requirements_{int(time.time())}",
                            title="Invalid Requirements File",
                            description=f"Cannot read requirements.txt: {e}",
                            category="configuration",
                            severity="high",
                            location=str(req_file),
                            suggested_fix="Fix requirements.txt format and encoding",
                            auto_repairable=False,
                            detected_at=datetime.now().isoformat(),
                        )
                    )

        except Exception as e:
            print(f"Error in configuration scan: {e}")

        return issues

    def _scan_dependencies(self) -> List[Issue]:
        """Scan for dependency issues"""
        issues = []

        try:
            # Check if required packages are installed
            required_packages = [
                "PyQt6",
                "PyQt-Fluent-Widgets",
                "watchdog",
                "psutil",
                "Pillow",
                "numpy",
            ]

            for package in required_packages:
                try:
                    __import__(package.replace("-", "_").lower())
                except ImportError:
                    issues.append(
                        Issue(
                            id=f"missing_dependency_{package}_{int(time.time())}",
                            title=f"Missing Dependency: {package}",
                            description=f"Required package {package} is not installed",
                            category="dependencies",
                            severity="critical"
                            if package in ["PyQt6", "PyQt-Fluent-Widgets"]
                            else "high",
                            location="Python Environment",
                            suggested_fix=f"Install {package} using: pip install {package}",
                            auto_repairable=True,
                            detected_at=datetime.now().isoformat(),
                        )
                    )

        except Exception as e:
            print(f"Error in dependency scan: {e}")

        return issues

    def _scan_ui_responsiveness(self) -> List[Issue]:
        """Scan for UI responsiveness issues"""
        issues = []

        try:
            # This would be implemented with actual UI performance monitoring
            # For now, create a placeholder for the monitoring system

            # Check for potential UI blocking operations
            for py_file in self.project_root.rglob("*.py"):
                if self._should_skip_file(py_file):
                    continue

                try:
                    with open(py_file, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Look for potentially blocking operations
                    blocking_patterns = [
                        r"requests\.get\(",
                        r"requests\.post\(",
                        r"urllib\.request\.",
                        r"time\.sleep\(",
                        r"input\(",
                        r"subprocess\.run\(",
                    ]

                    lines = content.split("\n")
                    for line_num, line in enumerate(lines, 1):
                        for pattern in blocking_patterns:
                            import re

                            if re.search(pattern, line) and "QThread" not in content:
                                issues.append(
                                    Issue(
                                        id=f"ui_blocking_{py_file.name}_{line_num}_{int(time.time())}",
                                        title=f"Potential UI Blocking Operation in {py_file.name}",
                                        description=f"Line {line_num}: Blocking operation may freeze UI",
                                        category="ui_responsiveness",
                                        severity="medium",
                                        location=f"{py_file}:{line_num}",
                                        suggested_fix="Move blocking operation to QThread or use async/await",
                                        auto_repairable=False,
                                        detected_at=datetime.now().isoformat(),
                                    )
                                )
                                break

                except Exception as e:
                    print(f"Error scanning {py_file} for UI issues: {e}")

        except Exception as e:
            print(f"Error in UI responsiveness scan: {e}")

        return issues

    def _scan_integration(self) -> List[Issue]:
        """Scan for integration issues"""
        issues = []

        try:
            # Check for RF4S integration points
            rf4s_indicators = [
                "RF4S",
                "RussianFishing4Script",
                "rf4s",
                "config_bridge",
                "process_bridge",
            ]

            integration_found = False

            for py_file in self.project_root.rglob("*.py"):
                if self._should_skip_file(py_file):
                    continue

                try:
                    with open(py_file, "r", encoding="utf-8") as f:
                        content = f.read()

                    for indicator in rf4s_indicators:
                        if indicator in content:
                            integration_found = True
                            break

                    if integration_found:
                        break

                except Exception as e:
                    print(f"Error scanning {py_file} for integration: {e}")

            if not integration_found:
                issues.append(
                    Issue(
                        id=f"missing_rf4s_integration_{int(time.time())}",
                        title="RF4S Integration Not Detected",
                        description="No RF4S integration code found in project",
                        category="integration",
                        severity="high",
                        location="Project Files",
                        suggested_fix="Implement RF4S communication bridges",
                        auto_repairable=False,
                        detected_at=datetime.now().isoformat(),
                    )
                )

        except Exception as e:
            print(f"Error in integration scan: {e}")

        return issues

    def flag_issue(self, issue: Issue):
        """Flag an issue with user notification"""
        try:
            # Add to issues database
            self.issues_db[issue.id] = issue

            # Create console notification
            severity_icon = {
                "low": "🟡",
                "medium": "🟠",
                "high": "🔴",
                "critical": "🚨",
            }.get(issue.severity, "⚪")

            print(f"\n{severity_icon} ISSUE DETECTED: {issue.title}")
            print(f"   Category: {issue.category}")
            print(f"   Severity: {issue.severity.upper()}")
            print(f"   Location: {issue.location}")
            print(f"   Description: {issue.description}")
            print(f"   Suggested Fix: {issue.suggested_fix}")

            if issue.auto_repairable:
                print(f"   🔧 Auto-repair available")

            print()

        except Exception as e:
            print(f"Error flagging issue: {e}")

    def create_placeholders(self, issues: List[Issue]):
        """Create placeholder files for unresolved issues"""
        try:
            for issue in issues:
                if not issue.resolved and not issue.placeholder_created:
                    placeholder_content = self._generate_placeholder_content(issue)
                    placeholder_file = self.placeholders_dir / f"{issue.id}.md"

                    with open(placeholder_file, "w", encoding="utf-8") as f:
                        f.write(placeholder_content)

                    # Mark placeholder as created
                    issue.placeholder_created = True
                    self.issues_db[issue.id] = issue

                    print(f"📝 Created placeholder for issue: {issue.title}")

            # Update placeholders index
            self._update_placeholders_index()

        except Exception as e:
            print(f"Error creating placeholders: {e}")

    def _generate_placeholder_content(self, issue: Issue) -> str:
        """Generate placeholder content for an issue"""
        return f"""# PLACEHOLDER: {issue.title}

## Issue Details
- **ID**: {issue.id}
- **Category**: {issue.category}
- **Severity**: {issue.severity.upper()}
- **Detected**: {issue.detected_at}
- **Location**: {issue.location}

## Description
{issue.description}

## Suggested Fix
{issue.suggested_fix}

## Status
- **Resolved**: {'✅ Yes' if issue.resolved else '❌ No'}
- **Auto-repairable**: {'✅ Yes' if issue.auto_repairable else '❌ No'}

## Action Required
{'This issue can be automatically repaired.' if issue.auto_repairable else 'Manual intervention required to resolve this issue.'}

## Resolution Steps
1. Review the issue description and location
2. Implement the suggested fix
3. Test the resolution
4. Mark the issue as resolved
5. Remove this placeholder

---
*This placeholder was automatically generated by RF4S Issue Detector*
*Generated on: {datetime.now().isoformat()}*
"""

    def _update_placeholders_index(self):
        """Update the placeholders index file"""
        try:
            unresolved_issues = [
                issue for issue in self.issues_db.values() if not issue.resolved
            ]

            content = f"""# RF4S UI Issues and Placeholders

## Summary
- **Total Issues**: {len(self.issues_db)}
- **Unresolved Issues**: {len(unresolved_issues)}
- **Last Updated**: {datetime.now().isoformat()}

## Unresolved Issues by Severity
"""

            # Group by severity
            by_severity = {}
            for issue in unresolved_issues:
                if issue.severity not in by_severity:
                    by_severity[issue.severity] = []
                by_severity[issue.severity].append(issue)

            # Sort by severity level
            for severity in ["critical", "high", "medium", "low"]:
                if severity in by_severity:
                    issues = by_severity[severity]
                    severity_icon = {
                        "low": "🟡",
                        "medium": "🟠",
                        "high": "🔴",
                        "critical": "🚨",
                    }[severity]
                    content += f"\n### {severity_icon} {severity.title()} ({len(issues)} issues)\n"

                    for issue in issues:
                        auto_repair = "🔧" if issue.auto_repairable else "🔨"
                        content += f"- {auto_repair} **[{issue.title}]({issue.id}.md)** - {issue.category}\n"

            content += f"""
## Categories
"""

            # Group by category
            by_category = {}
            for issue in unresolved_issues:
                if issue.category not in by_category:
                    by_category[issue.category] = []
                by_category[issue.category].append(issue)

            for category, issues in by_category.items():
                content += f"- **{self.categories.get(category, category)}**: {len(issues)} issues\n"

            content += f"""
## Auto-repair Available
{len([i for i in unresolved_issues if i.auto_repairable])} issues can be automatically repaired.

---
*Generated automatically by RF4S Issue Detector*
"""

            with open(self.placeholders_dir / "README.md", "w", encoding="utf-8") as f:
                f.write(content)

        except Exception as e:
            print(f"Error updating placeholders index: {e}")

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped during scanning"""
        skip_patterns = [
            "__pycache__",
            ".git",
            ".venv",
            "venv",
            "node_modules",
            ".pytest_cache",
            "build",
            "dist",
        ]

        return any(pattern in str(file_path) for pattern in skip_patterns)

    def _get_code_quality_fix(self, pattern: str) -> str:
        """Get suggested fix for code quality issues"""
        fixes = {
            r"TODO|FIXME|HACK|XXX": "Complete the TODO item or remove the comment",
            r"print\(": "Replace with proper logging using loguru or Python logging",
            r"except\s*:": "Specify exception type: except SpecificException:",
        }

        for fix_pattern, fix_text in fixes.items():
            import re

            if re.search(fix_pattern, pattern):
                return fix_text

        return "Review and fix the identified issue"

    def _save_issues_db(self):
        """Save issues database to file"""
        try:
            issues_data = {
                "last_updated": datetime.now().isoformat(),
                "total_issues": len(self.issues_db),
                "issues": [
                    {
                        "id": issue.id,
                        "title": issue.title,
                        "description": issue.description,
                        "category": issue.category,
                        "severity": issue.severity,
                        "location": issue.location,
                        "suggested_fix": issue.suggested_fix,
                        "auto_repairable": issue.auto_repairable,
                        "detected_at": issue.detected_at,
                        "resolved": issue.resolved,
                        "placeholder_created": issue.placeholder_created,
                    }
                    for issue in self.issues_db.values()
                ],
            }

            with open(self.project_root / "issues_db.json", "w") as f:
                json.dump(issues_data, f, indent=2)

        except Exception as e:
            print(f"Error saving issues database: {e}")

    def resolve_issue(self, issue_id: str) -> bool:
        """Mark an issue as resolved"""
        try:
            if issue_id in self.issues_db:
                self.issues_db[issue_id].resolved = True
                self._save_issues_db()

                # Remove placeholder if it exists
                placeholder_file = self.placeholders_dir / f"{issue_id}.md"
                if placeholder_file.exists():
                    placeholder_file.unlink()

                print(f"✅ Issue resolved: {self.issues_db[issue_id].title}")
                return True

            return False

        except Exception as e:
            print(f"Error resolving issue: {e}")
            return False

    def get_issue_summary(self) -> Dict[str, Any]:
        """Get summary of all issues"""
        try:
            unresolved = [i for i in self.issues_db.values() if not i.resolved]

            return {
                "total_issues": len(self.issues_db),
                "unresolved_issues": len(unresolved),
                "critical_issues": len(
                    [i for i in unresolved if i.severity == "critical"]
                ),
                "auto_repairable": len([i for i in unresolved if i.auto_repairable]),
                "categories": {
                    category: len([i for i in unresolved if i.category == category])
                    for category in self.categories.keys()
                },
                "last_scan": datetime.now().isoformat(),
            }

        except Exception as e:
            print(f"Error getting issue summary: {e}")
            return {}
