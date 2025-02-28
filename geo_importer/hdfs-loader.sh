#!/bin/bash

# Configuration explicite de l'adresse HDFS - Correction des paramètres
export HADOOP_CONF_DIR=/etc/hadoop
export CORE_CONF_fs_defaultFS=hdfs://namenode:9000

# Force la configuration à être utilisée
echo "fs.defaultFS=hdfs://namenode:9000" > $HADOOP_CONF_DIR/core-site.xml.tmp
echo "<?xml version=\"1.0\"?>" > $HADOOP_CONF_DIR/core-site.xml
echo "<configuration>" >> $HADOOP_CONF_DIR/core-site.xml
echo "  <property>" >> $HADOOP_CONF_DIR/core-site.xml
echo "    <name>fs.defaultFS</name>" >> $HADOOP_CONF_DIR/core-site.xml
echo "    <value>hdfs://namenode:9000</value>" >> $HADOOP_CONF_DIR/core-site.xml
echo "  </property>" >> $HADOOP_CONF_DIR/core-site.xml
echo "</configuration>" >> $HADOOP_CONF_DIR/core-site.xml

# Attendre que le namenode soit prêt - avec timeout plus long
echo "Attente du démarrage du namenode..."
max_attempts=60  # Augmentation du nombre de tentatives
attempt=0
while [ $attempt -lt $max_attempts ]; do
    echo "Tentative $attempt/$max_attempts - Test de connexion à hdfs://namenode:9000"
    if hdfs dfs -ls hdfs://namenode:9000/ >/dev/null 2>&1; then
        echo "Namenode est prêt !"
        break
    fi

    attempt=$((attempt + 1))
    echo "Tentative $attempt/$max_attempts - Namenode pas encore prêt, nouvelle tentative dans 5 secondes..."
    sleep 5
done

if [ $attempt -eq $max_attempts ]; then
    echo "Échec de connexion au namenode après $max_attempts tentatives."
    exit 1
fi

# Test de connectivité explicite
echo "Test de ping du namenode..."
ping -c 3 namenode

# Créer le répertoire de données dans HDFS avec URL explicite
echo "Création du répertoire /data dans HDFS..."
hdfs dfs -mkdir -p hdfs://namenode:9000/data
if [ $? -ne 0 ]; then
    echo "Erreur lors de la création du répertoire /data"
    exit 1
fi

# Copier les fichiers GeoJSON dans HDFS avec vérification d'erreurs
echo "Copie des fichiers GeoJSON vers HDFS..."
for file in communes-1000m.geojson departements-1000m.geojson regions-1000m.geojson; do
    echo "Copie de $file vers HDFS..."
    if [ ! -f "/geojson_files/$file" ]; then
        echo "ATTENTION: Le fichier /geojson_files/$file n'existe pas!"
        ls -la /geojson_files/
        continue
    fi

    hdfs dfs -copyFromLocal -f /geojson_files/$file hdfs://namenode:9000/data/
    if [ $? -ne 0 ]; then
        echo "Erreur lors de la copie de $file vers HDFS"
        exit 1
    fi
    echo "Fichier $file copié avec succès."
done

echo "Vérification des fichiers dans HDFS:"
hdfs dfs -ls hdfs://namenode:9000/data/

echo "Fichiers GeoJSON chargés dans HDFS avec succès."

# Continuer à s'exécuter pour éviter que le conteneur ne s'arrête
echo "Script terminé, le conteneur reste actif pour faciliter le débogage"
tail -f /dev/null  # Garde le conteneur en vie