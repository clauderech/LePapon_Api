import flet as ft
from models.categoriaprodutos_api import CategoriaProdutosAPI

BASE_URL = "http://lepapon.novo:3000"
categoria_api = CategoriaProdutosAPI(BASE_URL)

def categorias_view(page: ft.Page):
    try:
        data = categoria_api.get_all()
        if not isinstance(data, list):
            data = [data] if data else []
    except Exception as e:
        return ft.Text(f"Erro ao buscar categorias: {e}", color="red")
    columns = [ft.DataColumn(ft.Text("id"))]
    if data and isinstance(data[0], dict):
        columns = [ft.DataColumn(ft.Text(str(key))) for key in data[0].keys()]
    rows = []
    if data:
        for row in data:
            if isinstance(row, dict):
                rows.append(ft.DataRow([
                    ft.DataCell(ft.Text(str(row.get(str(col.label.data), "")))) for col in columns
                ]))
    if not rows:
        rows = [ft.DataRow([ft.DataCell(ft.Text("")) for _ in columns])]
    
    # Função para limpar campo ao focar
    def limpar_ao_focar(e):
        e.control.value = ""
        page.update()

    # Formulário CRUD de categoria
    id_categoria = ft.TextField(label="ID", width=100, on_focus=limpar_ao_focar)
    nome_categoria = ft.TextField(label="Nome", width=200, on_focus=limpar_ao_focar)
    msg = ft.Text(visible=False)

    def criar_categoria(e):
        try:
            nova = {"id": id_categoria.value, "nome": nome_categoria.value}
            resp = categoria_api.create(nova)
            msg.value = "Categoria criada com sucesso!"
            msg.color = "green"
            msg.visible = True
            id_categoria.value = nome_categoria.value = ""
            page.update()
        except Exception as ex:
            msg.value = f"Erro ao criar categoria: {ex}"
            msg.color = "red"
            msg.visible = True
            page.update()

    def editar_categoria(e):
        try:
            if not id_categoria.value:
                msg.value = "Selecione uma categoria para editar."
                msg.color = "orange"
                msg.visible = True
                page.update()
                return
            nova = {"nome": nome_categoria.value}
            resp = categoria_api.update(id_categoria.value, nova)
            msg.value = "Categoria atualizada com sucesso!"
            msg.color = "green"
            msg.visible = True
            page.update()
        except Exception as ex:
            msg.value = f"Erro ao editar categoria: {ex}"
            msg.color = "red"
            msg.visible = True
            page.update()

    def deletar_categoria(e):
        try:
            if not id_categoria.value:
                msg.value = "Selecione uma categoria para deletar."
                msg.color = "orange"
                msg.visible = True
                page.update()
                return
            resp = categoria_api.delete(id_categoria.value)
            msg.value = "Categoria deletada com sucesso!"
            msg.color = "green"
            msg.visible = True
            id_categoria.value = nome_categoria.value = ""
            page.update()
        except Exception as ex:
            msg.value = f"Erro ao deletar categoria: {ex}"
            msg.color = "red"
            msg.visible = True
            page.update()

    # Dropdown para seleção de categoria
    opcoes_categorias = []
    if data:
        for row in data:
            if isinstance(row, dict):
                label = f"{row.get('id', '')} - {row.get('nome', '')}"
                value = str(row.get('id', ''))
                opcoes_categorias.append(ft.dropdown.Option(text=label, key=value))
    dropdown_categorias = ft.Dropdown(options=opcoes_categorias, label="Selecionar Categoria", width=350)

    def selecionar_categoria(e):
        valor = dropdown_categorias.value
        for row in data:
            if str(row.get('id', '')) == valor:
                id_categoria.value = str(row.get('id', ''))
                nome_categoria.value = str(row.get('nome', ''))
                break
        page.update()
    dropdown_categorias.on_change = selecionar_categoria

    return ft.Column([
        ft.Text("Categorias", style=ft.TextThemeStyle.HEADLINE_SMALL),
        dropdown_categorias,
        ft.Divider(),
        ft.Text("Cadastrar/Editar Categoria", style=ft.TextThemeStyle.TITLE_MEDIUM),
        ft.Row([id_categoria, nome_categoria]),
        ft.Row([
            ft.ElevatedButton("Criar", on_click=criar_categoria),
            ft.ElevatedButton("Editar", on_click=editar_categoria),
            ft.ElevatedButton("Deletar", on_click=deletar_categoria),
            msg
        ]),
        ft.DataTable(columns=columns, rows=rows)
    ])
