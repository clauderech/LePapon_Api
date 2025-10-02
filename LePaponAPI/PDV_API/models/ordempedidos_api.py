from .base_api import BaseAPI
import requests

class OrdemPedidosAPI(BaseAPI):
    def __init__(self, base_url):
        super().__init__(base_url, "orderpedidos")

    def create(self, data):
        # Mantém comportamento especial retornando somente id
        resp = requests.post(self._url(), json=data)
        try:
            js = resp.json()
            return js.get('id') if isinstance(js, dict) else js
        except ValueError:
            return None
