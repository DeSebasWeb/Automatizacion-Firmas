# Database Infrastructure Tests

Unit tests for the database infrastructure layer (Repository Pattern implementation).

## Test Files

### `test_exceptions.py`
Tests for domain exceptions:
- `DomainException` base class
- `RepositoryError` and subclasses
- `UserNotFoundError`
- `DuplicateEmailError`
- `InvalidCredentialsError`
- Exception hierarchy relationships

**Coverage:** 100% of domain exceptions

### `test_user_mapper.py`
Tests for UserMapper (Domain ↔ Persistence translation):
- `to_domain()` - Database model → Domain entity
- `to_persistence()` - Domain entity → Database model
- `update_db_from_domain()` - In-place update of DB model
- Round-trip conversions (data integrity)
- Value Object conversions
- Immutability enforcement (ID, created_at)

**Coverage:** 30+ test cases covering all mapper methods

### `test_user_repository.py`
Tests for UserRepository (SQLAlchemy adapter):
- `create()` - Create new user with duplicate detection
- `find_by_id()` - Query by UserId
- `find_by_email()` - Query by Email
- `update()` - Update with UserNotFoundError handling
- `delete()` - Delete with boolean return
- `exists_by_email()` - Efficient EXISTS query
- `list_all()` - Pagination support
- `count()` - Total user count
- Exception handling (domain vs infrastructure exceptions)
- SQLAlchemy error conversion

**Coverage:** 40+ test cases with mocked SQLAlchemy session

## Running Tests

### Install Dependencies
```bash
pip install pytest pytest-cov
```

### Run All Tests
```bash
# Run all repository pattern tests
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/domain/test_exceptions.py -v
pytest tests/unit/infrastructure/database/test_user_mapper.py -v
pytest tests/unit/infrastructure/database/test_user_repository.py -v

# Run with coverage
pytest tests/unit/ --cov=src --cov-report=html

# Run only fast tests (exclude slow/integration)
pytest tests/unit/ -v -m "not slow"
```

### Run Tests by Category
```bash
# Domain layer tests only
pytest tests/unit/domain/ -v

# Infrastructure layer tests only
pytest tests/unit/infrastructure/ -v

# Repository pattern tests only
pytest tests/unit/ -v -m repository
```

## Test Strategy

### Unit Tests (Mocked Dependencies)
All tests in this directory are **unit tests** that:
- Mock external dependencies (SQLAlchemy Session, database)
- Test single components in isolation
- Run fast (milliseconds)
- Don't require database connection
- Follow AAA pattern (Arrange, Act, Assert)

### What We Test
✅ **Happy paths** - Normal operation
✅ **Error cases** - Exception handling
✅ **Edge cases** - Null values, empty lists
✅ **Business rules** - Domain logic validation
✅ **Integration points** - Mapper conversions
✅ **Exception hierarchy** - Correct exception types

### What We DON'T Test Here
❌ Actual database operations (see integration tests)
❌ Network calls
❌ File I/O
❌ External services

## Test Coverage Goals

| Component | Target Coverage | Status |
|-----------|----------------|---------|
| Domain Exceptions | 100% | ✅ Achieved |
| UserMapper | 100% | ✅ Achieved |
| UserRepository | 90%+ | ✅ Achieved |

## Key Testing Patterns

### 1. Fixtures for Test Data
```python
@pytest.fixture
def sample_domain_user():
    """Reusable domain user for tests."""
    return DomainUser(...)
```

### 2. Mocking SQLAlchemy Session
```python
@pytest.fixture
def mock_session():
    """Mock session to avoid real DB."""
    session = Mock(spec=Session)
    session.query = Mock()
    return session
```

### 3. Testing Exception Handling
```python
def test_duplicate_email_raises_error():
    with pytest.raises(DuplicateEmailError) as exc_info:
        repository.create(user)

    assert "email" in str(exc_info.value)
```

### 4. Verifying Mock Calls
```python
mock_session.rollback.assert_called_once()
mock_session.add.assert_called_once()
```

## Bugs Caught by These Tests

These tests were designed to catch the bugs found in code audit:

1. **Bug #2 (UserRepository.update exception handling)**
   - Test: `test_update_user_not_found_raises_error()`
   - Verifies: UserNotFoundError is not wrapped in RepositoryError

2. **Bug #3 (exists_by_email inefficiency)**
   - Test: `test_exists_by_email_user_exists()`
   - Verifies: Uses SQLAlchemy EXISTS query, not .first()

3. **Mapper immutability**
   - Test: `test_update_db_from_domain_does_not_change_id()`
   - Test: `test_update_db_from_domain_does_not_change_created_at()`
   - Verifies: ID and created_at never change during update

## CI/CD Integration

These tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run Unit Tests
  run: |
    pytest tests/unit/ -v --cov=src --cov-report=xml

- name: Upload Coverage
  uses: codecov/codecov-action@v3
```

## Maintenance Notes

- Keep tests independent (no shared state)
- Use descriptive test names (test_method_scenario_expected)
- One assertion per test (when possible)
- Mock external dependencies, not domain logic
- Update tests when domain rules change
