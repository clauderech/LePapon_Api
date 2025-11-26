import flet as ft
from datetime import date
from models.pedidos_manager_api import PedidosManager
from models.controle_diario import ControleDiario
from models.clientes_api import ClientesAPI
from models.produtos_todos_api import ProdutosTodosAPI
import os
import requests
from dotenv import load_dotenv
from pathlib import Path

# Carrega .env do diretório raiz do projeto
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

api_key = os.environ.get("MINHA_API_KEY")

# Valida se a API key foi carregada
if not api_key:
    print("AVISO: API Key não foi carregada do arquivo .env")

BASE_URL = "http://lepapon.api:3000"
pedidos_manager = PedidosManager(BASE_URL, api_key) if api_key else PedidosManager(BASE_URL)
controle_diario = ControleDiario(BASE_URL)
clientes_api = ClientesAPI(BASE_URL)
produtos_api = ProdutosTodosAPI(BASE_URL)

# View para gerenciar pedidos temporários: listar, transferir e deletar

def pedidos_manager_view(page: ft.Page):
    msg = ft.Text(visible=False)

    def safe_boolean_convert(value):
        """Converte valor para boolean de forma segura e consistente"""
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'sim', 'verdadeiro')
        return False

    def format_pedido_item(pedido, produto_nome="Produto não encontrado"):
        """Formata um item de pedido individual com campos: id, qtd, nome_Prod, pago"""
        # Converte pago de forma segura
        is_pago = safe_boolean_convert(pedido.get('pago', False))
        
        return ft.Container(
            content=ft.Row([
                ft.Text(f"ID: {pedido.get('id', 'N/A')}", weight=ft.FontWeight.BOLD, size=12, expand=1, color=ft.Colors.BLACK),
                ft.Text(f"Qtd: {pedido.get('qtd', 'N/A')}", size=12, expand=1, color=ft.Colors.BLACK),
                ft.Text(f"{produto_nome}", size=12, color=ft.Colors.BLACK, expand=3),
                ft.Checkbox(
                    value=is_pago,
                    label=ft.Text("Pago", color=ft.Colors.BLACK),
                    disabled=True,  # Apenas visualização por enquanto
                    scale=0.8,
                    
                ),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=8,
            bgcolor="#f0f8ff",
            border_radius=6,
            margin=ft.margin.only(left=20, bottom=3),
            
        )

    def safe_float_convert(value, default=0.0):
        """Converte valor para float de forma segura"""
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def format_cliente_group(cliente_nome, pedidos_cliente, produtos_dict):
        """Formata um grupo de pedidos por cliente"""
        total_cliente = sum(safe_float_convert(p.get('sub_total', 0)) for p in pedidos_cliente)
        
        # Cabeçalho do cliente
        cliente_header = ft.Container(
            content=ft.Row([
                ft.Text(f"Cliente: {cliente_nome}", color=ft.Colors.BLUE, weight=ft.FontWeight.BOLD, size=14),
                ft.Text(f"Total Geral: R$ {total_cliente:.2f}", color=ft.Colors.GREEN, weight=ft.FontWeight.BOLD, size=14),
                ft.Text(f"({len(pedidos_cliente)} pedidos)", color=ft.Colors.GREY_700, size=12),
            ]),
            padding=10,
            bgcolor="#e3f2fd",
            border_radius=8,
            margin=ft.margin.only(bottom=5)
        )
        
        # Lista de pedidos do cliente
        pedidos_items = []
        for pedido in pedidos_cliente:
            id_produto = str(pedido.get('id_Prod', ''))
            produto_nome = produtos_dict.get(id_produto, f"Produto ID: {id_produto}")
            pedidos_items.append(format_pedido_item(pedido, produto_nome))
        
        return ft.Column([cliente_header] + pedidos_items, spacing=0)

    def validate_and_process_clientes(clientes_data):
        """Valida e processa dados de clientes da API"""
        if not isinstance(clientes_data, list):
            return {}
        
        clientes_dict = {}
        for cliente in clientes_data:
            if not isinstance(cliente, dict):
                continue
            client_id = cliente.get('id')
            nome = cliente.get('nome', '')
            sobrenome = cliente.get('sobrenome', '')
            if client_id is not None:
                clientes_dict[str(client_id)] = f"{nome} {sobrenome}".strip()
        return clientes_dict

    def validate_and_process_produtos(produtos_data):
        """Valida e processa dados de produtos da API"""
        if not isinstance(produtos_data, list):
            return {}
            
        produtos_dict = {}
        for produto in produtos_data:
            if not isinstance(produto, dict):
                continue
            prod_id = produto.get('id_Prod')
            nome_prod = produto.get('nome_Prod', 'Nome não disponível')
            if prod_id is not None:
                produtos_dict[str(prod_id)] = nome_prod
        return produtos_dict

    def show_loading(message="Processando..."):
        """Mostra indicador de loading"""
        msg.value = message
        msg.color = "blue"
        msg.visible = True
        page.update()

    def listar_pedidos(e=None):
        show_loading("Carregando pedidos...")
        try:
            pedidos = pedidos_manager.carregar_todos()
            pedidos_por_cliente = {}
            
            if not pedidos:
                lista_pedidos.controls = [ft.Text("Nenhum pedido temporário encontrado.")]
            else:
                # Busca todos os clientes para fazer o merge
                try:
                    clientes = clientes_api.get_all()
                    clientes_dict = validate_and_process_clientes(clientes)
                except (requests.RequestException, KeyError, AttributeError) as e:
                    print(f"Erro ao carregar clientes: {e}")
                    clientes_dict = {}
                
                # Busca todos os produtos para fazer o merge
                try:
                    produtos = produtos_api.get_all()
                    produtos_dict = validate_and_process_produtos(produtos)
                except (requests.RequestException, KeyError, AttributeError) as e:
                    print(f"Erro ao carregar produtos: {e}")
                    produtos_dict = {}
                
                # Agrupa pedidos por id_cliente
                for pedido in pedidos:
                    id_cliente = str(pedido.get('id_cliente', ''))
                    if id_cliente not in pedidos_por_cliente:
                        pedidos_por_cliente[id_cliente] = []
                    pedidos_por_cliente[id_cliente].append(pedido)
                
                # Cria os grupos formatados
                grupos = []
                for id_cliente, pedidos_cliente in pedidos_por_cliente.items():
                    cliente_nome = clientes_dict.get(id_cliente, f"Cliente ID: {id_cliente}")
                    grupo = format_cliente_group(cliente_nome, pedidos_cliente, produtos_dict)
                    grupos.append(grupo)
                
                lista_pedidos.controls = grupos
            
            msg.value = f"{len(pedidos)} pedidos carregados em {len(pedidos_por_cliente)} grupos de clientes."
            msg.color = "green"
            msg.visible = True
            page.update()
        except Exception as ex:
            msg.value = f"Erro ao carregar pedidos: {ex}"
            msg.color = "red"
            msg.visible = True
            page.update()

    def deletar_todos(e):
        show_loading("Deletando todos os pedidos...")
        try:
            pedidos_manager.deletar_todos()
            pedidos_manager.deletar_todos_externo()
            msg.value = "Todos os pedidos temporários foram deletados."
            msg.color = "green"
            msg.visible = True
            listar_pedidos(None)
        except Exception as ex:
            msg.value = f"Erro ao deletar: {ex}"
            msg.color = "red"
            msg.visible = True
            page.update()

    def transferir_para_vendas(e):
        show_loading("Transferindo para vendas...")
        try:
            vendas = pedidos_manager.transferir_para_vendas()
            msg.value = f"{len(vendas)} vendas criadas e pedidos removidos."
            msg.color = "green"
            msg.visible = True
            listar_pedidos(None)
        except Exception as ex:
            msg.value = f"Erro ao transferir para vendas: {ex}"
            msg.color = "red"
            msg.visible = True
            page.update()

    def transferir_para_crediario(e):
        show_loading("Transferindo para crediário...")
        try:
            crediarios = pedidos_manager.transferir_para_crediario()
            msg.value = f"{len(crediarios)} lançamentos no crediário e pedidos removidos."
            msg.color = "green"
            msg.visible = True
            listar_pedidos(None)
        except Exception as ex:
            msg.value = f"Erro ao transferir para crediário: {ex}"
            msg.color = "red"
            msg.visible = True
            page.update()

    def atualizar_data_ontem(e):
        show_loading("Atualizando data dos pedidos para ontem...")
        try:
            result = pedidos_manager.atualizar_data_ontem()
            msg.value = "Data de todos os pedidos atualizada para ontem com sucesso."
            msg.color = "green"
            msg.visible = True
            listar_pedidos(None)
        except Exception as ex:
            msg.value = f"Erro ao atualizar data: {ex}"
            msg.color = "red"
            msg.visible = True
            page.update()

    

    lista_pedidos = ft.Column([], scroll=ft.ScrollMode.AUTO, expand=False, height=700, width=800)
    listar_pedidos(None)

    return ft.Column([
        ft.Text("Gerenciar Pedidos Temporários", style=ft.TextThemeStyle.HEADLINE_SMALL),
        ft.Row([
            ft.ElevatedButton("Listar Pedidos", on_click=listar_pedidos),
            ft.ElevatedButton("Atualizar Data para Ontem", on_click=atualizar_data_ontem),
            ft.ElevatedButton("Transferir para Vendas", on_click=transferir_para_vendas),
            ft.ElevatedButton("Transferir para Crediário (não pagos)", on_click=transferir_para_crediario),
            ft.ElevatedButton("Deletar Todos", on_click=deletar_todos),
            msg
        ]),
        ft.Divider(),
        ft.Text("Pedidos Temporários Atuais:", style=ft.TextThemeStyle.TITLE_MEDIUM),
        lista_pedidos,        
    ])