import requests
import os
from dotenv import load_dotenv
import json
import asyncio
import pandas as pd
from models.produtosTodos import Produtos
from datetime import datetime

load_dotenv("../.env")
BASE_URL = "https://lepapon.com.br/api"
ENDPOINTS = {
    "pedidos": f"{BASE_URL}/pedidos"
}

API_KEY = os.getenv("MINHA_API_KEY")
HEADERS = {"x-api-key": API_KEY}
LOCAL_BASE_URL = "http://lepapon.api:3000/api"
SYNC_FILE = "last_sync.json"

fone = ''


def get_last_sync(endpoint):
    if not os.path.exists(SYNC_FILE):
        return None
    with open(SYNC_FILE, "r") as f:
        data = json.load(f)
    return data.get(endpoint)


def set_last_sync(endpoint, last_date):
    data = {}
    if os.path.exists(SYNC_FILE):
        with open(SYNC_FILE, "r") as f:
            data = json.load(f)
    data[endpoint] = last_date
    with open(SYNC_FILE, "w") as f:
        json.dump(data, f)



def baixar(endpoint):
    last_sync = get_last_sync(endpoint)
    url_remoto = ENDPOINTS[endpoint]
    params = {}
    if last_sync:
        params["updated_after"] = last_sync
    try:
        resp = requests.get(url_remoto, headers=HEADERS, params=params)
        resp.raise_for_status()
        dados = resp.json()
        if not dados:
            print(f"Nenhum dado encontrado para {endpoint}.")
            return
        #print(f"Baixados {len(dados)} registros de {endpoint}")
        return dados        
    except Exception as e:
        print(f"Erro ao processar {endpoint}: {e}")


def buscar_numero_pedido(fone):
    """Busca o número do pedido (id) pelo telefone na API local."""
    url = f"{LOCAL_BASE_URL}/numpedidoexist/{fone}"
    try:
        resp = requests.get(url)
        
        resp.raise_for_status()
        data = resp.json()
        # Se retornar uma lista, pega o primeiro id
        return data        
    except Exception as e:
        return None


def registrar_numero_pedido(payload):
    """Registra um novo número de pedido na API local usando a rota /numpedidos (POST)."""
    url = f"{LOCAL_BASE_URL}/numpedidos"
    try:
        resp = requests.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        print(f"Número de pedido registrado com sucesso: {data}")
        return data
    except Exception as e:
        print(f"Erro ao registrar número de pedido: {e}")
        return None


def buscar_cliente_por_fone(fone):
    """Busca um cliente pelo telefone na API local usando a rota /clienteexist."""
    url = f"{LOCAL_BASE_URL}/clienteexist/{fone}"
    try:
        resp = requests.get(url)
        
        resp.raise_for_status()
        data = resp.json()
        # Se retornar uma lista, pega o primeiro cliente
        if isinstance(data, list) and data:
            return data[0]
        elif isinstance(data, dict):
            return data
        else:
            return None
    except Exception as e:
        # Só mostra erro se não for 404
        print(f"Erro ao buscar cliente para o telefone {fone}: {e}")
        return None


def registrar_ordem_pedido(payload):
    """Registra uma nova ordem de pedido na API local usando a rota /orderpedidos (POST)."""
    url = f"{LOCAL_BASE_URL}/orderpedidos"
    try:
        resp = requests.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        #print(f"Ordem de pedido registrada com sucesso: {data}")
        return data
    except Exception as e:
        print(f"Erro ao registrar ordem de pedido: {e}")
        return None


def salvar_pedido_local(endpoint, item):
    """Salva um pedido no servidor local."""
    url_local = f"{LOCAL_BASE_URL}/{endpoint}"
    try:
        r = requests.post(url_local, json=item)
        r.raise_for_status()
        #print(f"Pedido salvo localmente: {r.json()}")
    except Exception as e:
        print(f"Erro ao salvar pedido localmente: {e} - Payload: {item}")


def async_baixar(endpoint):
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, baixar, endpoint)

def async_buscar_numero_pedido(fone):
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, buscar_numero_pedido, fone)

def async_registrar_numero_pedido(payload):
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, registrar_numero_pedido, payload)

def async_buscar_cliente_por_fone(fone):
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, buscar_cliente_por_fone, fone)

def async_registrar_ordem_pedido(payload):
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, registrar_ordem_pedido, payload)

def async_salvar_pedido_local(endpoint, item):
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, salvar_pedido_local, endpoint, item)

async def pedido_existe_localmente(pedido_payload, numPedido=None):
    """Verifica se o pedido já existe no servidor local para evitar duplicidade."""
    # Verifica duplicidade em pedidos temporários pelo telefone
    url_temp = f"{LOCAL_BASE_URL}/pedidoexist/{numPedido}"
    try:
        resp_temp = requests.get(url_temp)
        resp_temp.raise_for_status()
        pedidos_temp = resp_temp.json()
        # Verifica se já existe pedido com mesma data e hora
        existe_temp = any(
            p.get('data') == pedido_payload['data'] and p.get('hora') == pedido_payload['hora'] for p in pedidos_temp
        )
        if existe_temp:
            #print(f"Pedido temporário já registrado para fone {pedido_payload}. Não será duplicado.")
            return True
        else:
            return False
    except Exception as e:
        print(f"Erro ao buscar pedidos temporários: {e}")

def async_pedido_existe_localmente(pedido_payload, numPedido=None):
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, lambda: asyncio.run(pedido_existe_localmente(pedido_payload, numPedido)))

def formatar_data(data):
    try:
        return datetime.fromisoformat(data.replace('Z', '+00:00')).strftime('%Y-%m-%d')
    except Exception:
        return data

def formatar_hora(hora):
    try:
        if 'T' in hora:
            return datetime.fromisoformat(hora.replace('Z', '+00:00')).strftime('%H:%M:%S')
        else:
            return hora if len(hora.split(':')) == 3 else hora + ':00'
    except Exception:
        return hora

def montar_pedido_payload(id_cliente, numPedido, idOrderPedido, pedido, data, hora):
    return {
        "id_cliente": id_cliente,
        "numPedido": numPedido,
        "idOrderPedido": idOrderPedido,
        "id_Prod": pedido.get('id_Prod'),
        "qtd": pedido.get('qtd'),
        "observ": pedido.get('observ', ''),
        "V_unit": pedido.get('Valor_Prod'),
        "data": formatar_data(data),
        "hora": formatar_hora(hora)
    }

async def processar_e_salvar_pedidos(pedidos, id_cliente, numPedido, idOrderPedido, hora_item, data, df_produtos=None):
    if df_produtos is not None and not df_produtos.empty:
        df_pedidos = pd.DataFrame(pedidos)
        df_merged = pd.merge(df_pedidos, df_produtos, left_on="id_Prod", right_on="id_Prod", how="left")
        for _, pedido in df_merged.iterrows():
            data_pedido = pedido.get('data', data)
            hora_pedido = pedido.get('hora', hora_item)
            payload = montar_pedido_payload(id_cliente, numPedido, idOrderPedido, pedido, data_pedido, hora_pedido)
            await async_salvar_pedido_local("pedidos", payload)
    else:
        print("DataFrame de produtos está vazio ou não foi fornecido. Não será possível processar os pedidos.")
            

async def main_async():
    from datetime import datetime
    produtos_api = Produtos()
    produtos = await asyncio.get_event_loop().run_in_executor(None, produtos_api.listar_produtos)
    df_produtos = pd.DataFrame(produtos) if produtos else pd.DataFrame()
    last_sync = get_last_sync("pedidos")
    #print(f"Última data sincronizada: {last_sync}")
    dados = await async_baixar("pedidos")
    #print(f"Dados baixados: {dados}")
    if not dados:
        print("Nenhum dado encontrado.")
        return
    for item in dados:
        data_item = str(item['data'])
        hora_item = str(item['hora'])
        datahora_item = f"{data_item}T{hora_item}"
        if last_sync and datahora_item <= last_sync:
            continue
        data_object = datetime.fromisoformat(data_item.replace("Z", "+00:00"))
        data = data_object.strftime("%Y-%m-%d")
        fone_exist = await async_buscar_numero_pedido(item['fone'])
        cliente_exist = await async_buscar_cliente_por_fone(item['fone'])
        if fone_exist is None:
            if cliente_exist:
                payload = {
                    "nome": cliente_exist['nome'],
                    "id_cliente": cliente_exist['id'],
                    "data": data,
                    "hora": item['hora'],
                    "fone": item['fone']
                }
                new_num_pedido = await async_registrar_numero_pedido(payload)
                if new_num_pedido is not None and 'id' in new_num_pedido:
                    new_ordem_payload = {
                        "id_cliente": cliente_exist['id'],
                        "numPedido": new_num_pedido['id'],
                        "hora": item['hora'],
                    }
                    order = await async_registrar_ordem_pedido(new_ordem_payload)
                    pedidos_do_fone = [p for p in dados if p.get('fone') == item['fone'] and f"{str(p['data'])}T{str(p['hora'])}" == datahora_item]
                    if order is not None and 'id' in order:
                        await processar_e_salvar_pedidos(pedidos_do_fone, cliente_exist['id'], new_num_pedido['id'], order['id'], hora_item, data, df_produtos)
                    else:
                        print(f"Falha ao registrar ordem de pedido para cliente {cliente_exist['id']}.")
                else:
                    print(f"Falha ao registrar número de pedido para cliente {cliente_exist['id']}.")
            elif cliente_exist is None:
                payload = {
                    "nome": item['nome'],
                    "id_cliente": 13,
                    "fone": item['fone'],
                    "data": data,
                    "hora": item['hora']
                }
                new_num_pedido = await async_registrar_numero_pedido(payload)
                if new_num_pedido is not None and 'id' in new_num_pedido:
                    new_ordem_payload = {
                        "id_cliente": 13,
                        "numPedido": new_num_pedido['id'],
                        "hora": item['hora'],
                    }
                    order = await async_registrar_ordem_pedido(new_ordem_payload)
                    pedidos_do_fone = [p for p in dados if p.get('fone') == item['fone'] and f"{str(p['data'])}T{str(p['hora'])}" == datahora_item]
                    if order is not None and 'id' in order:
                        await processar_e_salvar_pedidos(pedidos_do_fone, 13, new_num_pedido['id'], order['id'], hora_item, data, df_produtos)
                    else:
                        print(f"Falha ao registrar ordem de pedido para cliente 13.")
                else:
                    print(f"Falha ao registrar número de pedido para cliente 13.")
                break
        elif fone_exist:
            new_ordem_payload = {
                "id_cliente": fone_exist['id_cliente'],
                "numPedido": fone_exist['id'],
                "hora": item['hora'],
            }
            pedidos_do_fone = [p for p in dados if p.get('fone') == item['fone'] and f"{str(p['data'])}T{str(p['hora'])}" == datahora_item]
            existe = False
            for pedido in pedidos_do_fone:
                existe = await async_pedido_existe_localmente(pedido, fone_exist['id'])
                if existe:
                    continue
                if not existe:
                    order = await async_registrar_ordem_pedido(new_ordem_payload)
                    if order is not None and 'id' in order:
                        await processar_e_salvar_pedidos(pedidos_do_fone, fone_exist['id_cliente'], fone_exist['id'], order['id'], hora_item, data, df_produtos)
                    else:
                        print(f"Falha ao registrar ordem de pedido para cliente {fone_exist['id_cliente']}.")
            
        set_last_sync("pedidos", datahora_item)
        #print(f"Última sincronização atualizada para {datahora_item}.")

async def loop_baixar_pedidos_async():
    while True:
        try:
            await main_async()
        except Exception as e:
            print(f"Erro na automação de download de pedidos: {e}")
        await asyncio.sleep(20)

if __name__ == "__main__":
    asyncio.run(loop_baixar_pedidos_async())
