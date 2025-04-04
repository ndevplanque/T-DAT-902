from v1.features.word_clouds.repository import get_word_cloud


def test_get_word_cloud():
    """Test de la fonction get_word_cloud"""
    entity = "cities"
    id = 1

    result = get_word_cloud(entity, id)

    assert result == {
        'Lorem': 100,
        'Ipsum': 80,
        'Dolor': 60,
        'Sit': 40,
        'Amet': 20
    }
