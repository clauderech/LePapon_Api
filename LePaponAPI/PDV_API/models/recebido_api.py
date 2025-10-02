import requests

class RecebidoAPI:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')

    def get_all(self):
        return requests.get(f"{self.base_url}/api/recebido").json()

    def get_by_id(self, id):
        return requests.get(f"{self.base_url}/api/recebido/{id}").json()

    def create(self, data):
        return requests.post(f"{self.base_url}/api/recebido", json=data).json()

    def update(self, id, data):
        return requests.put(f"{self.base_url}/api/recebido/{id}", json=data).json()
    
    def get_by_cliente_id(self, cliente_id):
        return requests.get(f"{self.base_url}/api/recebido/cliente/{cliente_id}").json()

    def delete(self, id):
        return requests.delete(f"{self.base_url}/api/recebido/{id}").json()
