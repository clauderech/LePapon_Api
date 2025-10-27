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
import threading
from functools import wraps

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Gerenciador de rate limiting mais elegante que substitui time.sleep()
    """
    def __init__(self):
        self._locks = {}
        self._last_call = {}
    
    def wait(self, operation_type: str, delay: float):
        """
        Implementa rate limiting para diferentes tipos de operação
        """
        if operation_type not in self._locks:
            self._locks[operation_type] = threading.Lock()
            self._last_call[operation_type] = 0
        
        with self._locks[operation_type]:
            current_time = time.time()
            time_since_last = current_time - self._last_call[operation_type]
            
            if time_since_last < delay:
                sleep_time = delay - time_since_last
                logger.debug(f"Rate limiting {operation_type}: aguardando {sleep_time:.2f}s")
                time.sleep(sleep_time)
            
            self._last_call[operation_type] = time.time()


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """
    Decorator para implementar retry logic em chamadas de API
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for tentativa in range(max_retries):
                try:
                    result = func(*args, **kwargs)
                    if result:  # Se o resultado é válido, retorna
                        return result
                    logger.warning(f"Tentativa {tentativa + 1}/{max_retries} falhou para {func.__name__}")
                except Exception as e:
                    last_exception = e
                    logger.warning(f"Tentativa {tentativa + 1}/{max_retries} gerou exceção em {func.__name__}: {str(e)}")
                
                if tentativa < max_retries - 1:  # Não aguarda na última tentativa
                    time.sleep(delay * (tentativa + 1))  # Backoff exponencial
            
            logger.error(f"Todas as {max_retries} tentativas falharam para {func.__name__}")
            if last_exception:
                raise last_exception
            return None
        return wrapper
    return decorator

# Constantes
API_BASE_URL = "http://lepapon.api"  # URL base da API (HTTP para desenvolvimento)
ID_CLIENTE_SEM_CADASTRO = 13  # ID usado quando o cliente não possui cadastro no sistema
DELAY_NUM_PEDIDO = 3.0  # segundos
DELAY_ORDER_PEDIDO = 2.0  # segundos  
DELAY_ITEM_PEDIDO = 1.0  # segundo
MAX_RETRIES = 3  # Número máximo de tentativas para operações críticas
RETRY_DELAY = 1.0  # Delay base para retry (com backoff exponencial)

# Inicialização do rate limiter
rate_limiter = RateLimiter()

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


def _sanitizar_string(value: Any) -> str:
    """
    Sanitiza strings removendo caracteres perigosos
    """
    if not isinstance(value, str):
        value = str(value) if value is not None else ""
    
    # Remove caracteres potencialmente perigosos
    caracteres_perigosos = ['<', '>', '"', "'", '&', '\n', '\r', '\t']
    for char in caracteres_perigosos:
        value = value.replace(char, '')
    
    return value.strip()


def _converter_e_validar_campo(campo: str, valor: Any) -> tuple:
    """
    Converte e valida um campo específico do pedido
    
    Args:
        campo: Nome do campo
        valor: Valor a ser validado/convertido
        
    Returns:
        Tupla (é_válido, valor_convertido)
    """
    try:
        if campo == 'nome':
            if not valor or not str(valor).strip():
                return False, None
            return True, str(valor).strip()
            
        elif campo == 'fone':
            if not valor or not str(valor).strip():
                return False, None
            return True, str(valor).strip()
            
        elif campo == 'id_Prod':
            # Aceita int, str que pode ser convertida para int
            if isinstance(valor, int):
                return valor > 0, valor
            elif isinstance(valor, str) and valor.strip().isdigit():
                convertido = int(valor.strip())
                return convertido > 0, convertido
            elif isinstance(valor, float) and valor.is_integer():
                convertido = int(valor)
                return convertido > 0, convertido
            else:
                return False, None
                
        elif campo == 'qtd':
            # Aceita int, float, str que pode ser convertida para float
            if isinstance(valor, (int, float)):
                return valor > 0, float(valor)
            elif isinstance(valor, str) and valor.strip():
                try:
                    convertido = float(valor.strip())
                    return convertido > 0, convertido
                except ValueError:
                    return False, None
            else:
                return False, None
                
    except Exception as e:
        logger.debug(f"Erro na conversão do campo {campo}: {str(e)}")
        return False, None
    
    return False, None


def _validar_dados_pedido(pedido: Dict[str, Any]) -> bool:
    """
    Valida se um pedido contém os campos obrigatórios com validação e conversão flexível de tipos.
    
    Args:
        pedido: Dicionário com dados do pedido
        
    Returns:
        True se válido, False caso contrário
    """
    if not isinstance(pedido, dict):
        logger.error("Pedido deve ser um dicionário")
        return False
    
    campos_obrigatorios = ['nome', 'fone', 'id_Prod', 'qtd']
    
    for campo in campos_obrigatorios:
        if campo not in pedido or pedido[campo] is None:
            logger.error(f"Campo obrigatório ausente ou nulo: {campo}")
            return False
        
        valor = pedido[campo]
        logger.debug(f"Validando campo {campo}: {valor} (tipo: {type(valor)})")
        
        # Converte e valida o campo
        is_valid, valor_convertido = _converter_e_validar_campo(campo, valor)
        
        if not is_valid:
            logger.error(f"Valor inválido para campo {campo}: {valor} (tipo: {type(valor)})")
            return False
        
        # Atualiza o valor no pedido com a versão convertida
        pedido[campo] = valor_convertido
        logger.debug(f"Campo {campo} convertido para: {valor_convertido} (tipo: {type(valor_convertido)})")
    
    return True


@retry_on_failure(max_retries=MAX_RETRIES, delay=RETRY_DELAY)
def _criar_numero_pedido(dados_pedido: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Cria o número do pedido com retry automático
    """
    return num_pedido_api.criar_num_pedido(dados_pedido)


@retry_on_failure(max_retries=MAX_RETRIES, delay=RETRY_DELAY)
def _criar_ordem_pedido(id_cliente: int, num_pedido_id: int, hora_pedido: str) -> Optional[Dict[str, Any]]:
    """
    Cria a ordem do pedido com retry automático
    """
    return order_pedido_api.criar_ordem_pedido(id_cliente, num_pedido_id, hora_pedido)


@retry_on_failure(max_retries=MAX_RETRIES, delay=RETRY_DELAY)
def _criar_item_pedido(dados_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Cria um item individual do pedido com retry automático
    """
    return pedido_api.criar_pedido(dados_item)


@retry_on_failure(max_retries=MAX_RETRIES, delay=RETRY_DELAY)
def _buscar_cliente_por_telefone(telefone: str) -> Optional[Dict[str, Any]]:
    """
    Busca cliente pelo telefone com retry automático.
    Usa o endpoint: clientes/fone/{fone}
    
    Args:
        telefone: Número de telefone do cliente
        
    Returns:
        Dados do cliente se encontrado, None caso contrário
    """
    telefone_sanitizado = _sanitizar_string(telefone)
    logger.info(f"Buscando cliente por telefone: {telefone_sanitizado}")
    
    try:
        cliente = client.get_by_fone(telefone_sanitizado)
        if cliente:
            logger.info(f"Cliente encontrado - ID: {cliente.get('id')}, Nome: {cliente.get('nome')} {cliente.get('sobrenome')}")
        else:
            logger.info(f"Nenhum cliente encontrado com o telefone: {telefone_sanitizado}")
        return cliente
    except Exception as e:
        logger.error(f"Erro ao buscar cliente por telefone {telefone_sanitizado}: {str(e)}")
        raise


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
    Cria os registros de número do pedido, ordem e itens individuais com melhorias de robustez.
    
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
        # Sanitizar dados de entrada
        nome_sanitizado = _sanitizar_string(nome)
        sobrenome_sanitizado = _sanitizar_string(sobrenome)
        fone_sanitizado = _sanitizar_string(fone_cliente)
        
        # Criar número do pedido com retry automático
        logger.info(f"Criando número do pedido para cliente ID: {id_cliente}")
        dados_num_pedido = {
            "id_cliente": id_cliente,
            "nome": nome_sanitizado,
            "sobrenome": sobrenome_sanitizado,
            "fone": fone_sanitizado,
            "data": data_pedido,
            "hora": hora_pedido
        }
        
        criar_num = _criar_numero_pedido(dados_num_pedido)
        if not criar_num:
            logger.error("Falha ao criar número do pedido após todas as tentativas")
            return False
        
        numero_pedido_id = criar_num.get('id')
        if not numero_pedido_id:
            logger.error("ID do número do pedido não foi retornado")
            return False
            
        logger.info(f"Número do pedido criado com sucesso: {numero_pedido_id}")
        
        # Rate limiting elegante
        rate_limiter.wait('num_pedido', DELAY_NUM_PEDIDO)
        
        # Criar ordem do pedido com retry automático
        logger.info(f"Criando ordem do pedido: {numero_pedido_id}")
        hora_pedido_str = hora_pedido or ""
        criar_order = _criar_ordem_pedido(id_cliente, int(numero_pedido_id), hora_pedido_str)
        
        if not criar_order:
            logger.error("Falha ao criar ordem do pedido após todas as tentativas")
            return False
        
        ordem_pedido_id = criar_order.get('id')
        logger.info(f"Ordem do pedido criada com sucesso: {ordem_pedido_id}")
        
        # Rate limiting elegante
        rate_limiter.wait('order_pedido', DELAY_ORDER_PEDIDO)
        
        # Criar itens individuais do pedido com processamento mais robusto
        itens_criados_com_sucesso = 0
        itens_com_falha = []
        
        for i, pedido in enumerate(lista_pedidos, 1):
            try:
                produto_id = pedido.get('id_Prod')
                logger.info(f"Processando item {i}/{len(lista_pedidos)} - Produto ID: {produto_id}")
                
                # Buscar informações do produto com tratamento de erro
                produto_info = None
                try:
                    produto_info = produtos_api.obter_produto(produto_id)
                except Exception as e:
                    logger.warning(f"Erro ao buscar produto {produto_id}: {str(e)}")
                
                if not produto_info:
                    logger.warning(f"Produto não encontrado: {produto_id}. Usando valor 0.0")
                    valor_unitario = 0.0
                else:
                    valor_unitario = float(produto_info.get('Valor_Prod', 0.0))
                
                # Rate limiting para cada item
                rate_limiter.wait('item_pedido', DELAY_ITEM_PEDIDO)
                
                # Log estruturado em vez de print
                logger.info(f"Criando item do pedido - numPedido: {numero_pedido_id}, "
                           f"idOrderPedido: {ordem_pedido_id}, id_Prod: {produto_id}, "
                           f"V_unit: {valor_unitario}, qtd: {pedido.get('qtd')}, "
                           f"data: {data_pedido}, hora: {hora_pedido}")
                
                dados_item = {
                    "id_cliente": id_cliente,
                    "numPedido": numero_pedido_id,
                    "idOrderPedido": ordem_pedido_id,
                    "id_Prod": produto_id,
                    "V_unit": valor_unitario,
                    "qtd": pedido.get('qtd'),
                    "observ": _sanitizar_string(pedido.get('observ', '')),
                    "data": data_pedido,
                    "hora": hora_pedido
                }
                
                resultado = _criar_item_pedido(dados_item)
                
                if resultado:
                    itens_criados_com_sucesso += 1
                    logger.info(f"Item {i} criado com sucesso")
                else:
                    itens_com_falha.append(i)
                    logger.error(f"Falha ao criar item {i} do pedido após todas as tentativas")
                    
            except Exception as e:
                itens_com_falha.append(i)
                logger.error(f"Erro inesperado ao processar item {i}: {str(e)}")
        
        # Relatório final
        total_itens = len(lista_pedidos)
        logger.info(f"Processamento concluído - Sucessos: {itens_criados_com_sucesso}/{total_itens}")
        
        if itens_com_falha:
            logger.warning(f"Itens com falha: {itens_com_falha}")
        
        # Considera sucesso se pelo menos 80% dos itens foram processados
        taxa_sucesso = itens_criados_com_sucesso / total_itens
        sucesso_parcial = taxa_sucesso >= 0.8
        
        if sucesso_parcial:
            logger.info(f"Pedido processado com sucesso! Taxa de sucesso: {taxa_sucesso:.1%}")
            return True
        else:
            logger.error(f"Taxa de sucesso muito baixa: {taxa_sucesso:.1%}")
            return False
        
    except Exception as e:
        logger.error(f"Erro crítico ao criar registros do pedido: {str(e)}", exc_info=True)
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
    print(dados_json)
    try:
        # Validação rigorosa do tipo de entrada
        if not isinstance(dados_json, str):
            logger.error(f"O argumento deve ser uma string JSON, recebido: {type(dados_json)}")
            return {
                'sucesso': False,
                'pedidos': [],
                'mensagem': f'Erro: O argumento deve ser uma string JSON, recebido: {type(dados_json)}'
            }
        
        # Validação básica do conteúdo
        dados_json_limpo = dados_json.strip()
        if not dados_json_limpo:
            logger.error("String JSON está vazia")
            return {
                'sucesso': False,
                'pedidos': [],
                'mensagem': 'Erro: String JSON está vazia'
            }
        
        # Sanitização básica - remove caracteres de controle potencialmente perigosos
        dados_json_sanitizado = ''.join(char for char in dados_json_limpo if ord(char) >= 32 or char in '\n\r\t')
        
        # Decodifica a string JSON
        dados = json.loads(dados_json_sanitizado)
        
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
        
        # Busca o cliente pelo telefone usando o endpoint clientes/fone/{fone}
        cliente_existente = None
        try:
            logger.info("=== VERIFICAÇÃO DE CLIENTE EXISTENTE ===")
            cliente_existente = _buscar_cliente_por_telefone(fone_cliente)
            
            if cliente_existente:
                logger.info("✅ Cliente já cadastrado no sistema!")
                logger.info(f"   📋 Dados do cliente encontrado:")
                logger.info(f"   🆔 ID: {cliente_existente.get('id')}")
                logger.info(f"   👤 Nome: {cliente_existente.get('nome')} {cliente_existente.get('sobrenome')}")
                logger.info(f"   📞 Telefone: {cliente_existente.get('fone')}")
            else:
                logger.info("ℹ️  Cliente não encontrado no sistema")
                logger.info(f"   📞 Telefone pesquisado: {fone_cliente}")
                logger.info(f"   ➡️  Será usado ID padrão {ID_CLIENTE_SEM_CADASTRO} (sem cadastro)")
                
        except Exception as e:
            logger.error(f"❌ Erro na busca do cliente: {str(e)}")
            logger.info(f"   ➡️  Continuando com ID padrão {ID_CLIENTE_SEM_CADASTRO}")
            cliente_existente = None

        # Determina os dados do cliente a serem usados no pedido
        if cliente_existente:
            # 🎯 USAR DADOS DO CLIENTE EXISTENTE
            id_cliente = cliente_existente.get('id')
            nome_para_pedido = cliente_existente.get('nome', '')
            sobrenome_para_pedido = cliente_existente.get('sobrenome', '')
            
            logger.info("📝 Usando dados do cliente cadastrado para o pedido:")
            logger.info(f"   🆔 ID Cliente: {id_cliente}")
            logger.info(f"   👤 Nome: {nome_para_pedido} {sobrenome_para_pedido}")
            
        else:
            # 🆕 CLIENTE NÃO CADASTRADO - usar dados do pedido
            id_cliente = ID_CLIENTE_SEM_CADASTRO
            nome_para_pedido = nome_cliente or ''
            sobrenome_para_pedido = "_"
            
            logger.info("📝 Usando dados do pedido (cliente não cadastrado):")
            logger.info(f"   🆔 ID Cliente: {id_cliente} (sem cadastro)")
            logger.info(f"   👤 Nome: {nome_para_pedido} {sobrenome_para_pedido}")

        # Validação final dos dados antes de criar o pedido
        if not id_cliente:
            logger.error("ID do cliente não foi determinado corretamente")
            return {
                'sucesso': False,
                'pedidos': lista_pedidos,
                'mensagem': 'Erro: ID do cliente não foi determinado'
            }
        
        logger.info("=== INICIANDO CRIAÇÃO DO PEDIDO ===")
        logger.info(f"📋 Resumo dos dados:")
        logger.info(f"   🆔 ID Cliente: {id_cliente}")
        logger.info(f"   👤 Nome: {nome_para_pedido} {sobrenome_para_pedido}")
        logger.info(f"   📞 Telefone: {fone_cliente}")
        logger.info(f"   📅 Data: {data_pedido}")
        logger.info(f"   🕐 Hora: {hora_pedido}")
        logger.info(f"   📦 Total de itens: {len(lista_pedidos)}")
        
        # Cria os registros do pedido
        sucesso = _criar_registros_pedido(
            id_cliente=int(id_cliente),
            nome=nome_para_pedido,
            sobrenome=sobrenome_para_pedido,
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


