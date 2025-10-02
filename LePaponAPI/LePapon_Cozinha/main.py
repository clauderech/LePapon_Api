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
    lista_widgets = []
    page.theme_mode = ft.ThemeMode.LIGHT

    async def atualizar_pedidos():
        produtos_api = Produtos()
        produtos = produtos_api.listar_produtos() or []
        df_produtos = pd.DataFrame(produtos)
        # host = "192.168.15.6"
        # port = 2380
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
                pedido = [pedido for pedido in pedidos if pedido["idOrderPedido"] == order["id"] and 10100 <= pedido["id_Prod"] <= 11017]
                if not pedido:
                    continue  # pula ordens sem itens após filtro
                df_pedido = pd.DataFrame(pedido)
                df_merged = pd.merge(df_pedido, df_produtos, left_on="id_Prod", right_on="id_Prod", how="left")
                itens_texto = "\n".join(f"{row['qtd']} - {row['nome_Prod']} - {row['observ']}" for _, row in df_merged.iterrows())
                def on_checkbox_change(e, order_id=order["id"]):
                    # Atualiza status da ordem para inativo
                    resOrderUpdate = orderPedidoAPI.atualizar_ordem_pedido(order_id, hora=order["hora"], ativo_status=0)
                    print(f"Ordem {order_id} atualizada: {resOrderUpdate}")
                    # Atualiza a lista imediatamente
                    page.clean()
                    page.add(ft.Column(lista_widgets))
                    page.update()

                checkbox = ft.Checkbox(
                    label="Desativar ordem",
                    value=False,
                    on_change=on_checkbox_change,
                    width=200,
                )
                item = ft.ListTile(
                    title=ft.Text(f"Hora: {order['hora']} - Cliente: {cliente_nome}", size=26, color=ft.Colors.BLUE_800, weight=ft.FontWeight.BOLD),
                    subtitle=ft.Text(itens_texto, size=24),
                    trailing=checkbox,
                    width=1100,
                )
                lista_widgets.append(item)
                lista_widgets.append(ft.Divider())
            page.clean()
            # Adiciona rolagem à lista de ordens
            page.add(
                ft.Container(
                    content=ft.Column(lista_widgets, height=900, scroll=ft.ScrollMode.AUTO),
                    width=1200,
                    height=900,
                    bgcolor=ft.Colors.WHITE,
                    padding=10,
                    border_radius=10
                )
            )
            page.update()
            await asyncio.sleep(15)

    page.run_task(atualizar_pedidos)

ft.app(target=main, view=ft.AppView.FLET_APP)
