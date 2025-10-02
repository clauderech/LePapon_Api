import flet as ft
from models.categoriaprodutos_api import CategoriaProdutosAPI
from models.subcategprodutos_api import SubCategProdutosAPI
import requests

BASE_URL = "http://lepapon.api"

# Instâncias das APIs
categoria_api = CategoriaProdutosAPI(BASE_URL)
subcategoria_api = SubCategProdutosAPI(BASE_URL)

def update_produto_view(page: ft.Page):
    page.route = "/update_produto_view"

    # Função para carregar categorias e subcategorias
    def carregar_dados():
        categorias = categoria_api.get_all()
        subcategorias = subcategoria_api.get_all()
        return categorias, subcategorias
    
    categorias, subcategorias = carregar_dados()
    #print(subcategorias)

    categoria_dropdown = ft.Dropdown(
        label="Categoria",
        options=[ft.dropdown.Option(c["id_CatProd"], c["nome_CatProd"]) for c in categorias],
        width=400
    )

    subcategoria_dropdown = ft.Dropdown(
        label="Subcategoria",
        options=[ft.dropdown.Option(sc["id_SubCategProd"], sc["nome_SubCategProd"]) for sc in subcategorias],
        width=400
    )

    mensagem = ft.Text()

    # Função auxiliar para criar o dicionário de dados do produto
    def criar_dados_produto():
        return {
            "subCategProd": subcateg_prod_field.value,
            "nome_Prod": nome_prod_field.value,
            "Valor_Prod": valor_prod_field.value,
            "unit": unit_field.value
        }

    # Função para atualizar o produto em ambos os endpoints
    def atualizar_tudo(e):
        if id_produto_field.value:
            produto_id = id_produto_field.value
            dados_produto = criar_dados_produto()

            # Cria payloads separados para cada endpoint
            dados_produtostodos = dados_produto.copy()
            dados_produtostodos.pop("subCategProd", None)

            # Atualiza no endpoint de produtos
            response_produtos = requests.put(f"{BASE_URL}/api/produtos/{produto_id}", json=dados_produto)

            # Atualiza no endpoint de produtostodos
            response_produtostodos = requests.put(f"{BASE_URL}/api/produtostodos/{produto_id}", json=dados_produtostodos)

            # Verifica os resultados
            if response_produtos.status_code == 200 and response_produtostodos.status_code == 200:
                mensagem.value = "Produto atualizado com sucesso em ambos os endpoints!"
                # Recarrega todos os produtos após a atualização
                recarregar_todos_produtos()
            else:
                mensagem.value = (
                    f"Erro ao atualizar: Produtos: {response_produtos.text}, "
                    f"ProdutosTodos: {response_produtostodos.text}"
                )
            page.update()

    # Referências para as caixas de texto
    id_produto_field = ft.TextField(label="id_Prod", width=100)
    subcateg_prod_field = ft.TextField(label="subCategProd", width=150)
    nome_prod_field = ft.TextField(label="nome_Prod", width=200)
    valor_prod_field = ft.TextField(label="Valor_Prod", width=100)
    unit_field = ft.TextField(label="unit", width=100)

    # Botão para atualizar o produto
    botao_atualizar = ft.ElevatedButton("Atualizar Produto", on_click=atualizar_tudo)

    linha_campos = ft.Row(
        controls=[
            id_produto_field,
            subcateg_prod_field,
            nome_prod_field,
            valor_prod_field,
            unit_field,
            botao_atualizar
        ]
    )

    # Atualiza subcategorias com base na categoria selecionada
    def atualizar_subcategorias(e):
        if categoria_dropdown.value is not None:
            subcategorias_filtradas = [
                sc for sc in subcategorias if sc["idCategProd"] == int(categoria_dropdown.value)
            ]
            subcategoria_dropdown.options = [
                ft.dropdown.Option(sc["id_SubCategProd"], sc["nome_SubCategProd"]) for sc in subcategorias_filtradas
            ]
            subcategoria_dropdown.value = None  # Reseta a seleção
            page.update()

    categoria_dropdown.on_change = atualizar_subcategorias

    # Carrega todos os produtos ao iniciar a janela
    todos_produtos = requests.get(f"{BASE_URL}/api/produtos").json()

    # Lista para exibir os produtos
    lista_produtos = ft.ListView(expand=True)

    # Função para editar um produto ao clicar na lista
    def editar_produto(e):
        produto_id = e.control.data  # Obtém o ID do produto armazenado no controle
        produto = next((p for p in todos_produtos if p["id_Prod"] == produto_id), None)
        if produto:
            id_produto_field.value = str(produto["id_Prod"])
            subcateg_prod_field.value = str(produto["subCategProd"])
            nome_prod_field.value = produto["nome_Prod"]
            valor_prod_field.value = str(produto["Valor_Prod"])
            unit_field.value = produto["unit"]
            page.update()

    # Função para recarregar todos os produtos
    def recarregar_todos_produtos():
        nonlocal todos_produtos
        todos_produtos = requests.get(f"{BASE_URL}/api/produtos").json()
        carregar_produtos()  # Atualiza a lista de produtos exibida

    # Atualiza a lista de produtos para incluir eventos de clique
    def carregar_produtos(e=None):
        if subcategoria_dropdown.value is not None:
            produtos_filtrados = [
                produto for produto in todos_produtos if produto["subCategProd"] == int(subcategoria_dropdown.value)
            ]
            lista_produtos.controls = [
                ft.ListTile(
                    title=ft.Text(f"{produto['id_Prod']}: {produto['nome_Prod']}"),
                    data=produto['id_Prod'],
                    on_click=editar_produto
                ) for produto in produtos_filtrados
            ]
            page.update()

    subcategoria_dropdown.on_change = carregar_produtos

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



