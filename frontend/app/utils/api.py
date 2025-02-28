import os

def v1(endpoint):
    url = os.getenv('API_V1_URL')
    return f"{url}/{endpoint}"
