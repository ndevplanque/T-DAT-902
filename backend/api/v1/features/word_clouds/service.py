from flask import Response
from io import BytesIO
from wordcloud import WordCloud
import v1.features.word_clouds.repository as repository


def word_clouds(entity, id):
    # Vérifier que l'entité est valide
    if entity not in ["cities"]:  # , "departments", "regions"]:
        raise AttributeError("Les nuages de mots ne sont disponibles que pour les 'cities'")

    # Récupérer les fréquences des mots
    frequencies = repository.get_word_frequencies(entity, id)

    # Construire le nuage de mots
    word_cloud = build_word_cloud(frequencies)

    # Retourner l'image en réponse HTTP avec le bon type MIME
    return Response(to_png(word_cloud), mimetype="image/png")


def build_word_cloud(frequencies):
    # Vérification des données
    if not frequencies or not all(isinstance(frequencies.get(key), int) for key in frequencies):
        raise ValueError("Données invalides.")

    # Générer le nuage de mots
    return WordCloud(width=250, height=200, background_color="white").generate_from_frequencies(frequencies)


def to_png(word_cloud):
    # Convertir le nuage de mots en image PNG
    img_io = BytesIO()
    word_cloud.to_image().save(img_io, format="PNG")
    img_io.seek(0)
    return img_io.getvalue()
