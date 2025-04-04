from v1.features.sentiments.repository import get_sentiments


def test_get_sentiments():
    """Test de la fonction get_sentiments"""
    entity = "cities"
    id = 1

    result = get_sentiments(entity, id)

    assert result == {
        "positif": 19,
        "neutre": 2,
        "negatif": 5
    }
