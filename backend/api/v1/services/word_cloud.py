from flask import Response
from io import BytesIO
from wordcloud import WordCloud
import api.v1.repositories.word_cloud as repository

def word_cloud(entity, id):
    # Vérifier que l'entité est valide
    if entity not in ["cities", "departments", "regions"]:
        raise ValueError("Les nuages de mots ne sont disponibles que pour les 'cities', 'departments' ou 'regions'")

    # Récupérer les fréquences des mots
    freqs = repository.get_word_cloud(entity, id)

    # Vérification des données
    if not freqs or not all(isinstance(freqs.get(key), int) for key in freqs):
        raise ValueError("Données invalides.")

    # Générer le nuage de mots
    word_cloud = WordCloud(width=800, height=400, background_color="white").generate_from_frequencies(freqs)

    # Convertir en image et envoyer la réponse
    img_io = BytesIO()
    word_cloud.to_image().save(img_io, format="PNG")
    img_io.seek(0)

    # Retourner l'image en réponse HTTP avec le bon type MIME
    return Response(img_io.getvalue(), mimetype="image/png")
