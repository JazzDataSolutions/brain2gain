"""
Configuration for unit tests that don't require database connections.
"""

import pytest
from unittest.mock import Mock

# This conftest.py overrides the parent conftest.py for unit tests
# It provides a lightweight testing environment without database dependencies

@pytest.fixture(scope="session", autouse=True)
def mock_db():
    """Mock database session for unit tests that don't need real DB."""
    return Mock()

@pytest.fixture(scope="module")
def mock_client():
    """Mock client for unit tests."""
    return Mock()

# Override parent fixtures to prevent database connections
@pytest.fixture(scope="session")
def db():
    """Override parent db fixture to prevent database connection."""
    return Mock()

@pytest.fixture(scope="module") 
def client():
    """Override parent client fixture."""
    return Mock()

@pytest.fixture(scope="module")
def superuser_token_headers():
    """Override parent superuser_token_headers fixture."""
    return {"Authorization": "Bearer mock-token"}

@pytest.fixture(scope="module")
def normal_user_token_headers():
    """Override parent normal_user_token_headers fixture."""
    return {"Authorization": "Bearer mock-token"}