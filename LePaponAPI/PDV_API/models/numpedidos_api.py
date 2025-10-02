from .base_api import BaseAPI

class NumPedidosAPI(BaseAPI):
    def __init__(self, base_url):
        super().__init__(base_url, "numpedidos")
