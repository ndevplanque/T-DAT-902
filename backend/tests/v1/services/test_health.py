import pytest
from v1.services.health import health

def test_health():
    result = health()

    assert isinstance(result, dict)
    assert "success" in result
    assert result["success"] is True
