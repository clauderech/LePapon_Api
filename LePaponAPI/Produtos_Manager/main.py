import flet as ft
from views.update_produto_view import update_produto_view as update_produto_view
from views.update_produto_bebidas_view import update_produto_bebidas_view as update_produto_bebidas_view
from views.inserir_produto_view import inserir_produto_view
from views.inserir_produto_bebidas_view import inserir_produto_bebidas_view

# Função principal para a janela do programa
def main(page: ft.Page):
    page.title = "Produtos Manager"
    page.route = "/home"

    # Menu lateral com rotas atualizadas
    menu = ft.NavigationRail(
        height=600,
        selected_index=0,
        destinations=[
            ft.NavigationRailDestination(icon=ft.Icons.HOME, label="Início"),
            ft.NavigationRailDestination(icon=ft.Icons.ADD, label="Inserir Produto"),
            ft.NavigationRailDestination(icon=ft.Icons.LOCAL_BAR, label="Inserir Bebida"),
            ft.NavigationRailDestination(icon=ft.Icons.EDIT, label="Update Produto"),
            ft.NavigationRailDestination(icon=ft.Icons.LOCAL_DRINK, label="Update Bebidas")
        ],
        on_change=lambda e: page.go(
            "/home" if e.control.selected_index == 0 else
            "/inserir_produto_view" if e.control.selected_index == 1 else
            "/inserir_produto_bebidas_view" if e.control.selected_index == 2 else
            "/update_produto_view" if e.control.selected_index == 3 else
            "/update_produto_bebidas_view"             
        )
    )

    # Função para configurar a navegação com base na rota
    def configurar_navegacao(route):
        page.views.clear()
        
        if route == "/inserir_produto_view":
            page.views.append(ft.View(
                route=route,
                controls=[
                    ft.Row([
                        menu,
                        ft.VerticalDivider(width=1),
                        ft.Container(content=inserir_produto_view(page), expand=True)
                    ])
                ]
            ))
        elif route == "/inserir_produto_bebidas_view":
            page.views.append(ft.View(
                route=route,
                controls=[
                    ft.Row([
                        menu,
                        ft.VerticalDivider(width=1),
                        ft.Container(content=inserir_produto_bebidas_view(page), expand=True)
                    ])
                ]
            ))
        elif route == "/update_produto_view":
            page.views.append(ft.View(
                route=route,
                controls=[
                    ft.Row([
                        menu,
                        ft.VerticalDivider(width=1),
                        ft.Container(content=update_produto_view(page), expand=True)
                    ])
                ]
            ))
        elif route == "/update_produto_bebidas_view":
            page.views.append(ft.View(
                route=route,
                controls=[
                    ft.Row([
                        menu,
                        ft.VerticalDivider(width=1),
                        ft.Container(content=update_produto_bebidas_view(page), expand=True)
                    ])
                ]
            ))
        else:  # route == "/home"
            page.views.append(ft.View(
                route="/home",
                controls=[
                    ft.Row([
                        menu,
                        ft.VerticalDivider(width=1),
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Bem-vindo ao Produtos Manager!", 
                                        size=24, 
                                        weight=ft.FontWeight.BOLD),
                                ft.Text("Selecione uma opção no menu lateral para começar.", 
                                        size=16)
                            ], 
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            expand=True
                        )
                    ])
                ]
            ))
        page.update()

    # Configurando o evento de mudança de rota
    page.on_route_change = lambda e: configurar_navegacao(page.route)
    
    # Configuração inicial da página
    configurar_navegacao(page.route)

ft.app(target=main)
