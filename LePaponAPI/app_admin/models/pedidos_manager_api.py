import requests
from datetime import datetime

class PedidosManager:
    """
    Classe utilitária para gerenciar pedidos temporários (carregar todos e deletar todos).
    """
    def __init__(self, base_url, api_key=None):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.endpoint = f"{self.base_url}/api/pedidos"

    def carregar_todos(self):
        """Retorna todos os pedidos temporários como lista de dicionários."""
        resp = requests.get(self.endpoint)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list):
                return data
            elif data:
                return [data]
            else:
                return []
        else:
            raise Exception(f"Erro ao carregar pedidos temp: {resp.status_code}")
        
    def deletar_todos_externo(self):
        """
        Deleta todos os pedidos no endpoint externo usando header API_KEY.
        """
        url = "https://lepapon.com.br/api/pedidos"
        headers = {"x-api-key": self.api_key}
        resp = requests.delete(url, headers=headers)
        if resp.status_code == 200 or resp.status_code == 204:
            return True
        else:
            raise Exception(f"Erro ao deletar pedidos externos: {resp.status_code} - {resp.text}")

    def deletar_todos(self):
        """Deleta todos os pedidos, todos numeros de pedidos e todas as ordens de pedidos."""
        endpoint = [f"{self.base_url}/api/numpedidos", f"{self.base_url}/api/orderpedidos", f"{self.base_url}/api/pedidos"]
        for ep in endpoint:
            requests.delete(ep)
        
        return True

    def transferir_para_vendas(self):
        """
        Transfere todos os pedidos temporários para vendas.
        Para cada pedido temp, cria uma venda correspondente via endpoint /api/vendas.
        Após transferir, deleta todos os pedidos temporários.
        """
        pedidos = self.carregar_todos()
        #print(pedidos)
        vendas_endpoint = f"{self.base_url}/api/vendas"
        vendas_criadas = []
        for pedido in pedidos:
            # Ajuste os campos conforme o modelo de vendas esperado pela sua API
            # Converte data de '2025-06-05T03:00:00.000Z' para 'YYYY-MM-DD'
            data_iso = pedido.get('data')
            if data_iso:
                try:
                    data_formatada = datetime.fromisoformat(data_iso.replace('Z', '+00:00')).date().isoformat()
                except Exception:
                    data_formatada = data_iso  # fallback se falhar a conversão
            else:
                data_formatada = None

            venda = {
                'id_Prod': pedido.get('id_Prod'),
                'qtd': pedido.get('qtd'),
                'data': data_formatada,
                'hora': pedido.get('hora'),
                'id_cliente': pedido.get('id_cliente') or pedido.get('idCliente'),
                'V_unit': pedido.get('V_unit')                
            }
            resp = requests.post(vendas_endpoint, json=venda)
            if resp.status_code == 200 or resp.status_code == 201:
                vendas_criadas.append(resp.json())
            else:
                # Se der erro, pode logar ou lançar exceção
                print(f"Erro ao transferir pedido {pedido.get('id_pedidos')}: {resp.status_code}")
        return vendas_criadas

    def transferir_para_crediario(self):
        """
        Transfere todos os pedidos temporários NÃO pagos (pago == 0) para crediário.
        Para cada pedido temp não pago, cria um registro correspondente via endpoint /api/crediario.
        Após transferir, deleta apenas os pedidos transferidos.
        """
        pedidos = self.carregar_todos()
        crediario_endpoint = f"{self.base_url}/api/crediario"
        crediarios_criados = []
        for pedido in pedidos:
            # Converte data de '2025-06-05T03:00:00.000Z' para 'YYYY-MM-DD'
            data_iso = pedido.get('data')
            if data_iso:
                try:
                    data_formatada = datetime.fromisoformat(data_iso.replace('Z', '+00:00')).date().isoformat()
                except Exception:
                    data_formatada = data_iso  # fallback se falhar a conversão
            else:
                data_formatada = None
            if pedido.get('pago', 0) == 0:
                sub_total = float(pedido.get('qtd', 0)) * float(pedido.get('V_unit', 0))
                crediario = {
                    'id_cliente': pedido.get('id_cliente'),
                    'id_Prod': pedido.get('id_Prod'),
                    'qtd': pedido.get('qtd'),
                    'sub_total': sub_total,
                    'data': data_formatada,
                    'hora': pedido.get('hora'),
                }
                resp = requests.post(crediario_endpoint, json=crediario)
                if resp.status_code == 200 or resp.status_code == 201:
                    crediarios_criados.append(resp.json())
                    # Deleta o pedido temp transferido
                    pedido_id = pedido.get('id_pedidos') or pedido.get('id')
                    if pedido_id:
                        requests.delete(f"{self.endpoint}/{pedido_id}")
                else:
                    print(f"Erro ao transferir pedido {pedido.get('id_pedidos')}: {resp.status_code}, {resp.text}")
        return crediarios_criados

    def atualizar_data_ontem(self):
        """
        Atualiza a data de todos os pedidos temporários para ontem.
        Utiliza o endpoint PATCH /api/pedidos/update-data-yesterday.
        """
        url = f"{self.base_url}/api/pedidos/update-data-yesterday"
        resp = requests.patch(url)
        if resp.status_code == 200 or resp.status_code == 204:
            return resp.json() if resp.content else {"message": "Data atualizada para ontem com sucesso"}
        else:
            raise Exception(f"Erro ao atualizar data: {resp.status_code} - {resp.text}")



