import flet as ft
from models.categoriabebidas_api import CategoriaBebidasAPI
from models.subcategoriabebidas_api import SubCategoriaBebidasAPI
import requests

BASE_URL = "http://lepapon.api"

# Instâncias das APIs
categoria_bebidas_api = CategoriaBebidasAPI(BASE_URL)
subcategoria_bebidas_api = SubCategoriaBebidasAPI(BASE_URL)

# Renomeando a função principal para update_produto_bebidas_view
def update_produto_bebidas_view(page: ft.Page):
    page.route = "/update_produto_bebidas_view"

    # Função para carregar categorias e subcategorias de bebidas
    def carregar_dados():
        categorias = categoria_bebidas_api.get_all()
        subcategorias = subcategoria_bebidas_api.get_all()
        return categorias, subcategorias

    categorias, subcategorias = carregar_dados()

    # Referências para as caixas de texto
    id_produto_field = ft.TextField(label="id_Prod", width=100)
    subcateg_bebidas_field = ft.TextField(label="subCategBebidas", width=150)
    nome_prod_field = ft.TextField(label="nome_Prod", width=200)
    valor_prod_field = ft.TextField(label="Valor_Prod", width=100)
    unit_field = ft.TextField(label="unit", width=100)

    linha_campos = ft.Row(
        controls=[
            id_produto_field,
            subcateg_bebidas_field,
            nome_prod_field,
            valor_prod_field,
            unit_field
        ]
    )

    mensagem = ft.Text()

    # Função auxiliar para criar o dicionário de dados do produto de bebidas
    def criar_dados_produto_bebidas():
        return {
            "subCategBebidas": subcateg_bebidas_field.value,
            "nome_Prod": nome_prod_field.value,
            "Valor_Prod": valor_prod_field.value,
            "unit": unit_field.value
        }

    # Função para atualizar o produto em ambos os endpoints de bebidas
    def atualizar_tudo_bebidas(e):
        if id_produto_field.value:
            produto_id = id_produto_field.value
            dados_produto_bebidas = criar_dados_produto_bebidas()

            # Cria um payload separado para produtostodos_bebidas sem o campo subCategBebidas
            dados_produtos_todos = dados_produto_bebidas.copy()
            dados_produtos_todos.pop("subCategBebidas", None)

            # Atualiza no endpoint de produtos_bebidas
            response_produtos_bebidas = requests.put(f"{BASE_URL}/api/produtos_bebidas/{produto_id}", json=dados_produto_bebidas)

            # Atualiza no endpoint de produtostodos_bebidas
            response_produtostodos_bebidas = requests.put(f"{BASE_URL}/api/produtostodos/{produto_id}", json=dados_produtos_todos)

            # Verifica os resultados
            if response_produtos_bebidas.status_code == 200 and response_produtostodos_bebidas.status_code == 200:
                mensagem.value = "Produto atualizado com sucesso em ambos os endpoints de bebidas!"
                # Recarrega todos os produtos após a atualização
                recarregar_todos_produtos()
            else:
                mensagem.value = (
                    f"Erro ao atualizar: ProdutosBebidas: {response_produtos_bebidas.text}, "
                    f"ProdutosTodosBebidas: {response_produtostodos_bebidas.text}"
                )
            page.update()

    botao_atualizar_tudo_bebidas = ft.ElevatedButton("Atualizar Tudo em Bebidas", on_click=atualizar_tudo_bebidas)

    linha_campos.controls.append(botao_atualizar_tudo_bebidas)

    # Carrega todos os produtos de bebidas ao iniciar a janela
    todos_produtos_bebidas = requests.get(f"{BASE_URL}/api/produtos_bebidas").json()

    # Lista para exibir os produtos de bebidas
    lista_produtos = ft.ListView(expand=True)

    # Função para editar um produto ao clicar na lista
    def editar_produto(e):
        produto_id = e.control.data  # Obtém o ID do produto armazenado no controle
        produto = next((p for p in todos_produtos_bebidas if p["id_Prod"] == produto_id), None)
        if produto:
            id_produto_field.value = str(produto["id_Prod"])
            subcateg_bebidas_field.value = str(produto["subCategBebidas"])
            nome_prod_field.value = produto["nome_Prod"]
            valor_prod_field.value = str(produto["Valor_Prod"])
            unit_field.value = produto["unit"]
            page.update()

    # Atualiza a lista de produtos para incluir eventos de clique
    def carregar_produtos(e=None):
        if subcategoria_dropdown.value is not None:
            produtos_filtrados = [
                produto for produto in todos_produtos_bebidas if produto["subCategBebidas"] == int(subcategoria_dropdown.value)
            ]
            lista_produtos.controls = [
                ft.ListTile(
                    title=ft.Text(f"{produto['id_Prod']}: {produto['nome_Prod']}"),
                    data=produto['id_Prod'],
                    on_click=editar_produto
                ) for produto in produtos_filtrados
            ]
            page.update()

    # Dropdowns para categorias e subcategorias de bebidas
    categoria_dropdown = ft.Dropdown(
        label="Categoria",
        options=[ft.dropdown.Option(c["id_CategBebidas"], c["nome_CategBebidas"]) for c in categorias],
        width=400,
        on_change=lambda e: atualizar_subcategorias()
    )

    subcategoria_dropdown = ft.Dropdown(
        label="Subcategoria",
        options=[ft.dropdown.Option(sc["idSubCategBebidas"], sc["nomeSubCategBebidas"]) for sc in subcategorias],
        width=400,
        on_change=carregar_produtos
    )

    # Função para atualizar subcategorias com base na categoria selecionada
    def atualizar_subcategorias():
        if categoria_dropdown.value is not None:
            subcategorias_filtradas = [
                sc for sc in subcategorias if sc["idCategBebidas"] == int(categoria_dropdown.value)
            ]
            subcategoria_dropdown.options = [
                ft.dropdown.Option(sc["idSubCategBebidas"], sc["nomeSubCategBebidas"]) for sc in subcategorias_filtradas
            ]
            subcategoria_dropdown.value = None  # Reseta a seleção
            page.update()

    # Função para recarregar todos os produtos de bebidas
    def recarregar_todos_produtos():
        nonlocal todos_produtos_bebidas
        todos_produtos_bebidas = requests.get(f"{BASE_URL}/api/produtos_bebidas").json()
        carregar_produtos()  # Atualiza a lista de produtos exibida

    # Função para retornar à página anterior
    def retornar_pagina(e):
        page.go("/home")  # Substitua "/" pelo caminho da página inicial ou anterior

    # Botão de retorno
    botao_retorno = ft.ElevatedButton("Voltar", on_click=retornar_pagina)

    # Adicionando o botão de retorno ao layout principal
    return ft.Column(
        controls=[
            botao_retorno,  # Botão de retorno adicionado no topo
            linha_campos,
            categoria_dropdown,
            subcategoria_dropdown,
            lista_produtos,
            mensagem
        ]
    )
