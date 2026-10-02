# Tests

This directory contains unit tests, integration tests, and test fixtures for the Space Debris Tracker project.

## Overview

The test suite ensures reliability and correctness of:
* Flask API endpoints
* Data processing functions
* Orbital mechanics calculations (SGP4/SDP4)
* ML model predictions
* Frontend-backend integration

## Test Structure

```
tests/
├── unit/                      # Unit tests for individual functions
│   ├── test_orbital_math.py   # SGP4 propagation tests
│   ├── test_data_parsing.py   # TLE and SATCAT parsing
│   ├── test_risk_model.py     # ML model inference
│   └── test_filters.py        # Object filtering logic
│
├── integration/               # Integration tests
│   ├── test_api_routes.py     # Flask endpoint tests
│   ├── test_data_pipeline.py  # End-to-end data flow
│   └── test_frontend.py       # Frontend API integration
│
├── fixtures/                  # Test data
│   ├── sample_tle.txt         # Sample TLE data
│   ├── test_satcat.csv        # Test satellite catalog
│   └── expected_outputs.json  # Expected test results
│
└── README.md                  # This file
```

## Running Tests

### Prerequisites

Install test dependencies:
```bash
pip install -r requirements.txt
pip install pytest pytest-cov pytest-flask
```

### Run All Tests

```bash
# From project root
pytest tests/

# With coverage report
pytest tests/ --cov=webapp --cov-report=html
```

### Run Specific Test Suites

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Specific test file
pytest tests/unit/test_orbital_math.py

# Specific test function
pytest tests/unit/test_orbital_math.py::test_sgp4_propagation
```

## Test Coverage Goals

Target coverage by component:
* **Orbital mechanics** - 95%+
* **Data parsing** - 90%+
* **Flask API** - 85%+
* **ML model** - 80%+
* **Utilities** - 75%+

## Writing New Tests

### Example Unit Test

```python
# tests/unit/test_orbital_math.py
import pytest
from webapp.orbital import compute_position

def test_sgp4_propagation():
    """Test SGP4 algorithm with known ISS TLE"""
    tle_line1 = "1 25544U 98067A   24001.50000000  .00016717  00000-0  30000-3 0  9995"
    tle_line2 = "2 25544  51.6400 208.9163 0002602  74.0123 286.1267 15.50574518123456"
    
    position = compute_position(tle_line1, tle_line2, "2024-01-01 12:00:00")
    
    assert -7000 < position['x'] < 7000  # km from Earth center
    assert -7000 < position['y'] < 7000
    assert -7000 < position['z'] < 7000
    assert position['altitude'] > 400  # ISS altitude > 400 km
    assert position['altitude'] < 450  # ISS altitude < 450 km
```

### Example Integration Test

```python
# tests/integration/test_api_routes.py
import pytest
from webapp.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_get_satellite_positions(client):
    """Test /api/positions endpoint"""
    response = client.get('/api/positions')
    assert response.status_code == 200
    
    data = response.get_json()
    assert 'satellites' in data
    assert len(data['satellites']) > 0
    assert 'lat' in data['satellites'][0]
    assert 'lon' in data['satellites'][0]
    assert 'alt' in data['satellites'][0]
```

## Continuous Integration

Tests are automatically run on:
* Every commit (pre-commit hook)
* Every pull request (GitHub Actions)
* Scheduled nightly builds

## Test Data

Test fixtures use:
* **Sample TLE data** - 50 representative objects across all orbital regimes
* **Historical data** - Known orbital positions for validation
* **Edge cases** - Highly elliptical orbits, decayed objects, invalid TLE

## Known Limitations

* Frontend JavaScript tests not yet implemented (TODO)
* Performance/load tests not included in this suite
* ML model training tests require GPU (run separately)

## Contributing

When adding new features:
1. Write tests BEFORE implementation (TDD)
2. Ensure tests pass locally before committing
3. Maintain or improve code coverage
4. Update this README if adding new test categories
