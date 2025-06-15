from unittest.mock import patch
from test_helper import mocked_word_frequencies
from v1.features.word_clouds.service import (
    word_clouds,
    build_word_cloud,
    to_png,
)
from wordcloud import WordCloud


@patch('v1.features.word_clouds.repository.get_word_frequencies')
def test_word_clouds(mock_get_word_frequencies):
    """Test de la fonction word_clouds"""

    # Test avec des paramètres invalides
    try:
        word_clouds("bug", 1)
        assert False, "Expected a AttributeError for invalid parameters"
    except AttributeError as e:
        assert str(e) == "Les nuages de mots ne sont disponibles que pour les 'cities'"

    # Test avec des paramètres valides
    entity = "cities"
    id = 1

    mock_get_word_frequencies.return_value = mocked_word_frequencies()

    response = word_clouds(entity, id)

    # Vérifiez que la fonction get_word_cloud a été appelée avec les bons arguments
    mock_get_word_frequencies.assert_called_once_with(entity, id)

    assert response is not None
    assert response.mimetype == "image/png"
    assert len(response.data) > 0


def test_build_word_cloud():
    """Test de la fonction build_word_cloud"""

    # Test avec des données invalides
    try:
        build_word_cloud({"Lorem": "cent"})
        assert False, "Expected a ValueError for invalid data"
    except ValueError as e:
        assert str(e) == "Données invalides."

    # Test avec des données vides
    try:
        build_word_cloud({})
        assert False, "Expected a ValueError for empty data"
    except ValueError as e:
        assert str(e) == "Données invalides."

    # Test avec des données valides
    frequencies = mocked_word_frequencies()
    word_cloud = build_word_cloud(frequencies)

    # Vérifiez que le nuage de mots est généré
    assert word_cloud is not None
    assert isinstance(word_cloud, WordCloud)

    # Vérifiez que les mots sont présents dans le nuage de mots
    for word in frequencies:
        assert word in word_cloud.words_


def test_to_png():
    """Test de la fonction to_png"""
    word_cloud = build_word_cloud(mocked_word_frequencies())

    png_data = to_png(word_cloud)

    # Vérifiez que les données PNG ne sont pas vides
    assert png_data is not None
    assert len(png_data) > 0

    # Vérifiez que les données PNG commencent par les octets corrects pour un fichier PNG
    assert png_data[:8] == b'\x89PNG\r\n\x1a\n'
