from v1.models.bounds import Bounds


def mocked_map_areas_feature_collection(size=1):
    return {
        "type": "FeatureCollection",
        "features": [{}] * size
    }


def mocked_map_areas_bounds():
    return Bounds(10, 48.8566, 2.3522, 48.8567, 2.3523)  # Paris


def mocked_sentiments_data():
    return {
        "positif": 50,
        "neutre": 30,
        "negatif": 20
    }


def mocked_sentiments_labels_values_colors():
    return ['Positif', 'Neutre', 'Négatif'], [50, 30, 20], ['green', 'gray', 'red']


def mocked_word_clouds_data():
    return {
        "Lorem": 100,
        "Ipsum": 80,
        "Dolor": 60,
        "Sit": 40,
        "Amet": 20
    }
