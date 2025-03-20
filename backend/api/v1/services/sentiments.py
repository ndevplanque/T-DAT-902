from flask import Response
from io import BytesIO
import matplotlib.pyplot as plt
import api.v1.repositories.sentiments as repository

def sentiments(entity, id):
    # Vérifier que l'entité est valide
    if entity not in ["cities", "departments", "regions"]:
        raise ValueError("Les nuages de mots ne sont disponibles que pour les 'cities', 'departments' ou 'regions'")

    # Récupérer les données
    sentiments = repository.get_sentiments(entity, id)

    # Vérification des données
    required_keys = ["positif", "neutre", "negatif"]
    if not sentiments or not all(key in sentiments for key in required_keys):
        raise ValueError("Données invalides.")

    # Tableau de conversion pour les labels
    label_conversion = {
        "positif": "Positif",
        "neutre": "Neutre",
        "negatif": "Négatif"
    }

    # Appliquer la conversion des labels
    labels = [label_conversion[key] for key in required_keys]
    values = [sentiments[key] for key in required_keys]
    colors = ["green", "gray", "red"]

    # Création du donut chart
    fig, ax = plt.subplots(figsize=(6, 6))
    wedges, texts, autotexts = ax.pie(
        values,
        autopct='%1.1f%%',
        colors=colors,
        startangle=90,
        wedgeprops={'edgecolor': 'white'}
    )

    # Ajout du trou pour le donut chart
    ax.add_artist(plt.Circle((0, 0), 0.7, fc='white'))  # Ajout du trou

    # Ajouter une légende
    ax.legend(
        wedges,  # Les secteurs du graphique
        labels,  # Les labels correspondants
        title="Sentiments",  # Titre de la légende
        loc="center left",  # Position de la légende
        bbox_to_anchor=(1, 0, 0.5, 1)  # Positionnement de la légende à l'extérieur
    )

    # Sauvegarde en mémoire
    img_io = BytesIO()
    fig.savefig(img_io, format="png", bbox_inches="tight")
    plt.close(fig)  # Fermer pour éviter la surcharge mémoire
    img_io.seek(0)

    return Response(img_io.getvalue(), mimetype="image/png")
