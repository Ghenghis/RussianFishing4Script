#!/usr/bin/env python3
"""
RF4S UI Code Quality Tools Setup
Automated setup and configuration for all code quality tools
"""

import subprocess
import sys
import os
from pathlib import Path


class CodeQualitySetup:
    """Setup and configure all code quality tools for RF4S UI"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.tools_dir = Path(__file__).parent
        
    def install_tools(self):
        """Install all development dependencies"""
        print("Installing code quality tools...")
        
        req_file = self.tools_dir / "requirements-dev.txt"
        cmd = [sys.executable, "-m", "pip", "install", "-r", str(req_file)]
        
        try:
            subprocess.run(cmd, check=True, cwd=self.project_root)
            print("✓ All code quality tools installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install tools: {e}")
            return False
        return True
    
    def setup_pre_commit(self):
        """Setup pre-commit hooks"""
        print("Setting up pre-commit hooks...")
        
        # Create pre-commit config
        pre_commit_config = self.project_root / ".pre-commit-config.yaml"
        config_content = """
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        additional_dependencies: [flake8-docstrings, flake8-import-order, flake8-bugbear]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-PyQt6]
"""
        
        with open(pre_commit_config, 'w') as f:
            f.write(config_content.strip())
        
        # Install pre-commit hooks
        try:
            subprocess.run([sys.executable, "-m", "pre_commit", "install"], 
                         check=True, cwd=self.project_root)
            print("✓ Pre-commit hooks installed")
        except subprocess.CalledProcessError:
            print("ℹ Pre-commit installation skipped (optional)")
        
    def copy_configs(self):
        """Copy configuration files to project root"""
        print("Copying configuration files...")
        
        configs = [
            ("pyproject.toml", self.project_root / "pyproject.toml"),
            (".flake8", self.project_root / ".flake8")
        ]
        
        for src_name, dst_path in configs:
            src_path = self.tools_dir / src_name
            try:
                import shutil
                shutil.copy2(src_path, dst_path)
                print(f"✓ Copied {src_name}")
            except Exception as e:
                print(f"✗ Failed to copy {src_name}: {e}")
    
    def run_initial_checks(self):
        """Run initial code quality checks"""
        print("\nRunning initial code quality checks...")
        
        rf4s_ui_path = self.project_root / "rf4s_ui"
        
        checks = [
            ("Black formatting", [sys.executable, "-m", "black", "--check", str(rf4s_ui_path)]),
            ("isort imports", [sys.executable, "-m", "isort", "--check-only", str(rf4s_ui_path)]),
            ("Flake8 linting", [sys.executable, "-m", "flake8", str(rf4s_ui_path)]),
            ("MyPy type checking", [sys.executable, "-m", "mypy", str(rf4s_ui_path)]),
        ]
        
        results = {}
        for name, cmd in checks:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
                if result.returncode == 0:
                    print(f"✓ {name}: PASSED")
                    results[name] = "PASSED"
                else:
                    print(f"✗ {name}: ISSUES FOUND")
                    results[name] = "ISSUES"
                    if result.stdout:
                        print(f"  Output: {result.stdout[:200]}...")
            except FileNotFoundError:
                print(f"⚠ {name}: TOOL NOT FOUND")
                results[name] = "NOT_FOUND"
        
        return results
    
    def setup_all(self):
        """Run complete setup process"""
        print("=== RF4S UI Code Quality Tools Setup ===\n")
        
        # Install tools
        if not self.install_tools():
            return False
        
        # Copy configs
        self.copy_configs()
        
        # Setup pre-commit
        self.setup_pre_commit()
        
        # Run initial checks
        results = self.run_initial_checks()
        
        print("\n=== Setup Complete ===")
        print("Available commands:")
        print("  Format code:     python -m black rf4s_ui/")
        print("  Sort imports:    python -m isort rf4s_ui/")
        print("  Check style:     python -m flake8 rf4s_ui/")
        print("  Type check:      python -m mypy rf4s_ui/")
        print("  Run all checks:  python tools/code_quality/run_checks.py")
        
        return True


if __name__ == "__main__":
    setup = CodeQualitySetup()
    success = setup.setup_all()
    sys.exit(0 if success else 1)