import requests

class ControleSemanalAPI:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')

    def get_all(self):
        return requests.get(f"{self.base_url}/api/controle_semanal").json()

    def get_by_id(self, id):
        return requests.get(f"{self.base_url}/api/controle_semanal/{id}").json()

    def get_by_data(self, data):
        return requests.get(f"{self.base_url}/api/controle_semanal/data/{data}").json()

    def get_last(self):
        return requests.get(f"{self.base_url}/api/controle_semanal/last").json()
    
    def get_lastfive(self):
        return requests.get(f"{self.base_url}/api/controle_semanal/lastfive").json()

    def create(self, data):
        return requests.post(f"{self.base_url}/api/controle_semanal", json=data).json()

    def update(self, id, data):
        return requests.put(f"{self.base_url}/api/controle_semanal/{id}", json=data).json()

    def delete(self, id):
        return requests.delete(f"{self.base_url}/api/controle_semanal/{id}").json()
