from v1.features.sentiments.repository import get_sentiments
import pytest

def test_get_sentiments_valid_city():
    """Test de get_sentiments avec une entité valide 'cities'"""
    entity = 'cities'
    city_id = '12345'
    expected_result = {'positive': 10, 'negative': 5}

    class MockDB:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def find_one(self, collection, query, fields):
            return {'sentiments': {'positive': 10, 'negative': 5}}

    # Mock MongoDB
    from v1.database.mongodb import MongoDB
    MongoDB.__new__ = lambda cls: MockDB()

    result = get_sentiments(entity, city_id)
    assert result == expected_result

def test_get_sentiments_invalid_entity():
    """Test de get_sentiments avec une entité invalide"""
    entity = 'countries'
    city_id = '12345'

    with pytest.raises(AttributeError, match="Les sentiments ne sont disponibles que pour les 'cities'"):
        get_sentiments(entity, city_id)

def test_get_sentiments_no_sentiments():
    """Test de get_sentiments lorsque aucun sentiment n'est trouvé"""
    entity = 'cities'
    city_id = '67890'

    class MockDB:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def find_one(self, collection, query, fields):
            return {}

    # Mock MongoDB
    from v1.database.mongodb import MongoDB
    MongoDB.__new__ = lambda cls: MockDB()

    result = get_sentiments(entity, city_id)
    assert result == {}
