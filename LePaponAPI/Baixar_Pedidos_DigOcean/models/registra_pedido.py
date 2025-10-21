import json
from LePaponAPI.app_admin.models.clientes_api import ClientesAPI
from numPedidoModel import NumPedidoAPI
from orderPedidoModel import OrderPedidoAPI
from pedidosModel import PedidoAPI
from datetime import datetime
import time

client = ClientesAPI("https://lepapon.api")
num_pedido_api = NumPedidoAPI()
order_pedido_api = OrderPedidoAPI()
pedido_api = PedidoAPI()


def processar_json(dados_json):
    """
    Recebe uma string JSON com um ou mais pedidos de um único cliente.
    Extrai os dados do cliente do primeiro registro e itera sobre todos os pedidos.

    Args:
        dados_json (str): Uma string no formato JSON. Pode ser um objeto ou uma lista de objetos.

    Returns:
        list: Uma lista de dicionários Python representando os pedidos, ou None se ocorrer um erro.
    """
    try:
        # Decodifica a string JSON
        dados = json.loads(dados_json)
        
        # Garante que estamos trabalhando com uma lista de pedidos
        if isinstance(dados, dict):
            lista_pedidos = [dados]
        elif isinstance(dados, list):
            lista_pedidos = dados
        else:
            print("Erro: O formato do JSON não é um objeto ou uma lista.")
            return None

        if not lista_pedidos:
            print("Aviso: A lista de pedidos está vazia.")
            return None

        # Extrai as informações do cliente e dados gerais do primeiro pedido
        primeiro_pedido = lista_pedidos[0]
        nome_cliente = primeiro_pedido.get('nome')
        fone_cliente = primeiro_pedido.get('fone')
        raw_data = primeiro_pedido.get('data')
        data_pedido = None
        if raw_data:
            try:
                # formato: 2025-10-21T03:00:00.000Z
                dt = datetime.strptime(raw_data, "%Y-%m-%dT%H:%M:%S.%fZ")
            except ValueError:
                try:
                    # tenta ISO com offset: 2025-10-21T03:00:00+00:00
                    dt = datetime.fromisoformat(raw_data)
                except ValueError:
                    try:
                        # formato simples: 2025-10-21
                        dt = datetime.strptime(raw_data, "%Y-%m-%d")
                    except ValueError:
                        # fallback: pega os 10 primeiros caracteres (YYYY-MM-DD)
                        data_pedido = raw_data[:10]
                        dt = None
            if dt:
                data_pedido = dt.strftime("%Y-%m-%d")
        else:
            data_pedido = None
        hora_pedido = primeiro_pedido.get('hora')
        cliente = client.get_by_fone(fone_cliente)

        criar_num = None
        criar_order = None

        if cliente:
            print(f"--- Dados do Cliente e Pedido ---\n")
            id_cliente = cliente.get('id')
            nome = cliente.get('nome')
            sobrenome = cliente.get('sobrenome')
            criar_num = num_pedido_api.criar_num_pedido({
                "id_cliente": id_cliente,
                "nome": nome,
                "sobrenome": sobrenome,
                "fone": fone_cliente,
                "data": data_pedido,
                "hora": hora_pedido
            })
            time.sleep(3)  # Simula um atraso de 3 segundo
            if criar_num:
                # criar_ordem_pedido espera os argumentos separados: id_cliente, num_pedido, hora
                order_pedido_api.criar_ordem_pedido(
                    id_cliente,
                    criar_num.get('id'),
                    hora_pedido
                )
        else:
            print("Cliente não encontrado.")
            criar_num = num_pedido_api.criar_num_pedido({
                "id_cliente": 13,
                "nome": nome_cliente,
                "sobrenome": "_",
                "fone": fone_cliente,
                "data": data_pedido,
                "hora": hora_pedido
            })
            time.sleep(3)  # Simula um atraso de 3 segundos
            
            if criar_num:
                criar_order = order_pedido_api.criar_ordem_pedido(
                    13,
                    criar_num.get('id'),
                    hora_pedido
                )

            # Itera sobre cada pedido na lista para extrair detalhes específicos
        
            for i, pedido in enumerate(lista_pedidos, 1):
                pedido_api.criar_pedido({
                    "id_cliente": 13,
                    "numPedido": criar_num,
                    "idOrderPedido": criar_order,
                    "id_Prod": pedido.get('id_Prod'),
                    "qtd": pedido.get('qtd'),
                    "observ": pedido.get('observ'),
                    "data": data_pedido,
                    "hora": hora_pedido
                })
                
            return lista_pedidos
        
    except json.JSONDecodeError:
        print("Erro: A string fornecida não é um JSON válido.")
        return None
    except TypeError:
        print("Erro: O argumento deve ser uma string.")
        return None


