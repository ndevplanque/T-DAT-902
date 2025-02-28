import folium
import psycopg2
from shapely import wkt

# Connexion à la base de données PostgreSQL
conn = psycopg2.connect(dbname='gis_db', user='postgres', password='postgres', host='localhost', port='5432')
cur = conn.cursor()

# Créer une carte centrée sur la France
m = folium.Map(location=[46.0, 2.0], zoom_start=6)

# ---------------------------
# Couche pour les villes
# ---------------------------
cities_layer = folium.FeatureGroup(name='Villes')
cur.execute("SELECT city_id, name, ST_AsText(geom) FROM cities;")
for city_id, name, geom_wkt in cur.fetchall():
    geom = wkt.loads(geom_wkt)
    folium.GeoJson(
        data=geom.__geo_interface__,
        style_function=lambda feature: {
            'fillColor': 'blue',
            'color': 'blue',
            'weight': 1,
            'fillOpacity': 0.5
        },
        tooltip=name
    ).add_to(cities_layer)
m.add_child(cities_layer)

# ---------------------------
# Couche pour les départements
# ---------------------------
departments_layer = folium.FeatureGroup(name='Départements')
cur.execute("SELECT department_id, name, ST_AsText(geom) FROM departments;")
for department_id, name, geom_wkt in cur.fetchall():
    geom = wkt.loads(geom_wkt)
    folium.GeoJson(
        data=geom.__geo_interface__,
        style_function=lambda feature: {
            'fillColor': 'green',
            'color': 'green',
            'weight': 2,
            'fillOpacity': 0.3
        },
        tooltip=name
    ).add_to(departments_layer)
m.add_child(departments_layer)

# ---------------------------
# Couche pour les régions
# ---------------------------
regions_layer = folium.FeatureGroup(name='Régions')
cur.execute("SELECT region_id, name, ST_AsText(geom) FROM regions;")
for region_id, name, geom_wkt in cur.fetchall():
    geom = wkt.loads(geom_wkt)
    folium.GeoJson(
        data=geom.__geo_interface__,
        style_function=lambda feature: {
            'fillColor': 'red',
            'color': 'red',
            'weight': 3,
            'fillOpacity': 0.1
        },
        tooltip=name
    ).add_to(regions_layer)
m.add_child(regions_layer)

# Ajouter un contrôle de couches pour pouvoir activer/désactiver chaque couche
folium.LayerControl().add_to(m)

# Sauvegarder la carte dans un fichier HTML
m.save("map_all_layers.html")

cur.close()
conn.close()