from v1.features.health.service import health


def test_health():
    result = health()

    assert isinstance(result, dict)
    assert "success" in result
    assert result["success"] == True
