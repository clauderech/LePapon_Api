import requests

BASE_URL = "http://lepapon.api/api/numpedidos"


# Criar um novo numPedido
class NumPedidoAPI:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url        

    def criar_num_pedido(self, data):
        try:
            resp = requests.post(self.base_url, json=data, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            print(f"Erro ao criar numPedido: {e}")
            return None

    def listar_num_pedidos(self):
        try:
            resp = requests.get(self.base_url, timeout=10)
            resp.raise_for_status()
            #print("Listar numPedidos:", resp.status_code, resp.json())
            return resp.json()
        except requests.RequestException as e:
            print(f"Erro ao listar numPedidos: {e}")
            return None

    def buscar_num_pedido_por_id(self, id):
        try:
            resp = requests.get(f"{self.base_url}/{id}", timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            print(f"Erro ao buscar numPedido {id}: {e}")
            return None

    def atualizar_num_pedido(self, id, data):
        try:
            resp = requests.put(f"{self.base_url}/{id}", json=data, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            print(f"Erro ao atualizar numPedido {id}: {e}")
            return None

    def deletar_num_pedido(self, id):
        try:
            resp = requests.delete(f"{self.base_url}/{id}", timeout=10)
            resp.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"Erro ao deletar numPedido {id}: {e}")
            return False

