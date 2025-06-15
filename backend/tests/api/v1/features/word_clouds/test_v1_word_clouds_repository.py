from v1.features.word_clouds.repository import get_word_frequencies
import pytest


def test_get_word_frequencies_valid_city():
    """Test avec une entité valide 'cities' et un ID valide"""
    entity = 'cities'
    city_id = '12345'
    expected_result = {'test': 5, 'example': 3}

    class MockDB:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def find_one(self, collection, query, fields):
            return {
                'mots': [
                    {'mot': 'test', 'poids': 5},
                    {'mot': 'example', 'poids': 3}
                ]
            }

    # Remplace MongoDB par MockMongoDB
    # Mock MongoDB
    from v1.database.mongodb import MongoDB
    MongoDB.__new__ = lambda cls: MockDB()

    result = get_word_frequencies(entity, city_id)
    assert result == expected_result


def test_get_word_frequencies_invalid_entity():
    """Test avec une entité invalide"""
    with pytest.raises(AttributeError, match="Les nuages de mots ne sont disponibles que pour les 'cities'"):
        get_word_frequencies('invalid_entity', 'valid_id')


def test_get_word_frequencies_no_words():
    """Test avec un document sans mots"""
    mock_db_result = {}

    class MockDB:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def find_one(self, collection, query, fields):
            return mock_db_result

    # Remplace MongoDB par MockDB
    from v1.database.mongodb import MongoDB
    MongoDB.__new__ = lambda cls: MockDB()

    result = get_word_frequencies('cities', 'valid_id')
    assert result == {}

