import json
import logging
from typing import Optional, List, Dict, Any
from clientes_api import ClientesAPI 
from numPedidoModel import NumPedidoAPI
from orderPedidoModel import OrderPedidoAPI
from produtosTodos import Produtos
from pedidosModel import PedidoAPI
from datetime import datetime
import time

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constantes
API_BASE_URL = "https://lepapon.api"
ID_CLIENTE_SEM_CADASTRO = 13  # ID usado quando o cliente não possui cadastro no sistema
DELAY_NUM_PEDIDO = 3  # segundos
DELAY_ORDER_PEDIDO = 2  # segundos
DELAY_ITEM_PEDIDO = 1  # segundo

# Inicialização das APIs
client = ClientesAPI(API_BASE_URL)
num_pedido_api = NumPedidoAPI()
order_pedido_api = OrderPedidoAPI()
pedido_api = PedidoAPI()
produtos_api = Produtos()


def _parse_data(raw_data: Optional[str]) -> Optional[str]:
    """
    Converte diferentes formatos de data para o formato padrão YYYY-MM-DD.
    
    Args:
        raw_data: String contendo a data em diversos formatos possíveis
        
    Returns:
        String no formato YYYY-MM-DD ou None se não conseguir converter
    """
    if not raw_data:
        return None
    
    formatos = [
        "%Y-%m-%dT%H:%M:%S.%fZ",  # ISO 8601 com milissegundos
        "%Y-%m-%d",               # Formato simples
    ]
    
    for formato in formatos:
        try:
            dt = datetime.strptime(raw_data, formato)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    # Tenta ISO com offset
    try:
        dt = datetime.fromisoformat(raw_data.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass
    
    # Fallback: pega os 10 primeiros caracteres
    if len(raw_data) >= 10:
        logger.warning(f"Usando fallback para data: {raw_data[:10]}")
        return raw_data[:10]
    
    logger.error(f"Não foi possível converter a data: {raw_data}")
    return None


def _validar_dados_pedido(pedido: Dict[str, Any]) -> bool:
    """
    Valida se um pedido contém os campos obrigatórios.
    
    Args:
        pedido: Dicionário com dados do pedido
        
    Returns:
        True se válido, False caso contrário
    """
    campos_obrigatorios = ['nome', 'fone', 'id_Prod', 'qtd']
    for campo in campos_obrigatorios:
        if campo not in pedido or pedido[campo] is None:
            logger.error(f"Campo obrigatório ausente ou nulo: {campo}")
            return False
    return True


def _criar_registros_pedido(
    id_cliente: int,
    nome: str,
    sobrenome: str,
    fone_cliente: str,
    data_pedido: Optional[str],
    hora_pedido: Optional[str],
    lista_pedidos: List[Dict[str, Any]]
) -> bool:
    """
    Cria os registros de número do pedido, ordem e itens individuais.
    
    Args:
        id_cliente: ID do cliente no sistema
        nome: Nome do cliente
        sobrenome: Sobrenome do cliente
        fone_cliente: Telefone do cliente
        data_pedido: Data do pedido no formato YYYY-MM-DD
        hora_pedido: Hora do pedido
        lista_pedidos: Lista com os itens do pedido
        
    Returns:
        True se todos os registros foram criados com sucesso, False caso contrário
    """
    try:
        # Criar número do pedido
        logger.info(f"Criando número do pedido para cliente ID: {id_cliente}")
        criar_num = num_pedido_api.criar_num_pedido({
            "id_cliente": id_cliente,
            "nome": nome,
            "sobrenome": sobrenome,
            "fone": fone_cliente,
            "data": data_pedido,
            "hora": hora_pedido
        })
        
        if not criar_num:
            logger.error("Falha ao criar número do pedido")
            return False
        
        time.sleep(DELAY_NUM_PEDIDO)
        
        # Criar ordem do pedido
        logger.info(f"Criando ordem do pedido: {criar_num.get('id')}")
        criar_order = order_pedido_api.criar_ordem_pedido(
            id_cliente,
            criar_num.get('id'),
            hora_pedido
        )
        
        if not criar_order:
            logger.error("Falha ao criar ordem do pedido")
            return False
        
        time.sleep(DELAY_ORDER_PEDIDO)
        
        # Criar itens individuais do pedido
        for i, pedido in enumerate(lista_pedidos, 1):
            logger.info(f"Processando item {i}/{len(lista_pedidos)} - Produto ID: {pedido.get('id_Prod')}")
            
            produto_info = produtos_api.obter_produto(pedido.get('id_Prod'))
            if not produto_info:
                logger.warning(f"Produto não encontrado: {pedido.get('id_Prod')}. Usando valor 0.0")
                v_unit = 0.0
            else:
                v_unit = produto_info.get('Valor_Prod', 0.0)
            
            time.sleep(DELAY_ITEM_PEDIDO)
            
            resultado = pedido_api.criar_pedido({
                "id_cliente": id_cliente,
                "numPedido": criar_num,
                "idOrderPedido": criar_order,
                "id_Prod": pedido.get('id_Prod'),
                "V_unit": v_unit,
                "qtd": pedido.get('qtd'),
                "observ": pedido.get('observ'),
                "data": data_pedido,
                "hora": hora_pedido
            })
            
            if not resultado:
                logger.error(f"Falha ao criar item {i} do pedido")
                return False
        
        logger.info(f"Pedido criado com sucesso! Total de itens: {len(lista_pedidos)}")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao criar registros do pedido: {str(e)}")
        return False


def processar_json(dados_json: str) -> Optional[Dict[str, Any]]:
    """
    Recebe uma string JSON com um ou mais pedidos de um único cliente.
    Extrai os dados do cliente do primeiro registro e itera sobre todos os pedidos.

    Args:
        dados_json: Uma string no formato JSON. Pode ser um objeto ou uma lista de objetos.

    Returns:
        Dicionário com informações do processamento:
        - 'sucesso': bool indicando se o processamento foi bem-sucedido
        - 'pedidos': lista de pedidos processados
        - 'mensagem': mensagem descritiva do resultado
        Retorna None se ocorrer um erro crítico.
    """
    logger.info("Iniciando processamento de pedidos JSON")
    
    try:
        # Validação do tipo de entrada
        if not isinstance(dados_json, str):
            logger.error("O argumento deve ser uma string JSON")
            return {
                'sucesso': False,
                'pedidos': [],
                'mensagem': 'Erro: O argumento deve ser uma string JSON'
            }
        
        # Decodifica a string JSON
        dados = json.loads(dados_json)
        
        # Garante que estamos trabalhando com uma lista de pedidos
        if isinstance(dados, dict):
            lista_pedidos = [dados]
        elif isinstance(dados, list):
            lista_pedidos = dados
        else:
            logger.error("Formato do JSON inválido (não é objeto ou lista)")
            return {
                'sucesso': False,
                'pedidos': [],
                'mensagem': 'Erro: O formato do JSON não é um objeto ou uma lista'
            }

        if not lista_pedidos:
            logger.warning("Lista de pedidos está vazia")
            return {
                'sucesso': False,
                'pedidos': [],
                'mensagem': 'Aviso: A lista de pedidos está vazia'
            }

        # Validação do primeiro pedido
        primeiro_pedido = lista_pedidos[0]
        if not _validar_dados_pedido(primeiro_pedido):
            return {
                'sucesso': False,
                'pedidos': lista_pedidos,
                'mensagem': 'Erro: Dados do pedido inválidos ou incompletos'
            }

        # Extrai as informações do cliente e dados gerais do primeiro pedido
        nome_cliente = primeiro_pedido.get('nome', '')
        fone_cliente = primeiro_pedido.get('fone', '')
        raw_data = primeiro_pedido.get('data')
        data_pedido = _parse_data(raw_data)
        hora_pedido = primeiro_pedido.get('hora', '')
        
        logger.info(f"Processando pedido para: {nome_cliente} - Fone: {fone_cliente}")
        
        # Busca o cliente pelo telefone
        cliente = None
        try:
            cliente = client.get_by_fone(fone_cliente)
        except Exception as e:
            logger.error(f"Erro ao buscar cliente: {str(e)}")

        # Determina os dados do cliente a serem usados
        if cliente:
            logger.info(f"Cliente encontrado no sistema: {cliente.get('nome')} {cliente.get('sobrenome')}")
            id_cliente = cliente.get('id')
            nome = cliente.get('nome', '')
            sobrenome = cliente.get('sobrenome', '')
        else:
            logger.warning(f"Cliente não encontrado. Usando ID padrão {ID_CLIENTE_SEM_CADASTRO} (sem cadastro)")
            id_cliente = ID_CLIENTE_SEM_CADASTRO
            nome = nome_cliente or ''
            sobrenome = "_"

        # Cria os registros do pedido
        sucesso = _criar_registros_pedido(
            id_cliente=id_cliente,
            nome=nome,
            sobrenome=sobrenome,
            fone_cliente=fone_cliente,
            data_pedido=data_pedido,
            hora_pedido=hora_pedido,
            lista_pedidos=lista_pedidos
        )
        
        if sucesso:
            mensagem = f"Pedido processado com sucesso! {len(lista_pedidos)} item(ns) registrado(s)"
            logger.info(mensagem)
            return {
                'sucesso': True,
                'pedidos': lista_pedidos,
                'mensagem': mensagem
            }
        else:
            mensagem = "Falha ao processar o pedido"
            logger.error(mensagem)
            return {
                'sucesso': False,
                'pedidos': lista_pedidos,
                'mensagem': mensagem
            }
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON inválido: {str(e)}")
        return {
            'sucesso': False,
            'pedidos': [],
            'mensagem': f'Erro: A string fornecida não é um JSON válido - {str(e)}'
        }
    except Exception as e:
        logger.error(f"Erro inesperado ao processar pedidos: {str(e)}", exc_info=True)
        return {
            'sucesso': False,
            'pedidos': [],
            'mensagem': f'Erro inesperado: {str(e)}'
        }


