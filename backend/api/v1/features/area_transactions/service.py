import v1.features.area_transactions.repository as repository


def area_transactions(entity, id):
    transactions = repository.get_transactions(entity, id)

    return transactions