import flet as ft
from views.clientes_view import clientes_view
from views.pedidostemp_view import pedidostemp_view
from views.ordempedidos_view import ordempedidos_view
from views.numpedidos_view import numpedidos_view
from views.edita_pedidos_view import pedidos_accordion_view  # nova importação
from views.tema_0_0_0 import COR_PRIMARIA, COR_TEXTO, COR_FUNDO
from views.crediario_view import crediario_view
from views.chat_history import chat_history_view
from views.produtos_todos_view import produtos_todos_view
from views.produtos_outros_view import produtos_outros_view

# Rotas/views do app principal
views = {
    "/": clientes_view,
    "/clientes": clientes_view,
    "/produtos_todos": produtos_todos_view,
    "/produtos_outros": produtos_outros_view,
    "/pedidostemp": pedidostemp_view,
    "/ordempedidos": ordempedidos_view,
    "/numpedidos": numpedidos_view,
    "/editapedidos": pedidos_accordion_view,  # nova view para edição de pedidos
    "/crediario": crediario_view,  # nova rota para crediario
    "/chat_history": chat_history_view,
}
dataKeynumPedido = 'id=""&nome=""&sobrenome=""&fone=""'
datakeyPedidosTemp = ''
datakeyOrder = "numPedido=''&idCliente=''"

def main(page: ft.Page):
    page.title = "LePapon Principal"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = COR_FUNDO
    def route_change(e):
        route_path = page.route.split("?")[0]
        view_func = views.get(route_path, clientes_view)
        
        # Remove todas as views existentes e cria uma nova
        page.views.clear()
        page.views.append(
            ft.View(
                page.route,
                [ft.Column([c for c in [view_func(page)] if c is not None], expand=True, scroll=ft.ScrollMode.AUTO)],
                navigation_bar=ft.NavigationBar(
                    destinations=[
                        ft.NavigationBarDestination(icon=ft.Icons.PERSON, label="Clientes"),
                        ft.NavigationBarDestination(icon=ft.Icons.FORMAT_LIST_NUMBERED, label="Num Pedidos"),
                        ft.NavigationBarDestination(icon=ft.Icons.FORMAT_LIST_NUMBERED_ROUNDED, label="Ordem Pedidos"),
                        ft.NavigationBarDestination(icon=ft.Icons.RECEIPT, label="Pedidos Temp"),
                        ft.NavigationBarDestination(icon=ft.Icons.EDIT, label="Editar Pedidos"),
                        ft.NavigationBarDestination(icon=ft.Icons.SHOPPING_CART, label="Produtos Outros"),
                        ft.NavigationBarDestination(icon=ft.Icons.PAYMENTS, label="Crediário"),
                        ft.NavigationBarDestination(icon=ft.Icons.CHAT, label="Chat"),
                    ],
                    on_change=lambda e: page.go([
                        "/clientes", "/numpedidos?"+dataKeynumPedido, "/ordempedidos?"+datakeyOrder, "/pedidostemp", "/editapedidos", "/produtos_outros", "/crediario", "/chat_history"
                    ][e.control.selected_index]),
                    bgcolor=COR_PRIMARIA,
                )
            )
        )
        page.update()
    page.on_route_change = route_change
    
    # Inicializa a primeira view
    initial_view_func = views.get(page.route or "/", clientes_view)
    page.views.append(
        ft.View(
            page.route or "/",
            [ft.Column([c for c in [initial_view_func(page)] if c is not None], expand=True, scroll=ft.ScrollMode.AUTO)],
            navigation_bar=ft.NavigationBar(
                destinations=[
                    ft.NavigationBarDestination(icon=ft.Icons.PERSON, label="Clientes"),
                    ft.NavigationBarDestination(icon=ft.Icons.FORMAT_LIST_NUMBERED, label="Num Pedidos"),
                    ft.NavigationBarDestination(icon=ft.Icons.FORMAT_LIST_NUMBERED_ROUNDED, label="Ordem Pedidos"),
                    ft.NavigationBarDestination(icon=ft.Icons.RECEIPT, label="Pedidos Temp"),
                    ft.NavigationBarDestination(icon=ft.Icons.EDIT, label="Editar Pedidos"),
                    ft.NavigationBarDestination(icon=ft.Icons.SHOPPING_CART, label="Produtos Outros"),
                    ft.NavigationBarDestination(icon=ft.Icons.PAYMENTS, label="Crediário"),
                    ft.NavigationBarDestination(icon=ft.Icons.CHAT, label="Chat"),
                ],
                on_change=lambda e: page.go([
                    "/clientes", "/numpedidos?"+dataKeynumPedido, "/ordempedidos?"+datakeyOrder, "/pedidostemp", "/editapedidos", "/produtos_outros", "/crediario", "/chat_history"
                ][e.control.selected_index]),
                bgcolor=COR_PRIMARIA,
            )
        )
    )
    page.update()

ft.app(target=main)