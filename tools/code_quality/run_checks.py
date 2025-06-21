#!/usr/bin/env python3
"""
RF4S UI Code Quality Check Runner
Automated execution of all code quality tools with detailed reporting
"""

import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple, Any
import json


class CodeQualityRunner:
    """Run all code quality checks and generate comprehensive reports"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        # Cover entire codebase - this is a complete RF4S ecosystem upgrade
        self.target_paths = [
            self.project_root / "rf4s",           # Original RF4S core
            self.project_root / "rf4s_ui",        # New UI components
            self.project_root / "tools",          # Development tools
            self.project_root / "dev-tools",      # Additional dev utilities
        ]
        # Filter to only existing directories with Python files
        self.target_paths = [p for p in self.target_paths if p.exists() and list(p.rglob("*.py"))]
        self.results = {}
        
    def run_black_check(self) -> Dict[str, Any]:
        """Run Black formatting check on entire codebase"""
        print("Running Black formatting check on entire RF4S codebase...")
        
        cmd = [sys.executable, "-m", "black", "--check", "--diff"] + [str(p) for p in self.target_paths]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', cwd=self.project_root)
        
        total_files = sum(len(list(p.rglob("*.py"))) for p in self.target_paths)
        
        return {
            "tool": "black",
            "passed": result.returncode == 0,
            "output": result.stdout,
            "errors": result.stderr,
            "files_checked": total_files,
            "directories_scanned": [str(p.name) for p in self.target_paths]
        }
    
    def run_isort_check(self) -> Dict[str, Any]:
        """Run isort import sorting check on entire codebase"""
        print("Running isort import sorting check on entire RF4S codebase...")
        
        cmd = [sys.executable, "-m", "isort", "--check-only", "--diff"] + [str(p) for p in self.target_paths]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', cwd=self.project_root)
        
        total_files = sum(len(list(p.rglob("*.py"))) for p in self.target_paths)
        
        return {
            "tool": "isort",
            "passed": result.returncode == 0,
            "output": result.stdout,
            "errors": result.stderr,
            "files_checked": total_files,
            "directories_scanned": [str(p.name) for p in self.target_paths]
        }
    
    def run_flake8_check(self) -> Dict[str, Any]:
        """Run Flake8 style and error checking on entire codebase"""
        print("Running Flake8 style and error checking on entire RF4S codebase...")
        
        cmd = [sys.executable, "-m", "flake8", "--statistics"] + [str(p) for p in self.target_paths]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', cwd=self.project_root)
        
        # Parse flake8 output for detailed reporting
        issues = []
        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                if ':' in line and not line.startswith(' '):
                    issues.append(line)
        
        return {
            "tool": "flake8",
            "passed": result.returncode == 0,
            "output": result.stdout,
            "errors": result.stderr,
            "issues_count": len(issues),
            "issues": issues[:10],  # First 10 issues for summary
            "directories_scanned": [str(p.name) for p in self.target_paths]
        }
    
    def run_mypy_check(self) -> Dict[str, Any]:
        """Run MyPy type checking on entire codebase"""
        print("Running MyPy type checking on entire RF4S codebase...")
        
        cmd = [sys.executable, "-m", "mypy"] + [str(p) for p in self.target_paths]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', cwd=self.project_root)
        
        # Parse mypy output
        errors = []
        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                if 'error:' in line or 'warning:' in line:
                    errors.append(line)
        
        return {
            "tool": "mypy",
            "passed": result.returncode == 0,
            "output": result.stdout,
            "errors": result.stderr,
            "type_errors": len(errors),
            "error_details": errors[:10],  # First 10 errors for summary
            "directories_scanned": [str(p.name) for p in self.target_paths]
        }
    
    def run_pylint_check(self) -> Dict[str, Any]:
        """Run Pylint advanced static analysis on entire codebase"""
        print("Running Pylint advanced static analysis on entire RF4S codebase...")
        
        cmd = [sys.executable, "-m", "pylint"] + [str(p) for p in self.target_paths] + ["--output-format=json"]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', cwd=self.project_root)
        
        # Parse pylint JSON output
        issues = []
        score = 0.0
        
        try:
            if result.stdout:
                pylint_data = json.loads(result.stdout)
                if isinstance(pylint_data, list):
                    issues = pylint_data
        except json.JSONDecodeError:
            # Fallback to text parsing if JSON fails
            pass
        
        # Extract score from stderr (pylint puts score there)
        if result.stderr:
            for line in result.stderr.split('\n'):
                if 'Your code has been rated at' in line:
                    try:
                        score = float(line.split('rated at ')[1].split('/')[0])
                    except (IndexError, ValueError):
                        pass
        
        return {
            "tool": "pylint",
            "passed": len(issues) == 0,
            "output": result.stdout,
            "errors": result.stderr,
            "score": score,
            "issues_count": len(issues),
            "issues": issues[:5] if issues else []  # First 5 issues for summary
        }
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all code quality checks"""
        print("=== RF4S UI Code Quality Checks ===\n")
        
        start_time = time.time()
        
        # Run all checks
        checks = [
            self.run_black_check,
            self.run_isort_check,
            self.run_flake8_check,
            self.run_mypy_check,
            self.run_pylint_check
        ]
        
        results = {}
        for check_func in checks:
            try:
                result = check_func()
                results[result["tool"]] = result
                
                # Print immediate feedback
                status = "✓ PASSED" if result["passed"] else "✗ ISSUES FOUND"
                print(f"{result['tool'].upper():>8}: {status}")
                
            except Exception as e:
                print(f"ERROR running {check_func.__name__}: {e}")
                results[check_func.__name__] = {
                    "tool": check_func.__name__,
                    "passed": False,
                    "error": str(e)
                }
        
        end_time = time.time()
        
        # Generate summary
        summary = self._generate_summary(results, end_time - start_time)
        
        return {
            "summary": summary,
            "results": results,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration": end_time - start_time
        }
    
    def _generate_summary(self, results: Dict[str, Any], duration: float) -> Dict[str, Any]:
        """Generate comprehensive summary of all checks"""
        total_checks = len(results)
        passed_checks = sum(1 for r in results.values() if r.get("passed", False))
        
        # Calculate overall score
        overall_score = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
        
        # Collect all issues
        total_issues = 0
        critical_issues = []
        
        for tool, result in results.items():
            if not result.get("passed", False):
                issues_count = result.get("issues_count", result.get("type_errors", 0))
                total_issues += issues_count
                
                if tool == "mypy" and result.get("type_errors", 0) > 0:
                    critical_issues.extend(result.get("error_details", [])[:3])
                elif tool == "flake8" and result.get("issues_count", 0) > 0:
                    critical_issues.extend(result.get("issues", [])[:3])
        
        return {
            "overall_score": overall_score,
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": total_checks - passed_checks,
            "total_issues": total_issues,
            "critical_issues": critical_issues[:5],  # Top 5 critical issues
            "duration": duration,
            "status": "PASSED" if passed_checks == total_checks else "ISSUES_FOUND"
        }
    
    def print_detailed_report(self, results: Dict[str, Any]):
        """Print detailed report of all checks"""
        print("\n" + "="*60)
        print("DETAILED CODE QUALITY REPORT")
        print("="*60)
        
        summary = results["summary"]
        print(f"Overall Score: {summary['overall_score']:.1f}%")
        print(f"Checks Passed: {summary['passed_checks']}/{summary['total_checks']}")
        print(f"Total Issues: {summary['total_issues']}")
        print(f"Duration: {summary['duration']:.2f}s")
        print(f"Status: {summary['status']}")
        
        if summary["critical_issues"]:
            print(f"\nTop Critical Issues:")
            for i, issue in enumerate(summary["critical_issues"], 1):
                print(f"  {i}. {issue}")
        
        print("\n" + "-"*60)
        print("TOOL-SPECIFIC RESULTS:")
        print("-"*60)
        
        for tool, result in results["results"].items():
            status = "✓ PASSED" if result.get("passed", False) else "✗ FAILED"
            print(f"\n{tool.upper()} {status}")
            
            if not result.get("passed", False):
                if tool == "pylint" and "score" in result:
                    print(f"  Score: {result['score']}/10.0")
                
                if result.get("issues_count", 0) > 0:
                    print(f"  Issues: {result['issues_count']}")
                
                if result.get("type_errors", 0) > 0:
                    print(f"  Type Errors: {result['type_errors']}")
        
        print("\n" + "="*60)
    
    def save_report(self, results: Dict[str, Any], filename: str = None):
        """Save detailed report to file"""
        if filename is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"code_quality_report_{timestamp}.json"
        
        report_path = self.project_root / "tools" / "code_quality" / filename
        
        with open(report_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nDetailed report saved to: {report_path}")


def main():
    """Main entry point for code quality checks"""
    runner = CodeQualityRunner()
    
    # Run all checks
    results = runner.run_all_checks()
    
    # Print detailed report
    runner.print_detailed_report(results)
    
    # Save report
    runner.save_report(results)
    
    # Exit with appropriate code
    summary = results["summary"]
    if summary["status"] == "PASSED":
        print(f"\n🎉 All code quality checks PASSED! Score: {summary['overall_score']:.1f}%")
        sys.exit(0)
    else:
        print(f"\n⚠️  Code quality issues found. Score: {summary['overall_score']:.1f}%")
        print("Run individual tools to fix issues:")
        print("  python -m black rf4s_ui/")
        print("  python -m isort rf4s_ui/")
        sys.exit(1)


if __name__ == "__main__":
    main()