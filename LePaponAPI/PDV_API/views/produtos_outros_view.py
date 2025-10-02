import flet as ft
import datetime
from models.numpedidos_api import NumPedidosAPI
from models.ordempedidos_api import OrdemPedidosAPI
from services.order_service import OrderService
from config import BASE_URL
from views.tema_0_0_0 import texto_titulo, aplicar_tema, botao_acao

def produtos_outros_view(page: ft.Page):
    aplicar_tema(page)
    msg = ft.Text(visible=False)
    
    numpedidos_api = NumPedidosAPI(BASE_URL)
    ordempedidos_api = OrdemPedidosAPI(BASE_URL)
    order_service = OrderService(numpedidos_api, ordempedidos_api)
    
    # Cliente fixo ID 13 para "Outros"
    CLIENTE_OUTROS_ID = "13"
    
    def verificar_e_criar_pedido(e):
        try:
            msg.value = "Verificando pedidos existentes..."
            msg.color = "blue"
            msg.visible = True
            page.update()
            
            pedido, ordem = order_service.ensure_order_for_client(CLIENTE_OUTROS_ID, "Outros", "Clientes", "5554992635135")
            num_pedido_id = pedido.get('id') if isinstance(pedido, dict) else pedido
            id_ordem = ordem.get('id') if isinstance(ordem, dict) else ordem

            msg.value = f"Pedido {num_pedido_id} / Ordem {id_ordem} prontos." 
            msg.color = "green"
            msg.visible = True
            page.update()

            page.go(f"/produtos_todos?numPedido={num_pedido_id}&idOrderPedido={id_ordem}&idCliente={CLIENTE_OUTROS_ID}&nome=Outros&sobrenome=Clientes&fone=5554992635135")
            
        except Exception as ex:
            msg.value = f"Erro ao processar pedido: {ex}"
            msg.color = "red"
            msg.visible = True
            page.update()
    
    return ft.Column([
        texto_titulo("Produtos para Outros Clientes"),
        ft.Text("Esta seção permite adicionar produtos para clientes avulsos (ID: 13)", size=16),
        ft.Divider(),
        ft.Text("O sistema irá:", size=14),
        ft.Text("• Verificar se já existe um pedido para 'Outros'", size=12),
        ft.Text("• Criar um novo pedido se necessário", size=12),
        ft.Text("• Verificar se já existe uma ordem para o pedido", size=12),
        ft.Text("• Criar uma nova ordem se necessário", size=12),
        ft.Text("• Navegar para a tela de produtos", size=12),
        ft.Divider(),
        ft.Row([
            botao_acao("Adicionar Produtos para Outros", on_click=verificar_e_criar_pedido),
            msg
        ]),
    ], spacing=10, width=800)
