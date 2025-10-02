import flet as ft
from models.pedidosModel import PedidoAPI
from models.numPedidoModel import NumPedidoAPI
from models.orderPedidoModel import OrderPedidoAPI
import asyncio
import pandas as pd
from models.produtosTodos import Produtos

pedidoAPI = PedidoAPI()
numPedidoAPI = NumPedidoAPI()
orderPedidoAPI = OrderPedidoAPI()

def main(page: ft.Page):
    page.title = "Pedidos da Cozinha"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.controls = []
    lista_widgets = []

    async def atualizar_pedidos():
        produtos_api = Produtos()
        produtos = produtos_api.listar_produtos() or []
        df_produtos = pd.DataFrame(produtos)
        host = "192.168.15.6"
        port = 2380
        while True:
            pedidos = pedidoAPI.listar_pedidos() or []
            num_pedido = numPedidoAPI.listar_num_pedidos() or []
            order_pedidos = orderPedidoAPI.listar_ordem_pedidos() or []
            pedidos_ativos = [order for order in order_pedidos if order.get("ativo") == 1]
            lista_widgets.clear()
            for order in pedidos_ativos:
                num_pedido_id = order.get("numPedido")
                cliente_nome = "Desconhecido"
                for numpedido in num_pedido:
                    if numpedido["id"] == num_pedido_id:
                        cliente_nome = numpedido["nome"]
                        break
                pedido = [pedido for pedido in pedidos if pedido["idOrderPedido"] == order["id"]]
                df_pedido = pd.DataFrame(pedido)
                if not df_pedido.empty:
                    df_merged = pd.merge(df_pedido, df_produtos, left_on="id_Prod", right_on="id_Prod", how="left")
                    itens_texto = "\n".join(f"{row['qtd']} - {row['nome_Prod']} - {row['observ']}" for _, row in df_merged.iterrows())
                else:
                    itens_texto = ""
                item = ft.ListTile(
                    title=ft.Text(f"Pedido #{order['id']} - Hora: {order['hora']} - Cliente: {cliente_nome}"),
                    subtitle=ft.Text(itens_texto))
                lista_widgets.append(item)
            page.controls = []
            page.add(ft.Column(lista_widgets))
            page.update()
            await asyncio.sleep(60)

    page.run_task(atualizar_pedidos)

ft.app(target=main, view=ft.AppView.FLET_APP)
