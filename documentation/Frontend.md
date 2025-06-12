# Frontend - Application Streamlit

## Vue d'ensemble

Le frontend de Homepedia est une application web développée avec **Streamlit** qui offre une interface utilisateur intuitive pour visualiser et explorer les données immobilières et géographiques. L'application utilise une architecture multi-pages avec des composants de visualisation interactifs, notamment une carte Leaflet intégrée et des tableaux de données dynamiques.

## Architecture technique

### Technologies utilisées

- **Framework**: Streamlit (Python)
- **Cartographie**: Leaflet.js avec plugins
- **Données**: Pandas DataFrames
- **Communication**: Requests HTTP vers API Flask
- **Cache**: Cache intégré Streamlit
- **Containerisation**: Docker avec mode développement

### Structure de l'application

```
frontend/app/
├── 🏠_Homepedia.py           # Page d'accueil (point d'entrée)
├── pages/                    # Pages navigables
│   ├── 1_🌍_Map.py          # Carte interactive
│   ├── 2_💰_Price_Tables.py  # Tableaux de prix
│   └── 3_🧪_Test.py         # Page de test/développement
├── components/               # Composants réutilisables
│   └── PriceTable.py        # Composant tableau de prix
└── utils/                   # Utilitaires
    ├── api.py               # Interface API backend
    ├── cache.py             # Gestion du cache
    └── map.html             # Template carte Leaflet
```

## Navigation et pages

### Architecture multi-pages

Streamlit détecte automatiquement les fichiers dans le dossier `/pages/` et génère une navigation sidebar automatique:

- **Nommage**: Préfixes numériques (`1_`, `2_`) pour l'ordre d'affichage
- **Emojis**: Intégrés dans les noms pour améliorer l'UX
- **URLs directes**: Chaque page accessible via URL spécifique

### Pages disponibles

#### 1. Page d'accueil (🏠_Homepedia.py)
**Fonction**: Point d'entrée et vérification de santé du système

**Fonctionnalités**:
- Affichage du titre principal de l'application
- Health check de l'API backend
- Indicateur visuel de statut (✅ Connecté / ❌ Déconnecté)

```python
# Vérification de santé avec feedback visuel
health_status = api.v1_health()
if health_status:
    st.success("✅ API Backend connectée")
else:
    st.error("❌ API Backend non disponible")
```

#### 2. Carte interactive (1_🌍_Map.py)
**Fonction**: Visualisation cartographique des données géospatiales

**Fonctionnalités**:
- Carte Leaflet plein écran (600px de hauteur)
- Configuration en mode "wide" pour maximiser l'espace
- Intégration HTML personnalisée via `st.components.v1.html()`

#### 3. Tableaux de prix (2_💰_Price_Tables.py)
**Fonction**: Affichage tabulaire des données de prix immobiliers

**Fonctionnalités**:
- Récupération des données via cache optimisé
- Affichage multi-tableaux avec composant réutilisable
- Gestion d'erreurs robuste avec messages utilisateur
- Interface expandable pour économiser l'espace

#### 4. Page test (3_🧪_Test.py)
**Fonction**: Environnement de développement et tests

**État**: Page minimale pour tests et développements futurs

## Composants de visualisation

### Composant PriceTable

Le composant `PriceTable` fournit une interface standardisée pour afficher les données de prix:

```python
def PriceTable(data):
    """Affiche un tableau de prix avec interface pliable"""
    min_price = min(item["Moyenne"] for item in data["data"])
    max_price = max(item["Moyenne"] for item in data["data"])
    
    with st.expander(f"📍 {data['title']} (Min: {min_price}€ | Max: {max_price}€)"):
        df = pd.DataFrame(data["data"])
        st.dataframe(df, use_container_width=True)
```

**Caractéristiques**:
- **Interface pliable**: `st.expander` pour optimiser l'espace
- **Statistiques**: Affichage min/max dans le titre
- **DataFrame intégré**: Conversion automatique et affichage responsive
- **Largeur adaptive**: `use_container_width=True`

### Carte interactive Leaflet

La carte utilise un template HTML personnalisé intégrant Leaflet.js:

**Configuration technique**:
```javascript
// Configuration de base
const INITIAL_LOCATION = [48.584614, 7.750713]; // Strasbourg
const INITIAL_ZOOM = 10;
const API_URL = "http://localhost:5001";

// Librairies utilisées
- Leaflet.js (v1.9.4)         # Cartographie de base
- Leaflet-Ajax               # Chargement GeoJSON dynamique
- Leaflet-Fullscreen         # Mode plein écran
```

**Couches de données**:
- **priceLayer**: Visualisation des prix immobiliers par zone
- **satisfactionLayer**: Données de satisfaction (préparé, non implémenté)

**Interactions utilisateur**:
- **Hover**: Tooltips avec informations de prix
- **Click**: Panneau latéral avec détails complets
- **Zoom dynamique**: Rechargement des données selon le niveau
- **Contrôles**: Sélecteur de couches, zoom, mode plein écran

**Chargement dynamique des données**:
```javascript
// Chargement adaptatif selon la position et le zoom
map.on('moveend', function() {
    const bounds = map.getBounds();
    const zoom = map.getZoom();
    loadMapAreas(bounds, zoom);
});
```

## Intégration API Backend

### Configuration de connexion

```python
# utils/api.py
API_URL = os.getenv('API_URL', 'http://backend:5001')

def _api_v1(endpoint):
    """Construction d'URLs API v1"""
    return f"{API_URL}/api/v1/{endpoint}"
```

### Endpoints utilisés

1. **Health Check**: `GET /api/v1/health`
   - Vérification de la disponibilité du backend
   - Affichage de statut en temps réel

2. **Price Tables**: `GET /api/v1/price-tables`
   - Récupération des tableaux de prix par région/département/ville
   - Mise en cache automatique

3. **Map Areas**: `GET /api/v1/map-areas/{zoom}/{bounds}`
   - Données géospatiales pour la carte
   - Chargement dynamique selon le viewport

4. **Word Clouds & Sentiments**: 
   - Génération d'images à la demande
   - Intégration dans les panneaux de détails

## Gestion du cache

### Cache Streamlit optimisé

```python
# utils/cache.py
@st.cache_data
def get_price_tables():
    """Cache uniquement les requêtes réussies"""
    try:
        data = api.v1_price_tables()
        if data is not None:
            return data
        else:
            raise RuntimeError("Échec de la récupération des données")
    except Exception as e:
        st.error(f"Erreur: {e}")
        return None
```

**Avantages**:
- **Performance**: Évite les appels API répétés
- **Gestion d'erreurs**: Cache uniquement les succès
- **Invalidation automatique**: Streamlit gère l'invalidation

## Configuration et déploiement

### Variables d'environnement

```bash
# Configuration API
API_URL=http://backend:5001

# Configuration Mapbox (optionnel)
MAPBOX_ACCESS_TOKEN=your_token_here

# Configuration Streamlit
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_DEVELOPMENT=true
STREAMLIT_SERVER_RUN_ON_SAVE=true
```

### Configuration Docker

```yaml
frontend:
  build: ./frontend
  ports: ["8501:8501"]
  volumes: ["./frontend:/app"]
  environment:
    - STREAMLIT_SERVER_HEADLESS=true
    - STREAMLIT_DEVELOPMENT=true
    - STREAMLIT_SERVER_RUN_ON_SAVE=true
  depends_on: [backend]
```

### Dépendances

```txt
streamlit       # Framework web principal
requests        # Communication HTTP
pandas          # Manipulation de données
python-dotenv   # Variables d'environnement
```

## Interface utilisateur et UX

### Design et ergonomie

**Principes de design**:
- **Emojis systématiques**: Amélioration de la lisibilité et navigation
- **Layout responsive**: Mode "wide" pour les cartes, conteneurs adaptatifs
- **Feedback visuel**: Indicateurs de statut, spinners, messages d'erreur
- **Navigation intuitive**: Sidebar automatique avec ordre logique

**Composants UX**:
- **Expandable tables**: Interface pliable pour optimiser l'espace écran
- **Status indicators**: ✅/❌ pour la connectivité API
- **Loading states**: Spinners pendant les chargements d'images/données
- **Error handling**: Messages d'erreur clairs et contextuels

### Interactions avancées

**Carte interactive**:
- Tooltips informatifs au survol des zones
- Panneau de détails avec nuages de mots et sentiments
- Contrôles de zoom et sélecteur de couches
- Mode plein écran pour visualisation immersive

**Tableaux de données**:
- Tri automatique des colonnes
- Recherche intégrée Streamlit
- Export CSV disponible
- Affichage de statistiques descriptives

## Performance et optimisations

### Optimisations Frontend

1. **Cache intelligent**: Mise en cache des appels API coûteux
2. **Chargement lazy**: Données cartographiques chargées à la demande
3. **Images optimisées**: Format PNG optimisé pour les nuages de mots
4. **État persistant**: Conservation de l'état de navigation

### Optimisations Cartographiques

1. **Zoom adaptatif**: Granularité des données selon le niveau de zoom
2. **Bounds filtering**: Chargement uniquement des données visibles
3. **Layer management**: Gestion intelligente des couches actives
4. **Memory management**: Nettoyage automatique des anciennes données

## Limitations et évolutions futures

### Limitations actuelles

1. **Token Mapbox inutilisé**: Configuration présente mais OpenStreetMap utilisé
2. **Couche satisfaction**: Interface préparée mais données backend manquantes
3. **Page test vide**: Environnement de développement non utilisé
4. **Cache global**: Pas de granularité fine par endpoint

### Évolutions prévues

1. **Authentification**: Intégration système de login
2. **Dashboard avancé**: Métriques et KPIs temps réel
3. **Export de données**: Fonctionnalités d'export avancées
4. **Personnalisation**: Thèmes et préférences utilisateur
5. **Mobile responsive**: Optimisation pour appareils mobiles

## Sécurité

### Mesures actuelles

- **Variables d'environnement**: Configuration sensible externalisée
- **CORS handling**: Gestion par le backend Flask
- **Input validation**: Validation côté API backend

### Améliorations prévues

- **Content Security Policy**: Protection XSS
- **Rate limiting**: Protection contre le spam
- **Session management**: Gestion sécurisée des sessions

Le frontend Streamlit offre une interface moderne et intuitive pour explorer les données complexes de Homepedia, combinant visualisation cartographique avancée et tableaux de données interactifs dans une architecture modulaire et extensible.