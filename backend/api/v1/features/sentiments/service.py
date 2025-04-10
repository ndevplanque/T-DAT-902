from flask import Response
from io import BytesIO
import matplotlib.pyplot as plt
import v1.features.sentiments.repository as repository


def sentiments(entity, id):
    # Vérifier que l'entité est valide
    if entity not in ["cities", "departments", "regions"]:
        raise AttributeError("Les nuages de mots ne sont disponibles que pour les 'cities', 'departments' ou 'regions'")

    # Récupérer les données
    sentiments = repository.get_sentiments(entity, id)

    # Traduire les données en labels, valeurs et couleurs
    labels, values, colors = get_values_labels_colors(sentiments)

    # Création du donut chart
    chart, ax = build_chart(labels, values, colors)

    return Response(to_png(chart), mimetype="image/png")


def get_values_labels_colors(data):
    chart_keys = ["positif", "neutre", "negatif"]
    translations = {
        "positif": "Positif",
        "neutre": "Neutre",
        "negatif": "Négatif"
    }

    # Vérification des données
    if not data or not all(key in data for key in chart_keys):
        raise ValueError("Données invalides.")

    # Préparation les données pour le donut chart
    labels = [translations[key] for key in chart_keys]
    values = [data[key] for key in chart_keys]
    colors = ["green", "gray", "red"]

    return labels, values, colors


def build_chart(labels, values, colors):
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

    return fig, ax


def to_png(fig):
    img_io = BytesIO()
    fig.savefig(img_io, format="png", bbox_inches="tight")
    plt.close(fig)  # Fermer pour éviter la surcharge mémoire
    img_io.seek(0)
    return img_io.getvalue()
