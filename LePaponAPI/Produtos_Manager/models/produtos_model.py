import requests

class ProdutosModel:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')

    def listar_produtos(self):
        """Obtém a lista de produtos do endpoint."""
        try:
            response = requests.get(f"{self.base_url}/api/produtos")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao obter produtos: {e}")
            return None

    def obter_produto(self, produto_id):
        """Obtém os detalhes de um produto específico pelo ID."""
        try:
            response = requests.get(f"{self.base_url}/api/produtos/{produto_id}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao obter o produto {produto_id}: {e}")
            return None

    def criar_produto(self, dados_produto):
        """Cria um novo produto no endpoint."""
        try:
            response = requests.post(f"{self.base_url}/api/produtos", json=dados_produto)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao criar produto: {e}")
            return None

    def atualizar_produto(self, produto_id, dados_produto):
        """Atualiza os dados de um produto existente."""
        try:
            response = requests.put(f"{self.base_url}/api/produtos/{produto_id}", json=dados_produto)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao atualizar o produto {produto_id}: {e}")
            return None

    def deletar_produto(self, produto_id):
        """Remove um produto pelo ID."""
        try:
            response = requests.delete(f"{self.base_url}/api/produtos/{produto_id}")
            response.raise_for_status()
            return response.status_code == 204
        except requests.exceptions.RequestException as e:
            print(f"Erro ao deletar o produto {produto_id}: {e}")
            return False
