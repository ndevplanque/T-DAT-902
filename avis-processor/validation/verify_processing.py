#!/usr/bin/env python3
import pymongo
import pandas as pd
from tabulate import tabulate
import matplotlib.pyplot as plt
import seaborn as sns
import os
import json
import time

# Configuration
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://root:rootpassword@mongodb:27017/')
MONGO_DB = os.environ.get('MONGO_DB', 'villes_france')
OUTPUT_DIR = os.environ.get('OUTPUT_DIR', '/app/results')

# Création du répertoire de sortie s'il n'existe pas
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Connexion à MongoDB
client = pymongo.MongoClient(MONGO_URI)
db = client[MONGO_DB]

def analyse_traitement():
    """Analyser les statistiques générales du traitement"""
    # Compter les villes traitées vs non traitées
    total_villes = db.villes.count_documents({})
    villes_traitees = db.villes.count_documents({"statut_traitement": "traite"})
    villes_non_traitees = total_villes - villes_traitees

    # Compter les mots extraits
    mots_villes = list(db.mots_villes.find({}, {"ville_nom": 1, "mots": 1, "sentiments": 1}))
    total_mots_extraits = sum(len(ville.get("mots", [])) for ville in mots_villes)

    print(f"===== STATISTIQUES GÉNÉRALES =====")
    print(f"Total des villes: {total_villes}")
    print(f"Villes traitées: {villes_traitees} ({round(villes_traitees/total_villes*100, 2)}%)")
    print(f"Villes non traitées: {villes_non_traitees}")
    print(f"Total des mots extraits: {total_mots_extraits}")
    print(f"Moyenne de mots par ville: {round(total_mots_extraits/len(mots_villes), 2) if mots_villes else 0}")

    # Analyser la distribution des sentiments
    sentiments_data = []
    for ville in mots_villes:
        if "sentiments" in ville and ville["sentiments"]:
            sentiments_data.append({
                "ville": ville["ville_nom"],
                "positif": ville["sentiments"].get("positif_percent", 0),
                "neutre": ville["sentiments"].get("neutre_percent", 0),
                "negatif": ville["sentiments"].get("negatif_percent", 0)
            })

    stats_summary = {
        "total_villes": total_villes,
        "villes_traitees": villes_traitees,
        "pourcentage_traite": round(villes_traitees/total_villes*100, 2) if total_villes > 0 else 0,
        "total_mots_extraits": total_mots_extraits,
        "moyenne_mots_par_ville": round(total_mots_extraits/len(mots_villes), 2) if mots_villes else 0
    }

    if sentiments_data:
        df_sentiments = pd.DataFrame(sentiments_data)
        print("\n===== DISTRIBUTION DES SENTIMENTS =====")
        print(f"Sentiment positif moyen: {df_sentiments['positif'].mean():.2f}%")
        print(f"Sentiment neutre moyen: {df_sentiments['neutre'].mean():.2f}%")
        print(f"Sentiment négatif moyen: {df_sentiments['negatif'].mean():.2f}%")

        stats_summary["sentiment_positif_moyen"] = round(df_sentiments['positif'].mean(), 2)
        stats_summary["sentiment_neutre_moyen"] = round(df_sentiments['neutre'].mean(), 2)
        stats_summary["sentiment_negatif_moyen"] = round(df_sentiments['negatif'].mean(), 2)

        # Créer un graphique de la distribution des sentiments
        plt.figure(figsize=(10, 6))
        sns.histplot(data=df_sentiments, x="positif", kde=True)
        plt.title("Distribution du sentiment positif par ville")
        plt.xlabel("Pourcentage de sentiment positif")
        plt.ylabel("Nombre de villes")
        plt.savefig(f"{OUTPUT_DIR}/distribution_sentiment_positif.png")

    # Sauvegarder les statistiques en JSON
    with open(f"{OUTPUT_DIR}/stats_summary.json", 'w') as f:
        json.dump(stats_summary, f, indent=4)

    return stats_summary

def top_villes_par_sentiment():
    """Identifier les villes avec les sentiments les plus positifs et négatifs"""
    pipeline = [
        {"$project": {
            "ville_nom": 1,
            "positif": "$sentiments.positif_percent",
            "negatif": "$sentiments.negatif_percent"
        }},
        {"$match": {
            "positif": {"$exists": True},
            "negatif": {"$exists": True}
        }}
    ]

    resultats = list(db.mots_villes.aggregate(pipeline))
    df = pd.DataFrame(resultats)

    if not df.empty:
        # Top 5 villes les plus positives
        top_positives = df.sort_values("positif", ascending=False).head(5)
        # Top 5 villes les plus négatives
        top_negatives = df.sort_values("negatif", ascending=False).head(5)

        print("\n===== TOP 5 VILLES LES PLUS POSITIVES =====")
        print(tabulate(top_positives[["ville_nom", "positif"]], headers=["Ville", "% Positif"], tablefmt="pretty"))

        print("\n===== TOP 5 VILLES LES PLUS NÉGATIVES =====")
        print(tabulate(top_negatives[["ville_nom", "negatif"]], headers=["Ville", "% Négatif"], tablefmt="pretty"))

        # Sauvegarder en CSV
        top_positives[["ville_nom", "positif"]].to_csv(f"{OUTPUT_DIR}/top_villes_positives.csv", index=False)
        top_negatives[["ville_nom", "negatif"]].to_csv(f"{OUTPUT_DIR}/top_villes_negatives.csv", index=False)

def mots_frequents_global():
    """Identifier les mots les plus fréquents à l'échelle nationale"""
    mots_villes = list(db.mots_villes.find({}, {"mots": 1}))

    # Compteur global des mots
    mots_counter = {}
    for ville in mots_villes:
        if "mots" in ville:
            for mot_obj in ville["mots"]:
                mot = mot_obj.get("mot")
                poids = mot_obj.get("poids", 0)
                if mot in mots_counter:
                    mots_counter[mot] += poids
                else:
                    mots_counter[mot] = poids

    # Convertir en DataFrame pour l'affichage
    mots_df = pd.DataFrame([{"mot": mot, "poids": poids} for mot, poids in mots_counter.items()])

    if not mots_df.empty:
        top_mots = mots_df.sort_values("poids", ascending=False).head(50)

        print("\n===== TOP 20 MOTS LES PLUS FRÉQUENTS =====")
        print(tabulate(top_mots.head(20), headers=["Mot", "Poids global"], tablefmt="pretty"))

        # Sauvegarder en CSV
        top_mots.to_csv(f"{OUTPUT_DIR}/top_50_mots_frequents.csv", index=False)

        # Créer un nuage de mots
        plt.figure(figsize=(12, 8))
        top30 = top_mots.head(30)
        plt.bar(top30['mot'], top30['poids'])
        plt.xticks(rotation=45, ha='right')
        plt.title("Top 30 des mots les plus fréquents")
        plt.tight_layout()
        plt.savefig(f"{OUTPUT_DIR}/top30_mots_frequents.png")

def verifier_coherence():
    """Vérifier la cohérence entre les mots extraits et les sentiments"""
    # Prendre un échantillon de villes pour analyse
    echantillon = list(db.mots_villes.find({}).limit(5))

    resultats = []
    for ville in echantillon:
        ville_nom = ville.get("ville_nom", "Inconnue")
        mots = ville.get("mots", [])
        sentiments = ville.get("sentiments", {})

        # Vérifier les relations entre mots et sentiments
        print(f"\n===== COHÉRENCE POUR {ville_nom} =====")
        print(f"Sentiments: Positif {sentiments.get('positif_percent', 0):.1f}%, "
              f"Neutre {sentiments.get('neutre_percent', 0):.1f}%, "
              f"Négatif {sentiments.get('negatif_percent', 0):.1f}%")

        resultat_ville = {
            "ville_nom": ville_nom,
            "sentiments": sentiments,
            "top_mots": mots[:10] if mots else []
        }
        resultats.append(resultat_ville)

        # Afficher les 10 premiers mots
        if mots:
            print("Top 10 mots:")
            for i, mot in enumerate(mots[:10]):
                print(f"  {i+1}. {mot.get('mot')} (poids: {mot.get('poids')})")

    # Sauvegarder l'échantillon en JSON
    with open(f"{OUTPUT_DIR}/echantillon_coherence.json", 'w') as f:
        json.dump(resultats, f, indent=4, default=str)

if __name__ == "__main__":
    print("=======================================")
    print("VÉRIFICATION DU TRAITEMENT DES AVIS")
    print(f"Date d'exécution: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=======================================")

    stats = analyse_traitement()
    top_villes_par_sentiment()
    mots_frequents_global()
    verifier_coherence()

    print(f"\nVérification terminée! Résultats sauvegardés dans {OUTPUT_DIR}")

    # Créer un rapport de synthèse
    with open(f"{OUTPUT_DIR}/rapport_synthese.txt", 'w') as f:
        f.write("=======================================\n")
        f.write("SYNTHÈSE DU TRAITEMENT DES AVIS\n")
        f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=======================================\n\n")
        f.write(f"Total des villes: {stats['total_villes']}\n")
        f.write(f"Villes traitées: {stats['villes_traitees']} ({stats['pourcentage_traite']}%)\n")
        f.write(f"Total des mots extraits: {stats['total_mots_extraits']}\n")
        f.write(f"Moyenne de mots par ville: {stats['moyenne_mots_par_ville']}\n\n")

        if 'sentiment_positif_moyen' in stats:
            f.write("SENTIMENTS MOYENS:\n")
            f.write(f"Positif: {stats['sentiment_positif_moyen']}%\n")
            f.write(f"Neutre: {stats['sentiment_neutre_moyen']}%\n")
            f.write(f"Négatif: {stats['sentiment_negatif_moyen']}%\n")