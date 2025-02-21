import pytest
from v1.services.example import example

def test_example():
    result = example()

    assert isinstance(result, dict)
    assert "message" in result
    assert result["message"] is "Hello from Flask!"
    assert "value" in result
    assert result["value"] is 42
