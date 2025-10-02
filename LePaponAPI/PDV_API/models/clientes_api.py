from .base_api import BaseAPI

class ClientesAPI(BaseAPI):
    def __init__(self, base_url):
        super().__init__(base_url, "clientes")
