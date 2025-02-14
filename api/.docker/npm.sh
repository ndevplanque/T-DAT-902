#!/bin/bash

# Exécute la commande npm avec tous les arguments passés au script
docker container run --rm -v "$(pwd)":/srv/app node:22 bash -c "cd /srv/app && npm $@"
