"""
Tests for SDK initialization.
"""

import fleeks_sdk


def test_version():
    """Test that version is available."""
    assert hasattr(fleeks_sdk, '__version__')
    assert fleeks_sdk.__version__ == "0.1.0"


def test_imports():
    """Test that main classes can be imported."""
    from fleeks_sdk import FleeksClient, FleeksException, FleeksAPIError
    
    assert FleeksClient is not None
    assert FleeksException is not None
    assert FleeksAPIError is not None