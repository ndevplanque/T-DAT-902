import matplotlib.pyplot as plt
from matplotlib.patches import Wedge
from matplotlib.colors import to_rgba
from unittest.mock import patch
from test_helper import mocked_sentiments_data, mocked_sentiments_labels_values_colors
from v1.features.sentiments.service import (
    sentiments,
    get_values_labels_colors,
    build_chart,
    to_png,
)


@patch('v1.features.sentiments.service.get_values_labels_colors')
@patch('v1.features.sentiments.repository.get_sentiments')
def test_sentiments(mock_get_sentiments, mock_get_values_labels_colors):
    """Test de la fonction sentiments"""

    # Test avec des paramètres invalides
    try:
        sentiments("bug", 1)
        assert False, "Expected a AttributeError for invalid parameters"
    except AttributeError as e:
        assert str(e) == "Les nuages de mots ne sont disponibles que pour les 'cities', 'departments' ou 'regions'"

    # Test avec des paramètres valides
    entity = "cities"
    id = 1

    # Mock des données de retour
    mock_get_sentiments.return_value = mocked_sentiments_data()
    mock_get_values_labels_colors.return_value = mocked_sentiments_labels_values_colors()

    # Appel de la fonction
    response = sentiments(entity, id)

    # Vérifiez que la fonction get_sentiments a été appelée avec les bons arguments
    mock_get_sentiments.assert_called_once_with(entity, id)
    mock_get_values_labels_colors.assert_called_once_with(mock_get_sentiments.return_value)

    assert response is not None
    assert response.mimetype == "image/png"
    assert len(response.data) > 0


def test_get_values_labels_colors():
    """Test de la fonction get_values_labels_colors"""

    # Test avec des données invalides
    try:
        get_values_labels_colors({"bug": 1})
        assert False, "Expected a ValueError for invalid data"
    except ValueError as e:
        assert str(e) == "Données invalides."

    # Test avec des données vides
    try:
        get_values_labels_colors({})
        assert False, "Expected a ValueError for empty data"
    except ValueError as e:
        assert str(e) == "Données invalides."

    # Test avec des données valides
    labels, values, colors = get_values_labels_colors(mocked_sentiments_data())

    # Vérifiez que les labels sont corrects
    assert labels == ["Positif", "Neutre", "Négatif"]
    assert values == [50, 30, 20]
    assert colors == ["green", "gray", "red"]


def test_build_chart():
    labels, values, colors = mocked_sentiments_labels_values_colors()

    fig, ax = build_chart(labels, values, colors)

    # Vérifiez que la figure et les axes sont créés
    assert fig is not None
    assert ax is not None

    # Vérifiez que le nombre de wedges correspond au nombre de valeurs
    wedges = [w for w in ax.patches if isinstance(w, Wedge)]
    assert len(wedges) == len(values)

    # Vérifiez que les couleurs des wedges sont correctes
    for wedge, color in zip(wedges, colors):
        assert wedge.get_facecolor() == to_rgba(color)

    # Vérifiez que le trou du donut chart est présent
    circles = [c for c in ax.patches if isinstance(c, plt.Circle)]
    assert len(circles) == 1
    assert circles[0].get_radius() == 0.7

    # Vérifiez que la légende est correctement configurée
    legend = ax.get_legend()
    assert legend is not None
    assert legend.get_title().get_text() == "Sentiments"
    assert len(legend.get_texts()) == len(labels)
    for text, label in zip(legend.get_texts(), labels):
        assert text.get_text() == label


def test_to_png():
    """Test de la fonction to_png"""
    labels, values, colors = mocked_sentiments_labels_values_colors()

    fig, ax = build_chart(labels, values, colors)
    png_data = to_png(fig)

    # Vérifiez que les données PNG ne sont pas vides
    assert png_data is not None
    assert len(png_data) > 0

    # Vérifiez que les données PNG commencent par les octets corrects pour un fichier PNG
    assert png_data[:8] == b'\x89PNG\r\n\x1a\n'
