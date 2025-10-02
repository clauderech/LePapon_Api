from .base_api import BaseAPI

class PedidosTempAPI(BaseAPI):
    def __init__(self, base_url):
        super().__init__(base_url, "pedidos")
