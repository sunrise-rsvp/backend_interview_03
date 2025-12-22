# Integration Tests Documentation

This directory contains end-to-end integration tests using Playwright for the Event Management API.

## Overview

The test suite covers:
- **Event CRUD Operations**: Complete Create, Read, Update, Delete functionality
- **Ticket Management**: Ticket creation, purchase workflows (framework ready)
- **Caching Integration**: Redis caching behavior and performance
- **Background Tasks**: Celery task processing and async workflows
- **System Integration**: Full application stack testing

## Test Structure

```
tests/
├── conftest.py                          # Test configuration and fixtures
├── test_events_integration.py           # Event CRUD and workflow tests
├── test_tickets_integration.py          # Ticket system tests (framework)
├── test_caching_integration.py          # Cache functionality tests  
├── test_background_tasks_integration.py # Background processing tests
└── README.md                           # This documentation
```

## Requirements

### System Dependencies
- Python 3.10+
- PostgreSQL (with test database)
- Redis Server
- Node.js (for Playwright)

### Python Dependencies
```bash
pip install -r requirements.txt
python -m playwright install chromium
```

## Running Tests

### Quick Start
```bash
# Install and run all integration tests
python run_tests.py

# Install Playwright browsers only
python run_tests.py --install-playwright

# Set up test environment and keep it running
python run_tests.py --setup-only
```

### Test Categories

#### Integration Tests (Default)
```bash
# All integration tests with full stack
python run_tests.py --integration-only

# With verbose output
python run_tests.py --verbose

# Run tests in parallel (if pytest-xdist installed)
python run_tests.py --parallel
```

#### Unit Tests Only
```bash
python run_tests.py --unit-only
```

#### Specific Test Suites
```bash
# Event functionality
python run_tests.py --suite events

# Ticket functionality
python run_tests.py --suite tickets

# Caching functionality  
python run_tests.py --suite cache

# Background tasks
python run_tests.py --suite background
```

#### Filter Tests
```bash
# Run specific test patterns
python run_tests.py --filter "test_create_event"
python run_tests.py --filter "CRUD"
python run_tests.py --filter "cache"
```

### Direct Pytest Usage
```bash
# All integration tests
pytest tests/ -m integration

# Specific test file
pytest tests/test_events_integration.py -v

# Exclude slow tests
pytest tests/ -m "integration and not slow"

# Cache tests only
pytest tests/ -m "integration and cache"
```

## Test Configuration

### Environment Variables
The test suite automatically configures:
- `DATABASE_URL`: Test database connection
- `REDIS_URL`: Redis connection for caching tests
- `ENVIRONMENT`: Set to "test"

### Test Database
- Database: `test_events_db`
- Automatically created and migrated
- Cleaned between test runs

### Test Server
- URL: `http://localhost:8000`
- Automatically started and stopped
- Health check verification

## Test Categories & Markers

### Markers
- `@pytest.mark.integration`: Full integration tests
- `@pytest.mark.crud`: CRUD operation tests  
- `@pytest.mark.cache`: Caching functionality tests
- `@pytest.mark.slow`: Long-running tests
- `@pytest.mark.unit`: Unit tests (non-integration)

### Test Classes

#### TestEventsCRUDIntegration
- Basic CRUD operations for events
- Input validation testing
- Error handling scenarios

#### TestEventWorkflowIntegration
- Complete event lifecycle testing
- Bulk operations
- Complex workflows

#### TestEventCachingIntegration  
- Cache behavior verification
- Cache invalidation testing
- Performance improvements

#### TestTicketsCRUDIntegration
- Ticket management (framework ready)
- Purchase workflow testing
- Business rule validation

#### TestBackgroundTasksIntegration
- Celery task processing
- Asynchronous workflows
- Task failure handling

## Sample Test Data

Tests use predefined sample data:
- `sample_event_data`: Single event for basic tests
- `sample_event_data_list`: Multiple events for bulk operations
- `sample_ticket_data`: Ticket information (when implemented)

## Common Test Patterns

### API Testing Pattern
```python
async def test_api_operation(self, server_process, api_client, sample_data):
    async with api_client.AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.post("/events/", json=sample_data)
        assert response.status_code == 200
        # Additional assertions...
```

### Cache Testing Pattern
```python
async def test_cache_behavior(self, server_process, api_client):
    # Setup Redis connection
    redis_client = redis.from_url("redis://localhost:6379")
    
    # Perform operation
    # Verify cache state
    # Clean up
```

### Background Task Pattern
```python
async def test_background_task(self, server_process):
    with patch('celery_worker.task_name.delay') as mock_task:
        # Trigger operation
        # Verify task was called
        # Check task parameters
```

## Troubleshooting

### Common Issues

#### Database Connection
```bash
# Check PostgreSQL is running
psql -h localhost -p 5432 -U postgres -l

# Create test database manually
createdb -h localhost -p 5432 -U postgres test_events_db
```

#### Redis Connection
```bash
# Check Redis is running
redis-cli ping

# Start Redis server
redis-server
```

#### Playwright Issues
```bash
# Reinstall browsers
python -m playwright install --force

# Check browser installation
python -m playwright install --help
```

#### Port Conflicts
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill process using port
kill -9 <PID>
```

### Debug Mode
```bash
# Run with maximum verbosity
python run_tests.py --verbose -s

# Keep test environment running for debugging
python run_tests.py --setup-only
```

### Performance Issues
```bash
# Run fewer tests
python run_tests.py --filter "not slow"

# Skip cache tests if Redis issues
pytest tests/ -m "integration and not cache"
```

## Integration with CI/CD

### GitHub Actions Example
```yaml
name: Integration Tests
on: [push, pull_request]
jobs:
  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: password
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:6
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.10
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          python -m playwright install chromium
      - name: Run integration tests
        run: python run_tests.py --integration-only
```

## Contributing

When adding new tests:
1. Follow existing test patterns
2. Use appropriate markers (`@pytest.mark.integration`, etc.)
3. Add proper fixtures and cleanup
4. Update this documentation
5. Ensure tests are deterministic and isolated

## Coverage

To run with coverage reporting:
```bash
pip install pytest-cov
pytest tests/ --cov=. --cov-report=html --cov-report=term-missing
```

## Performance Benchmarking

Some tests include basic performance verification:
- Response time measurements
- Cache hit/miss ratios
- Concurrent request handling

For detailed performance testing, consider using tools like:
- `locust` for load testing
- `pytest-benchmark` for micro-benchmarks
- Application Performance Monitoring (APM) tools
