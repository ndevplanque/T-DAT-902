import os
import folium

def create():
    token = os.getenv('MAPBOX_ACCESS_TOKEN')
    return folium.Map(
       location=[48.584614, 7.750713], # Strasbourg
       zoom_start=10,
       tiles=f"https://api.mapbox.com/styles/v1/mapbox/streets-v12/tiles/{{z}}/{{x}}/{{y}}?access_token={token}",
       attr='Mapbox',
    )

# Utilisation d'une échelle de couleurs douces, du vert au rouge
colors = [
    "#006400",  # Vert foncé
    "#228B22",  # Vert forêt
    "#32CD32",  # Vert lime
    "#7CFC00",  # Vert clair
    "#ADFF2F",  # Vert jaune
    "#FFFF00",  # Jaune
    "#FFD700",  # Jaune doré
    "#FFA500",  # Orange
    "#FF8C00",  # Orange foncé
    "#FF6347",  # Tomate
    "#FF4500",  # Rouge orangé
    "#FF0000"   # Rouge
]

def get_fill_color(price, min_price, max_price):
    # Calcul de la position relative entre le prix min et max
    normalized_price = (price - min_price) / (max_price - min_price)

    # Sélection de la couleur correspondante
    return colors[int(normalized_price * (len(colors) - 1))]

def polygon(zone, min_price, max_price):
    return folium.Polygon(
        locations=zone["coordinates"],
        color="white",
        weight=1,
        fill=True,
        fill_color=get_fill_color(zone["price"], min_price, max_price),
        fill_opacity=0.3,
        popup=zone["name"]
    )