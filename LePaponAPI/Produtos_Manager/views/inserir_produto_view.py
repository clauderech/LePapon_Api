import flet as ft
from models.categoriaprodutos_api import CategoriaProdutosAPI
from models.subcategprodutos_api import SubCategProdutosAPI
from models.produtos_model import ProdutosModel
from models.produtos_todos_api import ProdutosTodosAPI

BASE_URL = "http://lepapon.api"

# Instâncias das APIs
categoria_api = CategoriaProdutosAPI(BASE_URL)
subcategoria_api = SubCategProdutosAPI(BASE_URL)
produto_model = ProdutosModel(BASE_URL)
produtos_todos_api = ProdutosTodosAPI(BASE_URL)

def inserir_produto_view(page: ft.Page):
    page.route = "/inserir_produto_view"

    # Função para carregar categorias e subcategorias
    def carregar_dados():
        try:
            categorias = categoria_api.get_all()
            subcategorias = subcategoria_api.get_all()
            return categorias or [], subcategorias or []
        except Exception as e:
            print(f"Erro ao carregar dados: {e}")
            return [], []
    
    categorias, subcategorias = carregar_dados()

    # Campos do formulário
    nome_prod_field = ft.TextField(
        label="Nome do Produto",
        hint_text="Digite o nome do produto",
        width=400,
        autofocus=True
    )

    valor_prod_field = ft.TextField(
        label="Valor do Produto",
        hint_text="Digite o valor (ex: 15.50)",
        width=200,
        keyboard_type=ft.KeyboardType.NUMBER
    )

    unit_field = ft.TextField(
        label="Unidade",
        hint_text="Ex: UN, KG, LT",
        width=150
    )

    # Campo para mostrar o próximo ID (readonly)
    proximo_id_field = ft.TextField(
        label="Próximo ID",
        value="Selecione uma subcategoria",
        width=150,
        read_only=True
    )

    categoria_dropdown = ft.Dropdown(
        label="Categoria",
        hint_text="Selecione uma categoria",
        options=[ft.dropdown.Option(str(c["id_CatProd"]), c["nome_CatProd"]) for c in categorias],
        width=300,
        on_change=lambda e: filtrar_subcategorias()
    )

    subcategoria_dropdown = ft.Dropdown(
        label="Subcategoria",
        hint_text="Selecione uma subcategoria",
        width=300,
        on_change=lambda e: carregar_produtos_por_subcategoria()
    )

    # Lista para mostrar produtos da subcategoria selecionada
    produtos_lista = ft.Column([], scroll=ft.ScrollMode.AUTO, height=300)

    # Função para filtrar subcategorias baseadas na categoria selecionada
    def filtrar_subcategorias():
        if categoria_dropdown.value:
            categoria_id = int(categoria_dropdown.value)
            subcategorias_filtradas = [
                sc for sc in subcategorias 
                if sc.get("idCategProd") == categoria_id
            ]
            subcategoria_dropdown.options = [
                ft.dropdown.Option(str(sc["id_SubCategProd"]), sc["nome_SubCategProd"]) 
                for sc in subcategorias_filtradas
            ]
            subcategoria_dropdown.value = None
            # Limpar a lista de produtos quando a categoria muda
            produtos_lista.controls.clear()
            page.update()

    # Função para carregar produtos por subcategoria
    def carregar_produtos_por_subcategoria():
        if not subcategoria_dropdown.value:
            produtos_lista.controls.clear()
            proximo_id_field.value = "Selecione uma subcategoria"
            page.update()
            return
            
        try:
            # Buscar todos os produtos
            todos_produtos = produto_model.listar_produtos()
            
            if todos_produtos:
                subcategoria_id = int(subcategoria_dropdown.value)
                
                # Filtrar produtos pela subcategoria
                produtos_filtrados = [
                    p for p in todos_produtos 
                    if p.get("subCategProd") == subcategoria_id
                ]
                
                # Limpar lista anterior
                produtos_lista.controls.clear()
                
                if produtos_filtrados:
                    # Adicionar cabeçalho
                    produtos_lista.controls.append(
                        ft.Text(
                            f"Produtos na subcategoria ({len(produtos_filtrados)} encontrados):",
                            size=16,
                            weight=ft.FontWeight.W_500
                        )
                    )
                    
                    # Adicionar produtos como cards
                    for produto in produtos_filtrados:
                        card = ft.Card(
                            content=ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Text(
                                            produto.get("nome_Prod", "Nome não informado"),
                                            size=14,
                                            weight=ft.FontWeight.BOLD,
                                            expand=True
                                        ),
                                        ft.Text(
                                            f"R$ {produto.get('Valor_Prod', 0):.2f}",
                                            size=14,
                                            weight=ft.FontWeight.W_500
                                        )
                                    ]),
                                    ft.Text(
                                        f"Unidade: {produto.get('unit', 'N/A')} | ID: {produto.get('id_Prod', 'N/A')}",
                                        size=12,
                                        opacity=0.7
                                    )
                                ], tight=True),
                                padding=10
                            ),
                            elevation=1
                        )
                        produtos_lista.controls.append(card)
                else:
                    produtos_lista.controls.append(
                        ft.Text(
                            "Nenhum produto encontrado nesta subcategoria.",
                            size=14,
                            italic=True,
                            opacity=0.7
                        )
                    )
                
                # Atualizar o campo do próximo ID
                proximo_id = gerar_proximo_id()
                proximo_id_field.value = str(proximo_id)
            else:
                produtos_lista.controls.clear()
                produtos_lista.controls.append(
                    ft.Text(
                        "Erro ao carregar produtos.",
                        size=14
                    )
                )
                
        except Exception as e:
            produtos_lista.controls.clear()
            produtos_lista.controls.append(
                ft.Text(
                    f"Erro ao buscar produtos: {str(e)}",
                    size=14
                )
            )
        
        page.update()

    mensagem = ft.Text()

    # Função para validar os campos
    def validar_campos():
        erros = []
        
        if not nome_prod_field.value or nome_prod_field.value.strip() == "":
            erros.append("Nome do produto é obrigatório")
        
        if not valor_prod_field.value or valor_prod_field.value.strip() == "":
            erros.append("Valor do produto é obrigatório")
        else:
            try:
                float(valor_prod_field.value.replace(',', '.'))
            except ValueError:
                erros.append("Valor do produto deve ser um número válido")
        
        if not unit_field.value or unit_field.value.strip() == "":
            erros.append("Unidade é obrigatória")
        
        if not subcategoria_dropdown.value:
            erros.append("Subcategoria é obrigatória")
        
        return erros

    # Função para limpar o formulário
    def limpar_formulario():
        nome_prod_field.value = ""
        valor_prod_field.value = ""
        unit_field.value = ""
        categoria_dropdown.value = None
        subcategoria_dropdown.value = None
        subcategoria_dropdown.options = []
        produtos_lista.controls.clear()
        proximo_id_field.value = "Selecione uma subcategoria"
        mensagem.value = ""
        page.update()

    # Função para gerar próximo ID baseado na subcategoria
    def gerar_proximo_id():
        try:
            if not subcategoria_dropdown.value:
                return 1
            
            subcategoria_id = int(subcategoria_dropdown.value)
            
            # Buscar todos os produtos
            todos_produtos = produto_model.listar_produtos()
            
            if not todos_produtos:
                # Se não há produtos no sistema, usar subcategoria + 00
                return int(f"{subcategoria_id}00")
            
            # Filtrar produtos pela subcategoria
            produtos_subcategoria = [
                p for p in todos_produtos 
                if p.get("subCategProd") == subcategoria_id
            ]
            
            if not produtos_subcategoria:
                # Se não há produtos nesta subcategoria, usar subcategoria + 00
                return int(f"{subcategoria_id}00")
            
            # Encontrar o maior ID existente na subcategoria
            maior_id = max(
                int(p.get("id_Prod", 0)) for p in produtos_subcategoria
                if p.get("id_Prod") is not None
            )
            
            return maior_id + 1
            
        except Exception as e:
            print(f"Erro ao gerar próximo ID: {e}")
            # Em caso de erro, tentar usar subcategoria + 00
            try:
                if subcategoria_dropdown.value:
                    subcategoria_id = int(subcategoria_dropdown.value)
                    return int(f"{subcategoria_id}00")
                return 1
            except:
                return 1

    # Função para inserir o produto
    def inserir_produto(e):
        erros = validar_campos()
        
        if erros:
            mensagem.value = "Erros encontrados:\n" + "\n".join(f"• {erro}" for erro in erros)
            page.update()
            return

        try:
            # Gerar próximo ID
            proximo_id = gerar_proximo_id()
            
            # Preparar dados do produto
            dados_produto = {
                "id_Prod": proximo_id,
                "subCategProd": int(subcategoria_dropdown.value or "0"),
                "nome_Prod": (nome_prod_field.value or "").strip(),
                "Valor_Prod": float((valor_prod_field.value or "0").replace(',', '.')),
                "unit": (unit_field.value or "").strip().upper()
            }

            # Preparar dados para produtos_todos (apenas campos básicos)
            dados_produtos_todos = {
                "id_Prod": proximo_id,
                "nome_Prod": dados_produto["nome_Prod"],
                "Valor_Prod": dados_produto["Valor_Prod"],
                "unit": dados_produto["unit"]
            }
            
            # PRIMEIRO: Inserir em produtos_todos (tabela pai)
            try:
                resultado_todos = produtos_todos_api.create(dados_produtos_todos)
                
                if resultado_todos and not resultado_todos.get('error'):
                    # SEGUNDO: Inserir produto na API específica (tabela filha)
                    resultado = produto_model.criar_produto(dados_produto)
                    
                    if resultado and not resultado.get('error'):
                        mensagem.value = f"✅ Produto '{dados_produto['nome_Prod']}' inserido com sucesso em ambas as tabelas! (ID: {proximo_id})"
                    else:
                        mensagem.value = f"⚠️ Produto inserido em produtos_todos, mas erro ao inserir na tabela específica (ID: {proximo_id})"
                else:
                    mensagem.value = f"❌ Erro ao inserir em produtos_todos: {resultado_todos.get('error', 'Erro desconhecido')}"
                    return  # Não tenta inserir na tabela específica se falhou na principal
                    
            except Exception as e:
                mensagem.value = f"❌ Erro inesperado ao inserir em produtos_todos: {str(e)}"
                return
            
            # Recarregar a lista de produtos para mostrar o novo produto
            carregar_produtos_por_subcategoria()
            # Limpar apenas os campos do formulário, mantendo a categoria/subcategoria
            nome_prod_field.value = ""
            valor_prod_field.value = ""
            unit_field.value = ""
                
        except Exception as e:
            mensagem.value = f"❌ Erro inesperado: {str(e)}"
        
        page.update()

    # Botões
    btn_inserir = ft.ElevatedButton(
        text="Inserir Produto",
        icon=ft.Icons.ADD,
        on_click=inserir_produto
    )

    btn_limpar = ft.OutlinedButton(
        text="Limpar Formulário",
        icon=ft.Icons.CLEAR,
        on_click=lambda e: limpar_formulario()
    )

    # Layout da view
    return ft.Container(
        content=ft.Row([
            # Coluna esquerda - Formulário de inserção
            ft.Container(
                content=ft.Column([
                    ft.Text(
                        "Inserir Novo Produto",
                        size=28,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Divider(height=20),
                    
                    # Seção de informações básicas
                    ft.Text("Informações do Produto", size=18, weight=ft.FontWeight.W_500),
                    ft.Column([
                        nome_prod_field,
                        ft.Row([valor_prod_field, unit_field, proximo_id_field], spacing=10)
                    ], spacing=10),
                    
                    ft.Divider(height=10),
                    
                    # Seção de categorização
                    ft.Text("Categorização", size=18, weight=ft.FontWeight.W_500),
                    ft.Column([categoria_dropdown, subcategoria_dropdown], spacing=10),
                    
                    ft.Divider(height=20),
                    
                    # Botões de ação
                    ft.Row([btn_inserir, btn_limpar], spacing=20),
                    
                    ft.Divider(height=10),
                    
                    # Mensagem de status
                    mensagem
                    
                ], spacing=15, scroll=ft.ScrollMode.AUTO),
                width=500,
                padding=ft.padding.all(20)
            ),
            
            # Divisor vertical
            ft.VerticalDivider(width=1),
            
            # Coluna direita - Lista de produtos
            ft.Container(
                content=ft.Column([
                    ft.Text(
                        "Produtos Existentes",
                        size=22,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Text(
                        "Selecione uma subcategoria para ver os produtos existentes",
                        size=14,
                        italic=True,
                        opacity=0.7
                    ),
                    ft.Divider(height=10),
                    produtos_lista
                ], spacing=10),
                expand=True,
                padding=ft.padding.all(20)
            )
            
        ], expand=True),
        expand=True
    )
