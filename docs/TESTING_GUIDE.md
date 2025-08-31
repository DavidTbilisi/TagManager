# TagManager Tests

This directory contains unit tests for the TagManager project.

## Running Tests

### Method 1: Using the test runner

```bash
python3 run_tests.py
```

### Method 2: Using unittest directly

```bash
python3 -m unittest discover tests -v
```

### Method 3: Using pytest (if installed)

```bash
pip install pytest
pytest tests/
```

## Test Files

- `test_basic.py` - Basic functionality tests that don't require full module imports
- `test_tagmanager.py` - Comprehensive tests for TagManager functionality (requires dependencies)

## Test Structure

The tests are organized into several categories:

### Basic Functionality Tests

- File operations
- JSON data handling
- Tag data structure operations
- Search simulation
- Project structure validation

### TagManager Integration Tests

- Add/remove tags functionality
- Search operations
- Configuration management
- File validation

## Dependencies

Basic tests run without additional dependencies. Full integration tests require:

- typer
- rich

Install test dependencies:

```bash
pip install -e ".[test]"
```

## Coverage

To run tests with coverage:

```bash
pip install pytest-cov
pytest --cov=tagmanager tests/
```
