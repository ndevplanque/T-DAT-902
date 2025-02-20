FROM node:22

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers package.json et package-lock.json pour l'installation des dépendances
COPY package*.json ./

# Installer les dépendances de l'application
RUN npm install

# Copier tous les autres fichiers dans le conteneur, y compris le script .docker/npm.sh
COPY . .

# Donner les permissions d'exécution au script .docker/npm.sh
RUN chmod +x .docker/npm.sh

# Lancer l'application avec npm start
CMD ["npm", "start"]

# Exposer le port 3000
EXPOSE 3000
