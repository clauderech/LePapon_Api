import json
import os

_PEDIDOS_TEMP_PATH = os.path.join(os.path.dirname(__file__), '../storage/data/pedidos_temp.json')

def _load_pedidos_temp():
    if os.path.exists(_PEDIDOS_TEMP_PATH):
        with open(_PEDIDOS_TEMP_PATH, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except Exception:
                return []
    return []

def _save_pedidos_temp(lista):
    os.makedirs(os.path.dirname(_PEDIDOS_TEMP_PATH), exist_ok=True)
    with open(_PEDIDOS_TEMP_PATH, 'w', encoding='utf-8') as f:
        json.dump(lista, f, ensure_ascii=False, indent=2)

class PedidosTempLista:
    @staticmethod
    def get():
        return _load_pedidos_temp()

    @staticmethod
    def set(lista):
        _save_pedidos_temp(lista)

# Para compatibilidade com o restante do código
pedidosTemp = PedidosTempLista.get()

def add_pedido_temp(pedido):
    global pedidosTemp
    pedidosTemp = PedidosTempLista.get()
    pedidosTemp.append(pedido)
    PedidosTempLista.set(pedidosTemp)

def remove_pedido_temp(idx):
    global pedidosTemp
    pedidosTemp = PedidosTempLista.get()
    if 0 <= idx < len(pedidosTemp):
        pedidosTemp.pop(idx)
        PedidosTempLista.set(pedidosTemp)

def update_pedidos_temp(lista):
    global pedidosTemp
    PedidosTempLista.set(lista)
    pedidosTemp = PedidosTempLista.get()
