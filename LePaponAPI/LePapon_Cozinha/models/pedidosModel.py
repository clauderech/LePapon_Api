import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://lepapon.api/api/pedidos"


class PedidoAPI:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        

    def criar_pedido(self, data):
        try:
            resp = requests.post(self.base_url, json=data)
            resp.raise_for_status()
            #print("Criar pedido:", resp.status_code, resp.json())
            return resp.json()
        except requests.RequestException as e:
            print(f"Erro ao criar pedido: {e}")
            return None

    def listar_pedidos(self):
        try:
            resp = requests.get(self.base_url)
            resp.raise_for_status()
            #print("Listar pedidos:", resp.status_code, resp.json())
            return resp.json()
        except requests.RequestException as e:
            print(f"Erro ao listar pedidos: {e}")
            return None

    def buscar_pedido_por_id(self, id):
        try:
            resp = requests.get(f"{self.base_url}/{id}")
            resp.raise_for_status()
            print(f"Buscar pedido {id}:", resp.status_code, resp.json())
            return resp.json()
        except requests.RequestException as e:
            print(f"Erro ao buscar pedido {id}: {e}")
            return None

    def atualizar_pedido(self, id, data):
        try:
            resp = requests.put(f"{self.base_url}/{id}", json=data)
            resp.raise_for_status()
            #print(f"Atualizar pedido {id}:", resp.status_code, resp.json())
            return resp.json()
        except requests.RequestException as e:
            print(f"Erro ao atualizar pedido {id}: {e}")
            return None

    def deletar_pedido(self, id):
        try:
            resp = requests.delete(f"{self.base_url}/{id}")
            resp.raise_for_status()
            print(f"Deletar pedido {id}:", resp.status_code)
            return resp.status_code
        except requests.RequestException as e:
            print(f"Erro ao deletar pedido {id}: {e}")
            return None


