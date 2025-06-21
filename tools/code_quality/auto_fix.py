#!/usr/bin/env python3
"""
RF4S UI Automated Code Quality Fixes
Automatically applies formatting and import sorting fixes
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any


class AutoFixer:
    """Automated code quality fixes for RF4S UI"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        # Cover entire RF4S ecosystem - this is a complete upgrade branch
        self.target_paths = [
            self.project_root / "rf4s",           # Original RF4S core
            self.project_root / "rf4s_ui",        # New UI components
            self.project_root / "tools",          # Development tools
            self.project_root / "dev-tools",      # Additional dev utilities
        ]
        # Filter to only existing directories with Python files
        self.target_paths = [p for p in self.target_paths if p.exists() and list(p.rglob("*.py"))]
        
    def run_black_format(self) -> Dict[str, Any]:
        """Apply Black code formatting to entire RF4S codebase"""
        print("Applying Black code formatting to entire RF4S codebase...")
        
        cmd = [sys.executable, "-m", "black"] + [str(p) for p in self.target_paths]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', cwd=self.project_root)
        
        total_files = sum(len(list(p.rglob("*.py"))) for p in self.target_paths)
        
        return {
            "tool": "black",
            "success": result.returncode == 0,
            "output": result.stdout,
            "errors": result.stderr,
            "files_processed": total_files,
            "directories_processed": [str(p.name) for p in self.target_paths]
        }
    
    def run_isort_fix(self) -> Dict[str, Any]:
        """Apply isort import sorting to entire RF4S codebase"""
        print("Applying isort import sorting to entire RF4S codebase...")
        
        cmd = [sys.executable, "-m", "isort"] + [str(p) for p in self.target_paths]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', cwd=self.project_root)
        
        total_files = sum(len(list(p.rglob("*.py"))) for p in self.target_paths)
        
        return {
            "tool": "isort",
            "success": result.returncode == 0,
            "output": result.stdout,
            "errors": result.stderr,
            "files_processed": total_files,
            "directories_processed": [str(p.name) for p in self.target_paths]
        }
    
    def fix_all(self) -> Dict[str, Any]:
        """Apply all automated fixes"""
        print("=== RF4S UI Automated Code Quality Fixes ===\n")
        
        results = {}
        
        # Apply Black formatting
        black_result = self.run_black_format()
        results["black"] = black_result
        status = "✓ SUCCESS" if black_result["success"] else "✗ FAILED"
        print(f"Black formatting: {status}")
        
        # Apply isort import sorting
        isort_result = self.run_isort_fix()
        results["isort"] = isort_result
        status = "✓ SUCCESS" if isort_result["success"] else "✗ FAILED"
        print(f"Import sorting: {status}")
        
        # Summary
        total_fixes = len(results)
        successful_fixes = sum(1 for r in results.values() if r["success"])
        
        print(f"\nFixes applied: {successful_fixes}/{total_fixes}")
        
        if successful_fixes == total_fixes:
            print("🎉 All automated fixes applied successfully!")
            print("Run 'python tools/code_quality/run_checks.py' to verify.")
        else:
            print("⚠️  Some fixes failed. Check error messages above.")
        
        return {
            "results": results,
            "total_fixes": total_fixes,
            "successful_fixes": successful_fixes,
            "all_successful": successful_fixes == total_fixes
        }


def main():
    """Main entry point for automated fixes"""
    fixer = AutoFixer()
    results = fixer.fix_all()
    
    sys.exit(0 if results["all_successful"] else 1)


if __name__ == "__main__":
    main()