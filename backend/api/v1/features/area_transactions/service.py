import v1.features.area_transactions.repository as repository
import logs

def area_transactions(entity, id):
    # Vérifier que l'entité est valide
    if entity not in ["cities"]:  # , "departments", "regions"]:
        raise AttributeError(
            "Les transactions ne sont disponibles que pour les 'cities'")  # , 'departments' ou 'regions'")

    ids = [id]

    # Aggréger les ventes des arrondissements pour Paris
    if entity == 'cities' and id == '75056':
        logs.info("Récupération des détails pour Paris")
        ids = [
            75101, 75102, 75103, 75104, 75105, 75106, 75107, 75108, 75109, 75110,
            75111, 75112, 75113, 75114, 75115, 75116, 75117, 75118, 75119, 75120
        ]

    # Aggréger les ventes des arrondissements pour Marseille
    if entity == 'cities' and id == '13055':
        ids = [
            13201, 13202, 13203, 13204, 13205, 13206, 13207, 13208,
            13209, 13210, 13211, 13212, 13213, 13214, 13215, 13216
        ]

    transactions = repository.get_transactions(entity, ids)

    return transactions
