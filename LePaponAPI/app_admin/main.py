import flet as ft
from models.crediario_api import CrediarioAPI
from models.vendas_api import VendasAPI
from views.crediario_view import crediario_view
from views.vendas_view import vendas_view
from views.pedidos_manager_view import pedidos_manager_view
from views.fornecedores_view import fornecedores_view
from views.despesas_diarias_view import despesas_diarias_view
from views.forma_pagamento_view import forma_pagamento_view
from views.ativos_view import ativos_view
from views.controle_diario_view import controle_diario_view
from views.recebido_view import recebido_view
from views.controle_semanal_view import controle_semanal_view
from views.contador_agent_view import contador_agent_view

# Rotas/views do app_admin
views = {
    "/vendas": vendas_view,
    "/crediario": crediario_view,
    "/pedidosmanager": pedidos_manager_view,
    "/fornecedores": fornecedores_view,
    "/fornecedores/novo": fornecedores_view,  # Adiciona rota para novo fornecedor
    "/despesas_diarias": despesas_diarias_view,
    "/despesas_diarias/novo": despesas_diarias_view,  # Adiciona rota para nova despesa
    "/forma_pagamento": forma_pagamento_view,
    "/forma_pagamento/novo": forma_pagamento_view,
    "/ativos": ativos_view,
    "/controle_diario": controle_diario_view,
    "/recebido": recebido_view,
    "/controle_semanal": controle_semanal_view,
    "/contador_agent": contador_agent_view,
}

def main(page: ft.Page):
    page.title = "LePapon Admin"
    def route_change(e):
        route_path = page.route.split("?")[0]
        view_func = views.get(route_path, pedidos_manager_view)
        page.views[-1] = ft.View(
            page.route,
            [ft.Column([view_func(page)], expand=True)],
            navigation_bar=ft.NavigationBar(
                destinations=[
                    ft.NavigationBarDestination(icon=ft.Icons.PAID, label="Vendas"),
                    ft.NavigationBarDestination(icon=ft.Icons.CREDIT_CARD, label="Crediário"),
                    ft.NavigationBarDestination(icon=ft.Icons.LIST, label="Pedidos Manager"),
                    ft.NavigationBarDestination(icon=ft.Icons.PEOPLE, label="Fornecedores"),
                    ft.NavigationBarDestination(icon=ft.Icons.MONEY, label="Despesas Diárias"),
                    ft.NavigationBarDestination(icon=ft.Icons.PAYMENTS, label="Forma Pagamento"),
                    ft.NavigationBarDestination(icon=ft.Icons.ASSESSMENT, label="Ativos"),
                    ft.NavigationBarDestination(icon=ft.Icons.INSERT_CHART, label="Controle Diário"),
                    ft.NavigationBarDestination(icon=ft.Icons.ATTACH_MONEY, label="Recebido"),
                    ft.NavigationBarDestination(icon=ft.Icons.BAR_CHART, label="Controle Semanal"),
                    ft.NavigationBarDestination(icon=ft.Icons.SUPPORT_AGENT, label="Agente Contábil"),
                ],
                on_change=lambda e: page.go([
                    "/vendas", "/crediario", "/pedidosmanager", "/fornecedores", "/despesas_diarias", "/forma_pagamento", "/ativos", "/controle_diario", "/recebido", "/controle_semanal", "/contador_agent"
                ][e.control.selected_index])
            )
        )
        page.update()
    page.on_route_change = route_change
    view_func = views.get(page.route or "/", pedidos_manager_view)
    page.views.append(
        ft.View(
            page.route or "/",
            [ft.Column([view_func(page)], expand=True)],
            navigation_bar=ft.NavigationBar(
                destinations=[
                    ft.NavigationBarDestination(icon=ft.Icons.PAID, label="Vendas"),
                    ft.NavigationBarDestination(icon=ft.Icons.CREDIT_CARD, label="Crediário"),
                    ft.NavigationBarDestination(icon=ft.Icons.LIST, label="Pedidos Manager"),
                    ft.NavigationBarDestination(icon=ft.Icons.PEOPLE, label="Fornecedores"),
                    ft.NavigationBarDestination(icon=ft.Icons.MONEY, label="Despesas Diárias"),
                    ft.NavigationBarDestination(icon=ft.Icons.PAYMENTS, label="Forma Pagamento"),
                    ft.NavigationBarDestination(icon=ft.Icons.ASSESSMENT, label="Ativos"),
                    ft.NavigationBarDestination(icon=ft.Icons.INSERT_CHART, label="Controle Diário"),
                    ft.NavigationBarDestination(icon=ft.Icons.ATTACH_MONEY, label="Recebido"),
                    ft.NavigationBarDestination(icon=ft.Icons.BAR_CHART, label="Controle Semanal"),
                    ft.NavigationBarDestination(icon=ft.Icons.SUPPORT_AGENT, label="Agente Contábil"),
                ],
                on_change=lambda e: page.go([
                    "/vendas", "/crediario", "/pedidosmanager", "/fornecedores", "/despesas_diarias", "/forma_pagamento", "/ativos", "/controle_diario", "/recebido", "/controle_semanal", "/contador_agent"
                ][e.control.selected_index])
            )
        )
    )
    page.go(page.route or "/")

ft.app(target=main)