# Test Suite for Mergington High School API

This directory contains comprehensive tests for the FastAPI application that manages student activity registrations.

## Test Structure

- **`conftest.py`**: Test configuration and fixtures
- **`test_api.py`**: Core API endpoint tests
- **`test_integration.py`**: Integration and workflow tests

## Running Tests

### Basic Test Run
```bash
pytest tests/ -v
```

### Run Tests with Coverage
```bash
pytest tests/ --cov=src --cov-report=term-missing
```

### Run Specific Test Files
```bash
pytest tests/test_api.py -v
pytest tests/test_integration.py -v
```

### Run Specific Test Classes
```bash
pytest tests/test_api.py::TestSignupEndpoint -v
pytest tests/test_integration.py::TestCompleteWorkflow -v
```

## Test Coverage

The test suite covers:

- ✅ **Basic API endpoints** (GET /activities, POST /signup, DELETE /unregister)
- ✅ **Error handling** (404s, 400s, validation errors)
- ✅ **Data consistency** (signup/unregister persistence)
- ✅ **Edge cases** (special characters, URL encoding, empty parameters)
- ✅ **Complete workflows** (full signup/unregister cycles)
- ✅ **Capacity management** (max participant limits)
- ✅ **Concurrent operations** (multiple students, multiple activities)

## Dependencies

The tests require:
- `pytest`: Testing framework
- `httpx`: HTTP client for testing FastAPI
- `pytest-cov`: Coverage reporting

## Test Data

Tests use fixtures to:
- Reset activity data between tests
- Provide clean test environments
- Ensure test isolation
- Create sample data as needed

## Coverage Report

Current coverage: **100%** of application code