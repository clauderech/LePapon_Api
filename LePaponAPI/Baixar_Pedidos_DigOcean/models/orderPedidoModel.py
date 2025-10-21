import requests

BASE_URL = "http://lepapon.api/api/orderpedidos"

# Criar uma nova ordem de pedido
class OrderPedidoAPI:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        

    def criar_ordem_pedido(self, id_cliente, num_pedido, hora):
        data = {
            "id_cliente": id_cliente,
            "numPedido": num_pedido,
            "hora": hora
        }
        try:
            resp = requests.post(self.base_url, json=data)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            print(f"Erro ao criar ordemPedido: {e}")
            return None

    def listar_ordem_pedidos(self):
        try:
            resp = requests.get(self.base_url)
            resp.raise_for_status()
            #print("Listar ordemPedidos:", resp.status_code, resp.json())
            return resp.json()
        except requests.RequestException as e:
            print(f"Erro ao listar ordemPedidos: {e}")
            return None

    def buscar_ordem_pedido_por_id(self, id):
        try:
            resp = requests.get(f"{self.base_url}/{id}")
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            print(f"Erro ao buscar ordemPedido {id}: {e}")
            return None

    def atualizar_ordem_pedido(self, id, hora):
        data = {"hora": hora}
        try:
            resp = requests.put(f"{self.base_url}/{id}", json=data)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            print(f"Erro ao atualizar ordemPedido {id}: {e}")
            return None

    def deletar_ordem_pedido(self, id):
        try:
            resp = requests.delete(f"{self.base_url}/{id}")
            resp.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"Erro ao deletar ordemPedido {id}: {e}")
            return False

