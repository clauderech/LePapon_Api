import requests

class ProdutosBebidasModel:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')

    def listar_produtos_bebidas(self):
        return requests.get(f"{self.base_url}/api/produtos_bebidas").json()

    def obter_produto_bebida(self, produto_id):
        return requests.get(f"{self.base_url}/api/produtos_bebidas/{produto_id}").json()

    def criar_produto_bebida(self, dados_produto):
        return requests.post(f"{self.base_url}/api/produtos_bebidas", json=dados_produto).json()

    def atualizar_produto_bebida(self, produto_id, dados_produto):
        return requests.put(f"{self.base_url}/api/produtos_bebidas/{produto_id}", json=dados_produto).json()

    def deletar_produto_bebida(self, produto_id):
        return requests.delete(f"{self.base_url}/api/produtos_bebidas/{produto_id}").json()
