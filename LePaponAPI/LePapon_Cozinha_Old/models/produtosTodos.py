import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://lepapon.api:3000/api")
PRODUTOS_ENDPOINT = f"{BASE_URL}/produtostodos"

class Produtos:
    def __init__(self):
        self.endpoint = PRODUTOS_ENDPOINT

    def listar_produtos(self):
        try:
            resp = requests.get(self.endpoint)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Erro ao listar produtos: {e}")
            return None

    def obter_produto(self, produto_id):
        try:
            url = f"{self.endpoint}/{produto_id}"
            resp = requests.get(url)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Erro ao obter produto: {e}")
            return None

    def criar_produto(self, dados):
        try:
            resp = requests.post(self.endpoint, json=dados)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Erro ao criar produto: {e}")
            return None

    def atualizar_produto(self, produto_id, dados):
        try:
            url = f"{self.endpoint}/{produto_id}"
            resp = requests.put(url, json=dados)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Erro ao atualizar produto: {e}")
            return None

    def deletar_produto(self, produto_id):
        try:
            url = f"{self.endpoint}/{produto_id}"
            resp = requests.delete(url)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Erro ao deletar produto: {e}")
            return None
