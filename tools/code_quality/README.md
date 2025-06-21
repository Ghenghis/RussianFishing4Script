# RF4S Complete Project Code Quality Tools

Comprehensive code quality tooling for the entire RF4S ecosystem upgrade, implementing industry-standard linting, formatting, and static analysis tools across all Python code in the project.

## Overview

This module provides automated code quality enforcement for the complete RF4S project upgrade, covering:
- **RF4S Core**: Original Russian Fishing 4 Script codebase
- **RF4S UI**: New PyQt6 + Fluent-Widgets desktop interface
- **Tools & Utilities**: Development tools, diagnostics, and maintenance scripts
- **Integration Layer**: Bridges, APIs, and communication systems

Ensures consistent code style, type safety, and maintainability across the entire RF4S ecosystem.

## Tools Included

### 🎨 **Black** - Code Formatting
- **Purpose**: Automatic code formatting for consistent style
- **Configuration**: 88 character line length, Python 3.9+ target
- **Usage**: `python -m black rf4s_ui/`

### 📦 **isort** - Import Sorting
- **Purpose**: Automatic import organization and sorting
- **Configuration**: Black-compatible profile with RF4S-specific settings
- **Usage**: `python -m isort rf4s_ui/`

### 🔍 **Flake8** - Style & Error Checking
- **Purpose**: PEP 8 compliance and error detection
- **Features**: PyQt-specific rules, docstring checking, import order validation
- **Usage**: `python -m flake8 rf4s_ui/`

### 🔬 **MyPy** - Type Checking
- **Purpose**: Static type analysis and validation
- **Features**: PyQt6 type stubs, strict type checking configuration
- **Usage**: `python -m mypy rf4s_ui/`

### 🔧 **Pylint** - Advanced Static Analysis
- **Purpose**: Advanced code analysis and quality metrics
- **Features**: Qt naming convention support, complexity analysis
- **Usage**: `python -m pylint rf4s_ui/`

### 🛡️ **Additional Security Tools**
- **Bandit**: Security vulnerability scanning
- **Safety**: Dependency vulnerability checking
- **Pre-commit**: Git hooks for automated quality checks

## Quick Start

### 1. Install Tools
```bash
cd C:\Users\Admin\RF4S-UI
python tools/code_quality/setup_tools.py
```

### 2. Run All Checks
```bash
python tools/code_quality/run_checks.py
```

### 3. Apply Automated Fixes
```bash
python tools/code_quality/auto_fix.py
```

## Configuration Files

### `pyproject.toml`
Central configuration for all tools with RF4S-specific settings:
- Black formatting rules
- isort import organization
- MyPy type checking configuration
- Pylint analysis settings

### `.flake8`
Flake8-specific configuration:
- PyQt compatibility rules
- Line length and style settings
- File exclusions and per-file ignores

### `requirements-dev.txt`
Development dependencies with pinned versions for reproducible builds.

## Automated Workflows

### Pre-commit Hooks
Automatically run quality checks before each commit:
```bash
# Setup (done automatically by setup_tools.py)
pre-commit install

# Manual run
pre-commit run --all-files
```

### Continuous Integration
The tools are designed to integrate with CI/CD pipelines:
- Exit codes indicate pass/fail status
- JSON reports for automated processing
- Detailed error reporting for debugging

## Usage Examples

### Format Code
```bash
# Check formatting (no changes)
python -m black --check rf4s_ui/

# Apply formatting
python -m black rf4s_ui/
```

### Check Imports
```bash
# Check import order (no changes)
python -m isort --check-only rf4s_ui/

# Fix import order
python -m isort rf4s_ui/
```

### Style Checking
```bash
# Basic style check
python -m flake8 rf4s_ui/

# With statistics
python -m flake8 --statistics rf4s_ui/
```

### Type Checking
```bash
# Full type check
python -m mypy rf4s_ui/

# Specific module
python -m mypy rf4s_ui/core/
```

### Advanced Analysis
```bash
# Pylint with score
python -m pylint rf4s_ui/

# JSON output for automation
python -m pylint --output-format=json rf4s_ui/
```

## RF4S-Specific Configurations

### PyQt6 Integration
- Type stubs for PyQt6 components
- Qt naming convention allowances
- Signal/slot pattern recognition

### Modular Architecture Support
- 200-line file limit enforcement
- Component isolation validation
- Dependency analysis

### Performance Considerations
- Optimized for large codebases
- Parallel execution where possible
- Incremental checking support

## Quality Metrics

The tools enforce the following quality standards:

### Code Style
- ✅ PEP 8 compliance
- ✅ Consistent formatting
- ✅ Organized imports
- ✅ Proper docstrings

### Type Safety
- ✅ Full type annotations
- ✅ Type consistency checking
- ✅ Generic type usage
- ✅ Optional type handling

### Code Quality
- ✅ Complexity analysis
- ✅ Security vulnerability scanning
- ✅ Dependency safety checking
- ✅ Performance pattern analysis

## Integration with RF4S UI Architecture

### Service Registry Integration
The code quality tools respect the RF4S UI modular architecture:
- Component isolation validation
- Service dependency analysis
- Interface compliance checking

### Documentation Generation
Quality metrics are integrated with the documentation system:
- Automated quality reports
- Code coverage integration
- Architecture compliance validation

## Troubleshooting

### Common Issues

**Tool Not Found**
```bash
# Reinstall development dependencies
pip install -r tools/code_quality/requirements-dev.txt
```

**Configuration Conflicts**
```bash
# Reset to default configurations
python tools/code_quality/setup_tools.py
```

**PyQt Type Issues**
```bash
# Install PyQt6 type stubs
pip install types-PyQt6
```

### Getting Help

1. Check tool-specific documentation
2. Review configuration files for custom settings
3. Run individual tools with `--help` flag
4. Check the RF4S UI documentation for architecture-specific guidance

## Contributing

When contributing to RF4S UI:

1. **Always run quality checks** before committing
2. **Fix all automated issues** using the auto_fix.py script
3. **Address type checking errors** manually
4. **Maintain the 200-line file limit** enforced by the tools
5. **Follow the modular architecture** validated by the quality system

## Branch Strategy

This code quality system is part of the RF4S-UI upgrade branch strategy:
- Maintains compatibility with main RF4S repository
- Provides enhanced development workflow
- Ensures production-ready code quality
- Supports non-invasive integration approach

---

**RF4S UI Code Quality Tools** - Ensuring excellence in the RF4S ecosystem upgrade.