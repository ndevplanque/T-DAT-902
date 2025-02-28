**Documentation du Schéma de la Base MongoDB - HOMEPEDIA**

# Introduction
Ce document présente la structure et l'organisation de la base de données MongoDB utilisée pour le projet **HOMEPEDIA**. Cette base est conçue pour stocker et analyser les avis des habitants ainsi que les signalements urbains, complétant ainsi les données du marché immobilier.

---

## 1. Aperçu de la Structure MongoDB
La base de données MongoDB repose sur deux collections principales :
- **city_reviews** : Stocke les avis des résidents sur une ville.
- **urban_reports** : Contient les signalements urbains (incivilités, nuisances, problèmes environnementaux, etc.).

---

## 2. Schéma de la Collection `city_reviews`
Cette collection regroupe les avis des habitants sur divers aspects d'une ville.

### **Exemple de document MongoDB :**
```json
{
    "city_id": 67482,
    "city_name": "Strasbourg",
    "average_rating": 3.4,
    "total_reviews": 269,
    "ratings": {
        "sécurité": 3.0,
        "éducation": 3.7,
        "sport_loisir": 3.7,
        "environnement": 3.2,
        "vie_pratique": 3.6
    },
    "reviews": [
        {
            "user_id": "Glo",
            "date": "2024-12-30T00:00:00Z",
            "ratings": {
                "sécurité": 2,
                "éducation": 2,
                "sport_loisir": 2,
                "environnement": 2,
                "vie_pratique": 2
            },
            "comment": "Ville magnifique en période des fêtes de Noël, mais stationnement très cher !",
            "likes": 4,
            "dislikes": 2
        }
    ]
}
```

### **Définition des champs :**
- `city_id` (**int**) : Identifiant unique de la ville.
- `city_name` (**string**) : Nom de la ville.
- `average_rating` (**double**) : Note moyenne attribuée à la ville.
- `total_reviews` (**int**) : Nombre total d'avis.
- `ratings` (**objet**) : Moyenne des notes par critère (sécurité, éducation, etc.).
- `reviews` (**array**) : Liste des avis individuels.
    - `user_id` (**string**) : Identifiant de l'utilisateur.
    - `date` (**ISODate**) : Date de publication.
    - `ratings` (**objet**) : Notes de l'utilisateur par critère.
    - `comment` (**string**) : Avis de l'utilisateur.
    - `likes` (**int**) : Nombre de likes.
    - `dislikes` (**int**) : Nombre de dislikes.

---

## 3. Schéma de la Collection `urban_reports`
Cette collection enregistre les signalements urbains effectués par les habitants.

### **Exemple de document MongoDB :**
```json
{
    "city_id": 67482,
    "city_name": "Strasbourg",
    "total_reports": 4,
    "reports": [
        {
            "report_id": "603d2f1e3f1a3e1a3c1e1f1a",
            "type": "Dépôt sauvage / Objets abandonnés",
            "description": "Dépôt sauvage de pneu",
            "date_reported": "2024-12-30T00:00:00Z",
            "reported_by": "Nad",
            "location": "Quai Des Joncs, 67000 Strasbourg, France",
            "status": "En cours"
        }
    ]
}
```

### **Définition des champs :**
- `city_id` (**int**) : Identifiant unique de la ville.
- `city_name` (**string**) : Nom de la ville.
- `total_reports` (**int**) : Nombre total de signalements.
- `reports` (**array**) : Liste des signalements.
    - `report_id` (**ObjectId**) : Identifiant du signalement.
    - `type` (**string**) : Catégorie du signalement.
    - `description` (**string**) : Détails du signalement.
    - `date_reported` (**ISODate**) : Date du signalement.
    - `reported_by` (**string**) : Nom ou pseudonyme de l'utilisateur.
    - `location` (**string**) : Adresse du signalement.
    - `status` (**string**) : Statut du signalement ("En cours" ou "Résolu").

---

## 4. Indexation et Optimisation
Pour garantir des performances optimales, nous avons ajouté des index sur les champs clés :
```json
 db.city_reviews.createIndex({ city_id: 1 })
 db.urban_reports.createIndex({ city_id: 1 })
 db.urban_reports.createIndex({ "reports.report_id": 1 })
```
- Index sur `city_id` : Permet une recherche rapide par ville.
- Index sur `reports.report_id` : Accélère l'accès aux signalements spécifiques.

---

## 5. Conclusion
Ce document décrit la structure de la base MongoDB utilisée dans le projet HOMEPEDIA. Le stockage en NoSQL nous permet de gérer de grandes quantités de données non structurées, tout en assurant la cohérence et l'efficacité des analyses.

---