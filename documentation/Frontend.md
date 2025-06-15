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
│   ├── 2_📙_Details.py      # Page détails zones avec visualisations
│   └── 3_ℹ️_About.py        # Page à propos (équipe, sources)
├── components/               # Composants réutilisables
│   ├── PriceTable.py        # Composant tableau de prix
│   └── AreaDetails.py       # Composant détails zone (ratings, charts)
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
if api.v1_health()["success"]:
    st.write("Statut : en ligne ✅")
else:
    st.error("Statut : hors-ligne ❌")
```

#### 2. Carte interactive (1_🌍_Map.py)
**Fonction**: Visualisation cartographique des données géospatiales

**Fonctionnalités**:
- Carte Leaflet plein écran (600px de hauteur)
- Configuration en mode "wide" pour maximiser l'espace
- Intégration HTML personnalisée via `st.components.v1.html()`

#### 3. Page détails (2_📙_Details.py)
**Fonction**: Exploration détaillée des zones avec intégration tableaux prix

**Fonctionnalités**:
- **Sélecteur de localités**: Dropdown pour choisir villes spécifiques (cities uniquement)
- **Affichage conditionnel**: 
  - Si ville sélectionnée: Composant AreaDetails avec ratings, sentiment, word cloud, transactions
  - Si aucune sélection: Tableaux prix pour régions, départements, villes
- **Gestion d'erreurs**: Try-catch avec messages utilisateur explicites

#### 4. Page à propos (3_ℹ️_About.py)
**Fonction**: Informations projet et crédits équipe

**Contenu**:
- **Sources de données**: Description BAN, data.gouv.fr
- **Crédits équipe**: Liens vers profils GitHub des membres
- **Contexte projet**: Présentation générale de Homepedia

## Composants de visualisation

### Composant PriceTable

Composant mis à jour pour la nouvelle structure de données:

```python
def PriceTable(data):
    """Affiche un tableau de prix avec interface pliable"""
    # Nouvelle structure: data['aggs']['min_price'] au lieu de calcul manuel
    min_price = data['aggs']['min_price']
    max_price = data['aggs']['max_price']
    
    with st.expander(f"📍 {data['title']} (Min: {min_price}€ | Max: {max_price}€)"):
        # Nouvelle structure: data["items"] au lieu de data["data"]
        df = pd.DataFrame(data["items"])
        st.dataframe(df, use_container_width=True)
```

**Changements structure**:
- **Données**: `data["items"]` remplace `data["data"]`
- **Statistiques**: `data['aggs']['min_price']` pré-calculées
- **Colonnes**: "Numéro", "Zone", "Prix (€/m²)" standardisées

### Composant AreaDetails

Nouveau composant pour visualisations avancées:

```python
def AreaDetails(item, area_details, area_transactions):
    """Affiche détails complets d'une zone avec visualisations"""
    # Système de notation (5 catégories)
    grades = area_details["rating"]["grades"]
    # Colonnes pour les 5 catégories
    educ, envi, secu, spor, life = st.columns(5, border=True)
    
    # Visualisations dual-column
    col1, col2 = st.columns(2)
    with col1:
        # Graphique sentiment (Plotly donut)
        sentiments_fig = build_sentiments_fig(area_details['sentiments'])
        st.plotly_chart(sentiments_fig)
    
    with col2:
        # Nuage de mots (matplotlib/wordcloud)
        wordcloud_fig = build_wordcloud_fig(area_details['word_frequencies'])
        st.pyplot(wordcloud_fig)
```

**Fonctionnalités**:
- **Ratings visuels**: Métriques grandes avec scores /5
- **Charts interactifs**: Plotly pour sentiment analysis
- **Nuages de mots**: Génération dynamique avec wordcloud
- **Layout responsive**: Colonnes adaptatives
- **Gestion d'erreurs**: Fallbacks gracieux si données manquantes

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
- OpenStreetMap tiles        # Tuiles cartographiques (pas Mapbox)
```

**Couches de données**:
- **priceLayer**: Visualisation des prix immobiliers par zone (implémenté)
- **satisfactionLayer**: Interface préparée mais non implémentée

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

2. **Area Listing**: `GET /api/v1/area-listing`
   - Récupération listing complet zones avec statistiques prix réelles
   - Structure: `{"regions": [...], "departments": [...], "cities": [...]}`
   - Mise en cache automatique

3. **Area Details**: `GET /api/v1/area-details/{entity}/{id}`
   - Données détaillées zones (ratings, population, avis)
   - Intégration dans composant AreaDetails

4. **Area Transactions**: `GET /api/v1/area-transactions/{entity}/{id}`
   - Transactions immobilières individuelles par zone
   - Données réelles DVF avec dates, prix, surfaces

5. **Map Areas**: `GET /api/v1/map-areas/{zoom}/{bounds}`
   - Données géospatiales avec statistiques prix intégrées
   - Chargement dynamique selon le viewport

6. **Word Clouds & Sentiments**: 
   - Génération d'images à la demande
   - Intégration dans panneau détails AreaDetails

## Gestion du cache

### Cache Streamlit optimisé

```python
# utils/cache.py
@st.cache_data
def get_area_listing():
    """Cache uniquement les requêtes réussies"""
    try:
        data = api.v1_area_listing()
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
wordcloud       # Génération nuages de mots
plotly          # Graphiques interactifs (donut charts)
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
3. **Transactions limitées**: Endpoint area-transactions villes uniquement
4. **Cache global**: Pas de granularité fine par endpoint
5. **Images non cachées**: Nuages de mots régénérés à chaque visite

### Évolutions prévues

1. **Cache images**: Mise en cache nuages de mots et graphiques
2. **Transactions étendues**: Support départements/régions
3. **Dashboard avancé**: Métriques et KPIs temps réel
4. **Export de données**: Fonctionnalités d'export avancées (CSV, PDF)
5. **Personnalisation**: Thèmes et préférences utilisateur
6. **Mobile responsive**: Optimisation pour appareils mobiles
7. **Authentification**: Intégration système de login
8. **Historique transactions**: Graphiques évolution prix dans le temps

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