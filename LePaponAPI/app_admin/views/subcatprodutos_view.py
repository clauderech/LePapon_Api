import flet as ft
from models.subcategprodutos_api import SubCategProdutosAPI

BASE_URL = "http://lepapon.novo:3000"
subcategprodutos_api = SubCategProdutosAPI(BASE_URL)

def subcatprodutos_view(page: ft.Page):
    try:
        data = subcategprodutos_api.get_all()
        if not isinstance(data, list):
            data = [data] if data else []
    except Exception as e:
        return ft.Text(f"Erro ao buscar subcategorias de produtos: {e}", color="red")
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

    # Formulário CRUD de subcategoria
    id_subcat = ft.TextField(label="ID", width=100, on_focus=limpar_ao_focar)
    nome_subcat = ft.TextField(label="Nome", width=200, on_focus=limpar_ao_focar)
    msg = ft.Text(visible=False)

    def criar_subcat(e):
        try:
            nova = {"id": id_subcat.value, "nome": nome_subcat.value}
            resp = subcategprodutos_api.create(nova)
            msg.value = "Subcategoria criada com sucesso!"
            msg.color = "green"
            msg.visible = True
            id_subcat.value = nome_subcat.value = ""
            page.update()
        except Exception as ex:
            msg.value = f"Erro ao criar subcategoria: {ex}"
            msg.color = "red"
            msg.visible = True
            page.update()

    def editar_subcat(e):
        try:
            if not id_subcat.value:
                msg.value = "Selecione uma subcategoria para editar."
                msg.color = "orange"
                msg.visible = True
                page.update()
                return
            nova = {"nome": nome_subcat.value}
            resp = subcategprodutos_api.update(id_subcat.value, nova)
            msg.value = "Subcategoria atualizada com sucesso!"
            msg.color = "green"
            msg.visible = True
            page.update()
        except Exception as ex:
            msg.value = f"Erro ao editar subcategoria: {ex}"
            msg.color = "red"
            msg.visible = True
            page.update()

    def deletar_subcat(e):
        try:
            if not id_subcat.value:
                msg.value = "Selecione uma subcategoria para deletar."
                msg.color = "orange"
                msg.visible = True
                page.update()
                return
            resp = subcategprodutos_api.delete(id_subcat.value)
            msg.value = "Subcategoria deletada com sucesso!"
            msg.color = "green"
            msg.visible = True
            id_subcat.value = nome_subcat.value = ""
            page.update()
        except Exception as ex:
            msg.value = f"Erro ao deletar subcategoria: {ex}"
            msg.color = "red"
            msg.visible = True
            page.update()

    # Dropdown para seleção de subcategoria
    opcoes_subcats = []
    if data:
        for row in data:
            if isinstance(row, dict):
                label = f"{row.get('id', '')} - {row.get('nome', '')}"
                value = str(row.get('id', ''))
                opcoes_subcats.append(ft.dropdown.Option(text=label, key=value))
    dropdown_subcats = ft.Dropdown(options=opcoes_subcats, label="Selecionar Subcategoria", width=350)

    def selecionar_subcat(e):
        valor = dropdown_subcats.value
        for row in data:
            if str(row.get('id', '')) == valor:
                id_subcat.value = str(row.get('id', ''))
                nome_subcat.value = str(row.get('nome', ''))
                break
        page.update()
    dropdown_subcats.on_change = selecionar_subcat

    return ft.Column([
        ft.Text("Subcategorias de Produtos", style=ft.TextThemeStyle.HEADLINE_SMALL),
        dropdown_subcats,
        ft.Divider(),
        ft.Text("Cadastrar/Editar Subcategoria", style=ft.TextThemeStyle.TITLE_MEDIUM),
        ft.Row([id_subcat, nome_subcat]),
        ft.Row([
            ft.ElevatedButton("Criar", on_click=criar_subcat),
            ft.ElevatedButton("Editar", on_click=editar_subcat),
            ft.ElevatedButton("Deletar", on_click=deletar_subcat),
            msg
        ])
    ])
