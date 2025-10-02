from datetime import datetime
from models.numpedidos_api import NumPedidosAPI
from models.ordempedidos_api import OrdemPedidosAPI
from typing import Tuple, Dict, Any

class OrderService:
    """Orquestra criação ou recuperação de numPedido e ordem."""
    def __init__(self, num_api: NumPedidosAPI, ordem_api: OrdemPedidosAPI):
        self.num_api = num_api
        self.ordem_api = ordem_api

    def ensure_order_for_client(self, client_id: str, nome: str, sobrenome: str, fone: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        pedidos = self.num_api.get_all() or []
        if isinstance(pedidos, dict):
            pedidos = [pedidos]
        pedido_exist = next((p for p in pedidos if str(p.get('nome')) == str(nome)), None)
        if not pedido_exist:
            novo = {
                'id_cliente': client_id,
                'nome': nome,
                'sobrenome': sobrenome,
                'fone': fone,
                'data': datetime.now().strftime('%Y-%m-%d'),
                'hora': datetime.now().strftime('%H:%M:%S')
            }
            pedido_id = self.num_api.create(novo)
            # Alguns endpoints podem retornar só id, outros dict; padroniza
            if isinstance(pedido_id, dict):
                pedido_exist = pedido_id
            else:
                # Best effort: re-obtem lista
                pedidos = self.num_api.get_all() or []
                if isinstance(pedidos, dict):
                    pedidos = [pedidos]
                pedido_exist = next((p for p in pedidos if str(p.get('id_cliente')) == str(client_id)), novo | {'id': pedido_id})
        # Garante numPedido id
        num_pedido_id = pedido_exist.get('id') if isinstance(pedido_exist, dict) else None

        ordens = self.ordem_api.get_all() or []
        if isinstance(ordens, dict):
            ordens = [ordens]
        ordem_exist = next((o for o in ordens if str(o.get('numPedido')) == str(num_pedido_id)), None)
        if not ordem_exist:
            nova_ordem_payload = {
                'numPedido': num_pedido_id,
                'id_cliente': client_id,
                'hora': datetime.now().strftime('%H:%M:%S'),
                'ativo': True
            }
            ordem_id = self.ordem_api.create(nova_ordem_payload)
            # Recarrega
            ordens = self.ordem_api.get_all() or []
            if isinstance(ordens, dict):
                ordens = [ordens]
            ordem_exist = next((o for o in ordens if str(o.get('numPedido')) == str(num_pedido_id)), nova_ordem_payload | {'id': ordem_id})
        return pedido_exist, ordem_exist
