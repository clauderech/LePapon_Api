import requests
import logging

logger = logging.getLogger(__name__)

class ClientesAPI:
    def __init__(self, base_url, timeout=10):
        """
        Inicializa a API de clientes.
        
        Args:
            base_url: URL base da API
            timeout: Timeout em segundos para as requisições (padrão: 10s)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout

    def get_all(self):
        try:
            response = requests.get(f"{self.base_url}/api/clientes", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao buscar todos os clientes: {e}")
            return None

    def get_by_id(self, id):
        try:
            response = requests.get(f"{self.base_url}/api/clientes/{id}", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao buscar cliente por ID {id}: {e}")
            return None

    def get_by_fone(self, fone):
        """Busca clientes pelo número de telefone."""
        try:
            response = requests.get(
                f"{self.base_url}/api/clientes/fone/{fone}", 
                timeout=self.timeout
            )
            response.raise_for_status()  # Lança uma exceção para respostas de erro (4xx ou 5xx)
            return response.json()
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout ao buscar cliente por fone {fone}: A requisição demorou mais de {self.timeout}s")
            return None
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Erro de conexão ao buscar cliente por fone {fone}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao buscar cliente por fone {fone}: {e}")
            return None

    def create(self, data):
        try:
            response = requests.post(f"{self.base_url}/api/clientes", json=data, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao criar cliente: {e}")
            return None

    def update(self, id, data):
        try:
            response = requests.put(f"{self.base_url}/api/clientes/{id}", json=data, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao atualizar cliente {id}: {e}")
            return None

    def delete(self, id):
        try:
            response = requests.delete(f"{self.base_url}/api/clientes/{id}", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao deletar cliente {id}: {e}")
            return None
