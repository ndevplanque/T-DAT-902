#!/usr/bin/env python3
import psycopg2
import json
import os
import logging
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import time

# Configuration du logging
logger = logging.getLogger()

def setup_logging():
    """Configure le logging avec les handlers appropriés"""
    output_dir = os.environ.get('OUTPUT_DIR', 'results')

    # Si le répertoire n'existe pas, créons-le
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
        except Exception as e:
            print(f"Erreur lors de la création du répertoire {output_dir}: {e}")
            output_dir = "/tmp"
            print(f"Utilisation du répertoire temporaire: {output_dir}")

    # Vérifier si on peut écrire dans ce répertoire
    log_file = os.path.join(output_dir, "properties_validation.log")
    try:
        with open(log_file, "a") as f:
            f.write("Test d'écriture du log\n")
    except Exception as e:
        print(f"Impossible d'écrire dans le fichier de log {log_file}: {e}")
        log_file = "/tmp/properties_validation.log"
        print(f"Utilisation du fichier de log: {log_file}")

    # Configurer le logging avec le fichier de log et la console
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def connect_to_postgres():
    """Connexion à PostgreSQL"""
    try:
        conn = psycopg2.connect(
            dbname=os.environ.get('POSTGRES_DB', 'gis_db'),
            user=os.environ.get('POSTGRES_USER', 'postgres'),
            password=os.environ.get('POSTGRES_PASSWORD', 'postgres'),
            host=os.environ.get('POSTGRES_HOST', 'postgres'),
            port=os.environ.get('POSTGRES_PORT', 5432)
        )
        logger.info("Connexion à PostgreSQL réussie")
        return conn
    except Exception as e:
        logger.error(f"Erreur de connexion à PostgreSQL: {e}")
        return None

def wait_for_aggregations_completion(conn, max_retries=30, retry_interval=10):
    """Attend que les agrégations soient terminées"""
    logger.info("Vérification de la disponibilité des agrégations properties...")
    
    for attempt in range(max_retries):
        try:
            with conn.cursor() as cur:
                # Vérifier que les tables d'agrégation contiennent des données
                cur.execute("SELECT COUNT(*) FROM properties_cities_stats")
                cities_count = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM properties_departments_stats")
                dept_count = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM properties_regions_stats")
                region_count = cur.fetchone()[0]
                
                if cities_count > 0 and dept_count > 0 and region_count > 0:
                    logger.info(f"Agrégations disponibles: {cities_count} villes, {dept_count} départements, {region_count} régions")
                    
                    # Vérifier les colonnes des tables pour débugger
                    for table_name in ['properties_cities_stats', 'properties_departments_stats', 'properties_regions_stats']:
                        cur.execute(f"""
                            SELECT column_name 
                            FROM information_schema.columns 
                            WHERE table_name = '{table_name}' 
                            AND column_name LIKE '%transaction%'
                        """)
                        columns = [row[0] for row in cur.fetchall()]
                        logger.info(f"Colonnes transactions dans {table_name}: {columns}")
                    
                    return True
                else:
                    logger.warning(f"Agrégations incomplètes (tentative {attempt+1}/{max_retries}): "
                                 f"villes={cities_count}, départements={dept_count}, régions={region_count}")
        except Exception as e:
            logger.warning(f"Erreur lors de la vérification (tentative {attempt+1}/{max_retries}): {e}")
        
        if attempt < max_retries - 1:
            logger.info(f"Nouvelle tentative dans {retry_interval} secondes...")
            time.sleep(retry_interval)
    
    logger.error("Agrégations non disponibles après le nombre maximum de tentatives")
    return False

def validate_data_consistency(conn):
    """Valide la cohérence des données entre les niveaux d'agrégation"""
    logger.info("Validation de la cohérence des données")
    validation_results = {}
    
    try:
        with conn.cursor() as cur:
            # Test 1: Vérifier que les totaux régionaux correspondent aux sommes départementales
            cur.execute("""
                SELECT 
                    r.region_id,
                    r.region_name,
                    r.nb_transactions_total as region_total,
                    SUM(d.nb_transactions_total) as dept_sum_total
                FROM properties_regions_stats r
                LEFT JOIN properties_departments_stats d ON r.region_id = d.region_id
                GROUP BY r.region_id, r.region_name, r.nb_transactions_total
                HAVING ABS(r.nb_transactions_total - SUM(d.nb_transactions_total)) > 0
            """)
            
            inconsistent_regions = cur.fetchall()
            validation_results['inconsistent_regions'] = len(inconsistent_regions)
            
            if inconsistent_regions:
                logger.warning(f"Incohérences détectées dans {len(inconsistent_regions)} régions")
                for region in inconsistent_regions[:5]:  # Afficher les 5 premières
                    logger.warning(f"  {region[1]}: régional={region[2]}, somme_depts={region[3]}")
            else:
                logger.info("✓ Cohérence région-département vérifiée")
            
            # Test 2: Vérifier que les totaux départementaux correspondent aux sommes des villes
            cur.execute("""
                SELECT 
                    d.department_id,
                    d.department_name,
                    d.nb_transactions_total as dept_total,
                    SUM(c.nb_transactions) as cities_sum_total
                FROM properties_departments_stats d
                LEFT JOIN properties_cities_stats c ON d.department_id = c.department_id
                GROUP BY d.department_id, d.department_name, d.nb_transactions_total
                HAVING ABS(d.nb_transactions_total - SUM(c.nb_transactions)) > 0
            """)
            
            inconsistent_depts = cur.fetchall()
            validation_results['inconsistent_departments'] = len(inconsistent_depts)
            
            if inconsistent_depts:
                logger.warning(f"Incohérences détectées dans {len(inconsistent_depts)} départements")
                for dept in inconsistent_depts[:5]:  # Afficher les 5 premiers
                    logger.warning(f"  {dept[1]}: départemental={dept[2]}, somme_villes={dept[3]}")
            else:
                logger.info("✓ Cohérence département-ville vérifiée")
            
            # Test 3: Vérifier les plages de prix
            cur.execute("""
                SELECT 
                    COUNT(*) as total_cities,
                    COUNT(CASE WHEN prix_moyen < 0 THEN 1 END) as negative_prices,
                    COUNT(CASE WHEN prix_moyen > 50000 THEN 1 END) as extreme_prices,
                    MIN(prix_moyen) as min_price,
                    MAX(prix_moyen) as max_price,
                    AVG(prix_moyen) as avg_price
                FROM properties_cities_stats
                WHERE prix_moyen IS NOT NULL
            """)
            
            price_stats = cur.fetchone()
            validation_results['price_validation'] = {
                'total_cities': price_stats[0],
                'negative_prices': price_stats[1],
                'extreme_prices': price_stats[2],
                'min_price': float(price_stats[3]) if price_stats[3] else None,
                'max_price': float(price_stats[4]) if price_stats[4] else None,
                'avg_price': float(price_stats[5]) if price_stats[5] else None
            }
            
            if price_stats[1] > 0:
                logger.warning(f"⚠ {price_stats[1]} villes ont des prix moyens négatifs")
            if price_stats[2] > 0:
                logger.warning(f"⚠ {price_stats[2]} villes ont des prix moyens > 50000€")
            
            logger.info(f"✓ Prix: min={price_stats[3]:.2f}€, max={price_stats[4]:.2f}€, moyenne={price_stats[5]:.2f}€")
            
    except Exception as e:
        logger.error(f"Erreur lors de la validation de cohérence: {e}")
        validation_results['error'] = str(e)
    
    return validation_results

def generate_statistics_summary(conn):
    """Génère un résumé statistique des agrégations"""
    logger.info("Génération du résumé statistique")
    stats = {}
    
    try:
        with conn.cursor() as cur:
            # Statistiques générales par niveau
            tables = [
                ('cities', 'properties_cities_stats', 'nb_transactions'),
                ('departments', 'properties_departments_stats', 'nb_transactions_total'),
                ('regions', 'properties_regions_stats', 'nb_transactions_total')
            ]
            
            for level, table, trans_col in tables:
                try:
                    cur.execute(f"""
                        SELECT 
                            COUNT(*) as count,
                            AVG({trans_col}) as avg_transactions,
                            MIN({trans_col}) as min_transactions,
                            MAX({trans_col}) as max_transactions,
                            AVG(prix_moyen) as avg_price,
                            MIN(prix_moyen) as min_price,
                            MAX(prix_moyen) as max_price
                        FROM {table}
                        WHERE {trans_col} > 0
                    """)
                    
                    result = cur.fetchone()
                    stats[level] = {
                        'count': result[0],
                        'avg_transactions': float(result[1]) if result[1] else 0,
                        'min_transactions': result[2] if result[2] else 0,
                        'max_transactions': result[3] if result[3] else 0,
                        'avg_price': float(result[4]) if result[4] else 0,
                        'min_price': float(result[5]) if result[5] else 0,
                        'max_price': float(result[6]) if result[6] else 0
                    }
                    
                    logger.info(f"✓ {level.title()}: {result[0]} entités, "
                               f"prix moyen: {result[4]:.2f}€, "
                               f"transactions moyennes: {result[1]:.1f}")
                except Exception as e:
                    logger.error(f"Erreur lors du traitement de {level}: {e}")
                    # Rollback la transaction pour permettre aux requêtes suivantes de fonctionner
                    conn.rollback()
                    stats[level] = {'error': str(e)}
            
            # Top 10 villes par nombre de transactions
            try:
                cur.execute("""
                    SELECT city_name, nb_transactions, prix_moyen, prix_m2_moyen
                    FROM properties_cities_stats
                    ORDER BY nb_transactions DESC
                    LIMIT 10
                """)
                
                top_cities = []
                for row in cur.fetchall():
                    top_cities.append({
                        'name': row[0],
                        'transactions': row[1],
                        'avg_price': float(row[2]) if row[2] else 0,
                        'avg_price_m2': float(row[3]) if row[3] else 0
                    })
                
                stats['top_cities_by_transactions'] = top_cities
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des top villes par transactions: {e}")
                conn.rollback()
            
            # Top 10 villes par prix moyen
            try:
                cur.execute("""
                    SELECT city_name, nb_transactions, prix_moyen, prix_m2_moyen
                    FROM properties_cities_stats
                    WHERE prix_moyen IS NOT NULL
                    ORDER BY prix_moyen DESC
                    LIMIT 10
                """)
                
                top_cities_price = []
                for row in cur.fetchall():
                    top_cities_price.append({
                        'name': row[0],
                        'transactions': row[1],
                        'avg_price': float(row[2]) if row[2] else 0,
                        'avg_price_m2': float(row[3]) if row[3] else 0
                    })
                
                stats['top_cities_by_price'] = top_cities_price
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des top villes par prix: {e}")
                conn.rollback()
            
            # Top départements par transactions
            try:
                cur.execute("""
                    SELECT d.name, pds.nb_transactions_total, pds.prix_moyen, pds.nb_villes_avec_transactions
                    FROM properties_departments_stats pds
                    JOIN departments d ON pds.department_id = d.department_id
                    WHERE pds.nb_transactions_total > 0
                    ORDER BY pds.nb_transactions_total DESC
                    LIMIT 10
                """)
                stats['top_departments_by_transactions'] = [
                    {
                        'name': row[0],
                        'transactions': row[1],
                        'avg_price': float(row[2]) if row[2] else 0,
                        'nb_cities': row[3]
                    }
                    for row in cur.fetchall()
                ]
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des top départements: {e}")
                conn.rollback()
            
    except Exception as e:
        logger.error(f"Erreur lors de la génération des statistiques: {e}")
        stats['error'] = str(e)
        # Rollback pour permettre aux requêtes suivantes de fonctionner
        conn.rollback()
    
    return stats

def create_visualizations(conn):
    """Crée des visualisations des données agrégées"""
    logger.info("Création des visualisations")
    output_dir = os.environ.get('OUTPUT_DIR', 'results')
    
    # S'assurer qu'on commence avec une transaction propre
    try:
        conn.rollback()
    except:
        pass
    
    try:
        with conn.cursor() as cur:
            # Graphique 1: Distribution des prix par région
            try:
                cur.execute("""
                    SELECT region_name, prix_moyen, nb_transactions_total
                    FROM properties_regions_stats
                    WHERE prix_moyen IS NOT NULL
                    ORDER BY prix_moyen DESC
                """)
                
                regions_data = cur.fetchall()
                if regions_data:
                    df_regions = pd.DataFrame(regions_data, columns=['Region', 'Prix_Moyen', 'Nb_Transactions'])
                    
                    plt.figure(figsize=(12, 8))
                    bars = plt.bar(range(len(df_regions)), df_regions['Prix_Moyen'])
                    plt.title('Prix Moyen des Propriétés par Région')
                    plt.xlabel('Régions')
                    plt.ylabel('Prix Moyen (€)')
                    plt.xticks(range(len(df_regions)), df_regions['Region'], rotation=45, ha='right')
                    
                    # Colorier les barres selon le nombre de transactions
                    max_transactions = df_regions['Nb_Transactions'].max()
                    for i, bar in enumerate(bars):
                        intensity = df_regions.iloc[i]['Nb_Transactions'] / max_transactions
                        bar.set_color(plt.cm.viridis(intensity))
                    
                    plt.tight_layout()
                    plt.savefig(os.path.join(output_dir, 'prix_regions.png'), dpi=300, bbox_inches='tight')
                    plt.close()
                    logger.info("✓ Graphique prix par région créé")
                else:
                    logger.warning("Aucune donnée de région disponible pour la visualisation")
            except Exception as e:
                logger.error(f"Erreur lors de la création du graphique des prix par région: {e}")
                conn.rollback()
            
            # Graphique 2: Relation prix vs nombre de transactions (départements)
            try:
                cur.execute("""
                    SELECT department_name, prix_moyen, nb_transactions_total
                    FROM properties_departments_stats
                    WHERE prix_moyen IS NOT NULL AND nb_transactions_total > 10
                    ORDER BY nb_transactions_total DESC
                    LIMIT 50
                """)
                
                dept_data = cur.fetchall()
                if dept_data:
                    df_dept = pd.DataFrame(dept_data, columns=['Departement', 'Prix_Moyen', 'Nb_Transactions'])
                    
                    plt.figure(figsize=(12, 8))
                    plt.scatter(df_dept['Nb_Transactions'], df_dept['Prix_Moyen'], alpha=0.6)
                    plt.xlabel('Nombre de Transactions')
                    plt.ylabel('Prix Moyen (€)')
                    plt.title('Relation Prix vs Nombre de Transactions (Top 50 Départements)')
                    
                    # Ajouter des labels pour les points extrêmes
                    for i, row in df_dept.iterrows():
                        if row['Prix_Moyen'] > df_dept['Prix_Moyen'].quantile(0.9) or row['Nb_Transactions'] > df_dept['Nb_Transactions'].quantile(0.9):
                            plt.annotate(row['Departement'], (row['Nb_Transactions'], row['Prix_Moyen']), 
                                       xytext=(5, 5), textcoords='offset points', fontsize=8)
                    
                    plt.tight_layout()
                    plt.savefig(os.path.join(output_dir, 'prix_vs_transactions_departements.png'), dpi=300, bbox_inches='tight')
                    plt.close()
                    logger.info("✓ Graphique relation prix-transactions créé")
                else:
                    logger.warning("Aucune donnée de département disponible pour la visualisation")
            except Exception as e:
                logger.error(f"Erreur lors de la création du graphique prix-transactions: {e}")
                conn.rollback()
            
            # Graphique 3: Distribution des surfaces
            try:
                cur.execute("""
                    SELECT surface_bati_moyenne, surface_terrain_moyenne, nb_transactions
                    FROM properties_cities_stats
                    WHERE surface_bati_moyenne IS NOT NULL AND surface_terrain_moyenne IS NOT NULL
                    AND surface_bati_moyenne < 1000 AND surface_terrain_moyenne < 10000
                    LIMIT 1000
                """)
                
                surface_data = cur.fetchall()
                if surface_data:
                    df_surfaces = pd.DataFrame(surface_data, columns=['Surface_Bati', 'Surface_Terrain', 'Nb_Transactions'])
                    
                    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
                    
                    ax1.hist(df_surfaces['Surface_Bati'], bins=50, alpha=0.7, color='skyblue')
                    ax1.set_xlabel('Surface Bâtie Moyenne (m²)')
                    ax1.set_ylabel('Nombre de Villes')
                    ax1.set_title('Distribution des Surfaces Bâties')
                    
                    ax2.hist(df_surfaces['Surface_Terrain'], bins=50, alpha=0.7, color='lightgreen')
                    ax2.set_xlabel('Surface Terrain Moyenne (m²)')
                    ax2.set_ylabel('Nombre de Villes')
                    ax2.set_title('Distribution des Surfaces de Terrain')
                    
                    plt.tight_layout()
                    plt.savefig(os.path.join(output_dir, 'distribution_surfaces.png'), dpi=300, bbox_inches='tight')
                    plt.close()
                    logger.info("✓ Graphique distribution surfaces créé")
                else:
                    logger.warning("Aucune donnée de surface disponible pour la visualisation")
            except Exception as e:
                logger.error(f"Erreur lors de la création du graphique des surfaces: {e}")
                conn.rollback()
                
    except Exception as e:
        logger.error(f"Erreur générale lors de la création des visualisations: {e}")
        try:
            conn.rollback()
        except:
            pass

def generate_validation_report(validation_results, stats):
    """Génère un rapport HTML de validation"""
    logger.info("Génération du rapport de validation")
    output_dir = os.environ.get('OUTPUT_DIR', 'results')
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Rapport de Validation - Agrégations Properties</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .header {{ background-color: #f0f0f0; padding: 20px; text-align: center; }}
            .section {{ margin: 20px 0; }}
            .success {{ color: green; }}
            .warning {{ color: orange; }}
            .error {{ color: red; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Rapport de Validation - Agrégations Properties</h1>
            <p>Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="section">
            <h2>Résumé de la Validation</h2>
            <ul>
                <li>Régions incohérentes: <span class="{'error' if validation_results.get('inconsistent_regions', 0) > 0 else 'success'}">{validation_results.get('inconsistent_regions', 0)}</span></li>
                <li>Départements incohérents: <span class="{'error' if validation_results.get('inconsistent_departments', 0) > 0 else 'success'}">{validation_results.get('inconsistent_departments', 0)}</span></li>
                <li>Prix négatifs: <span class="{'warning' if validation_results.get('price_validation', {}).get('negative_prices', 0) > 0 else 'success'}">{validation_results.get('price_validation', {}).get('negative_prices', 0)}</span></li>
                <li>Prix extrêmes (>50k€): <span class="{'warning' if validation_results.get('price_validation', {}).get('extreme_prices', 0) > 0 else 'success'}">{validation_results.get('price_validation', {}).get('extreme_prices', 0)}</span></li>
            </ul>
        </div>
        
        <div class="section">
            <h2>Statistiques par Niveau</h2>
            <table>
                <tr><th>Niveau</th><th>Nombre d'entités</th><th>Prix moyen</th><th>Transactions moyennes</th></tr>
    """
    
    for level in ['cities', 'departments', 'regions']:
        if level in stats:
            s = stats[level]
            html_content += f"""
                <tr>
                    <td>{level.title()}</td>
                    <td>{s['count']}</td>
                    <td>{s['avg_price']:.2f}€</td>
                    <td>{s['avg_transactions']:.1f}</td>
                </tr>
            """
    
    html_content += """
            </table>
        </div>
        
        <div class="section">
            <h2>Top 10 Villes par Nombre de Transactions</h2>
            <table>
                <tr><th>Ville</th><th>Transactions</th><th>Prix Moyen</th><th>Prix/m²</th></tr>
    """
    
    for city in stats.get('top_cities_by_transactions', []):
        html_content += f"""
            <tr>
                <td>{city['name']}</td>
                <td>{city['transactions']}</td>
                <td>{city['avg_price']:.2f}€</td>
                <td>{city['avg_price_m2']:.2f}€/m²</td>
            </tr>
        """
    
    html_content += """
            </table>
        </div>
        
        <div class="section">
            <h2>Top 10 Villes par Prix Moyen</h2>
            <table>
                <tr><th>Ville</th><th>Transactions</th><th>Prix Moyen</th><th>Prix/m²</th></tr>
    """
    
    for city in stats.get('top_cities_by_price', []):
        html_content += f"""
            <tr>
                <td>{city['name']}</td>
                <td>{city['transactions']}</td>
                <td>{city['avg_price']:.2f}€</td>
                <td>{city['avg_price_m2']:.2f}€/m²</td>
            </tr>
        """
    
    html_content += """
            </table>
        </div>
        
        <div class="section">
            <h2>Top 10 Départements par Nombre de Transactions</h2>
            <table>
                <tr><th>Département</th><th>Transactions</th><th>Prix Moyen</th><th>Nb Villes</th></tr>
    """
    
    for dept in stats.get('top_departments_by_transactions', []):
        html_content += f"""
            <tr>
                <td>{dept['name']}</td>
                <td>{dept['transactions']}</td>
                <td>{dept['avg_price']:.2f}€</td>
                <td>{dept['nb_cities']}</td>
            </tr>
        """
    
    html_content += """
            </table>
        </div>
        
        <div class="section">
            <h2>Visualisations</h2>
            <p>Les graphiques suivants ont été générés :</p>
            <ul>
                <li>prix_regions.png - Prix moyen par région</li>
                <li>prix_vs_transactions_departements.png - Relation prix vs transactions</li>
                <li>distribution_surfaces.png - Distribution des surfaces</li>
            </ul>
        </div>
    </body>
    </html>
    """
    
    try:
        with open(os.path.join(output_dir, 'rapport_validation_properties.html'), 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info("✓ Rapport HTML généré")
    except Exception as e:
        logger.error(f"Erreur lors de la génération du rapport HTML: {e}")

def main():
    """Fonction principale de validation"""
    setup_logging()
    logger.info("Démarrage de la validation des agrégations properties")
    
    # Connexion à PostgreSQL
    pg_conn = connect_to_postgres()
    if pg_conn is None:
        logger.error("Impossible de se connecter à PostgreSQL")
        return
    
    try:
        # Attendre que les agrégations soient terminées
        if not wait_for_aggregations_completion(pg_conn):
            logger.error("Agrégations non disponibles, arrêt de la validation")
            return
        
        # Validation de la cohérence des données
        validation_results = validate_data_consistency(pg_conn)
        
        # Génération des statistiques
        stats = generate_statistics_summary(pg_conn)
        
        # Création des visualisations
        create_visualizations(pg_conn)
        
        # Génération du rapport
        generate_validation_report(validation_results, stats)
        
        # Sauvegarde des résultats en JSON
        output_dir = os.environ.get('OUTPUT_DIR', 'results')
        results = {
            'timestamp': datetime.now().isoformat(),
            'validation_results': validation_results,
            'statistics': stats
        }
        
        with open(os.path.join(output_dir, 'validation_results_properties.json'), 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info("Validation terminée avec succès")
        
    except Exception as e:
        logger.error(f"Erreur lors de la validation: {e}")
    finally:
        if pg_conn:
            pg_conn.close()

if __name__ == "__main__":
    main()