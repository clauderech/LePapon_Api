import flet as ft
from models.ativos_api import AtivosAPI
import datetime

BASE_URL = "http://lepapon.api"  # ajuste conforme necessário
ativos_api = AtivosAPI(BASE_URL)

def ativos_view(page: ft.Page):
    msg = ft.Text(visible=False)
    id_field = ft.TextField(label="ID", width=100, read_only=True)
    total_inicial_field = ft.TextField(label="Total Inicial", width=150)
    total_final_field = ft.TextField(label="Total Final", width=150)
    data_field = ft.TextField(label="Data", width=120, value=str(datetime.date.today()))

    def limpar_campos():
        id_field.value = ""
        total_inicial_field.value = ""
        total_final_field.value = ""
        data_field.value = str(datetime.date.today())
        page.update()

    def atualizar_lista():
        ativos = ativos_api.get_all()
        if not isinstance(ativos, list):
            ativos = [ativos] if ativos else []
        rows.clear()
        for ativo in ativos:
            rows.append(ft.DataRow([
                ft.DataCell(ft.Text(str(ativo.get("id", "")))),
                ft.DataCell(ft.Text(str(ativo.get("total_inicial", "")))),
                ft.DataCell(ft.Text(str(ativo.get("total_final", "")))),
                ft.DataCell(ft.Text(str(ativo.get("data", "")))),
                ft.DataCell(ft.IconButton(icon=ft.Icons.EDIT, tooltip="Editar", on_click=lambda e, a=ativo: editar_ativo(a))),
                ft.DataCell(ft.IconButton(icon=ft.Icons.DELETE, tooltip="Deletar", on_click=lambda e, a=ativo: deletar_ativo(a)))
            ]))
        if not rows:
            rows.append(ft.DataRow([ft.DataCell(ft.Text("")) for _ in columns]))
        page.update()

    def adicionar_ativo(e):
        data = {
            "total_inicial": total_inicial_field.value,
            "total_final": total_final_field.value,
            "data": data_field.value
        }
        resp = ativos_api.create(data)
        print(resp)  # Debug: verificar a resposta da API
        msg.value = "Ativo adicionado com sucesso!"
        msg.color = "green"
        msg.visible = True
        limpar_campos()
        atualizar_lista()

    def editar_ativo(ativo):
        id_field.value = str(ativo.get("id", ""))
        total_inicial_field.value = str(ativo.get("total_inicial", ""))
        total_final_field.value = str(ativo.get("total_final", ""))
        data_field.value = str(ativo.get("data", ""))
        page.update()

    def atualizar_ativo(e):
        if not id_field.value:
            msg.value = "Selecione um ativo para atualizar."
            msg.color = "red"
            msg.visible = True
            page.update()
            return
        data = {
            "total_inicial": total_inicial_field.value,
            "total_final": total_final_field.value,
            "data": data_field.value
        }
        ativos_api.update(id_field.value, data)
        msg.value = "Ativo atualizado com sucesso!"
        msg.color = "green"
        msg.visible = True
        limpar_campos()
        atualizar_lista()

    def deletar_ativo(ativo):
        ativos_api.delete(ativo.get("id"))
        msg.value = "Ativo deletado com sucesso!"
        msg.color = "green"
        msg.visible = True
        limpar_campos()
        atualizar_lista()

    columns = [
        ft.DataColumn(ft.Text("ID")),
        ft.DataColumn(ft.Text("Total Inicial")),
        ft.DataColumn(ft.Text("Total Final")),
        ft.DataColumn(ft.Text("Data")),
        ft.DataColumn(ft.Text("Editar")),
        ft.DataColumn(ft.Text("Deletar")),
    ]
    rows = []
    atualizar_lista()

    return ft.Column([
        ft.Text("Gestão de Ativos", style=ft.TextThemeStyle.HEADLINE_SMALL),
        ft.Row([
            id_field,
            total_inicial_field,
            total_final_field,
            data_field,
            ft.ElevatedButton("Adicionar", on_click=adicionar_ativo),
            ft.ElevatedButton("Atualizar", on_click=atualizar_ativo),
            ft.ElevatedButton("Limpar", on_click=lambda e: limpar_campos()),
        ]),
        msg,
        ft.Divider(),
        ft.Column([
                ft.DataTable(columns=columns, rows=rows, expand=True)
            ], scroll=ft.ScrollMode.AUTO, height=700, width=800)
    ])
