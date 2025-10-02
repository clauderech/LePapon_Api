import requests

class RecebidoAPI:
    def get_sum_period(self, data_inicio, data_fim):
        """Busca o somatório dos recebidos de um período."""
        params = {"dataInicio": data_inicio, "dataFim": data_fim}
        return requests.get(f"{self.base_url}/api/recebido/sum/period", params=params).json()
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

    def delete(self, id):
        return requests.delete(f"{self.base_url}/api/recebido/{id}").json()

    def get_by_data(self, data):
        """Busca recebido por data (YYYY-MM-DD)."""
        return requests.get(f"{self.base_url}/api/recebido/data/{data}").json()

    def get_last6days_sum(self):
        """Busca o somatório dos recebidos dos últimos 6 dias."""
        return requests.get(f"{self.base_url}/api/recebido/sum/last6days").json()

    def get_last7days_sum(self):
        """Busca o somatório dos recebidos dos últimos 7 dias (excluindo hoje)."""
        return requests.get(f"{self.base_url}/api/recebido/sum/last7days").json()
