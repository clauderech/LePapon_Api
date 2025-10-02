import requests

class SubCategoriaBebidasAPI:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')

    def get_all(self):
        return requests.get(f"{self.base_url}/api/subcategoria_bebidas").json()

    def get_by_id(self, id):
        return requests.get(f"{self.base_url}/api/subcategoria_bebidas/{id}").json()

    def create(self, data):
        return requests.post(f"{self.base_url}/api/subcategoria_bebidas", json=data).json()

    def update(self, id, data):
        return requests.put(f"{self.base_url}/api/subcategoria_bebidas/{id}", json=data).json()

    def delete(self, id):
        return requests.delete(f"{self.base_url}/api/subcategoria_bebidas/{id}").json()
