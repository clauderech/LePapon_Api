import flet as ft
from models.controle_diario import ControleDiario
from models.controle_diario_api import ControleDiarioAPI
import datetime

BASE_URL = "http://lepapon.api:3000"
controle_diario = ControleDiario(BASE_URL)
controle_diario_api = ControleDiarioAPI(BASE_URL)

def controle_diario_view(page: ft.Page):
    msg = ft.Text(visible=False)
    data_field = ft.TextField(label="Data (YYYY-MM-DD)", width=150, value=str(datetime.date.today()))

    def consultar_e_exibir(e=None):
        data_str = (data_field.value or "").strip() or str(datetime.date.today())
        try:
            resultado = controle_diario.consultar(data_str)
            msg.value = (
                f"Consulta de {data_str}:\n"
                f"Total Vendas: {resultado['total_vendas']} | "
                f"Total Crediário: {resultado['total_crediario']} | "
                f"Total Recebido: {resultado['total_recebido']} | "
                f"Total Despesas: {resultado['total_despesas']}"
            )
            msg.color = "blue"
            msg.visible = True
            page.update()
        except Exception as ex:
            msg.value = f"Erro ao consultar: {ex}"
            msg.color = "red"
            msg.visible = True
            page.update()

    def registrar_no_db(e=None):
        data_str = (data_field.value or "").strip() or str(datetime.date.today())
        try:
            resultado = controle_diario.registrar(data_str)
            msg.value = f"Registro salvo para {data_str}!"
            msg.color = "green"
            msg.visible = True
            page.update()
        except Exception as ex:
            msg.value = f"Erro ao registrar: {ex}"
            msg.color = "red"
            msg.visible = True
            page.update()

    def atualizar_lista():
        try:
            data_str = (data_field.value or "").strip() or str(datetime.date.today())
            registros = controle_diario_api.get_by_data(data_str)
            if not isinstance(registros, list):
                registros = [registros] if registros else []
            rows.clear()
            for reg in registros:
                rows.append(ft.DataRow([
                    ft.DataCell(ft.Text(str(reg.get("id", "")))),
                    ft.DataCell(ft.Text(str(reg.get("data", "")))),
                    ft.DataCell(ft.Text(str(reg.get("total_vendas", "")))),
                    ft.DataCell(ft.Text(str(reg.get("total_crediario", "")))),
                    ft.DataCell(ft.Text(str(reg.get("total_recebido", "")))),
                    ft.DataCell(ft.Text(str(reg.get("total_despesas", "")))),
                ]))
            if not rows:
                rows.append(ft.DataRow([ft.DataCell(ft.Text("")) for _ in columns]))
            page.update()
        except Exception as ex:
            msg.value = f"Erro ao carregar registros: {ex}"
            msg.color = "red"
            msg.visible = True
            page.update()

    columns = [
        ft.DataColumn(ft.Text("ID")),
        ft.DataColumn(ft.Text("Data")),
        ft.DataColumn(ft.Text("Total Vendas")),
        ft.DataColumn(ft.Text("Total Crediário")),
        ft.DataColumn(ft.Text("Total Recebido")),
        ft.DataColumn(ft.Text("Total Despesas")),
    ]
    rows = []
    atualizar_lista()

    return ft.Column([
        ft.Text("Controle Diário", style=ft.TextThemeStyle.HEADLINE_SMALL),
        ft.Row([
            data_field,
            ft.ElevatedButton("Consultar", on_click=lambda e: [consultar_e_exibir(e), atualizar_lista()]),
            ft.ElevatedButton("Registrar no DB", on_click=lambda e: [registrar_no_db(e), atualizar_lista()]),
        ]),
        msg,
        ft.Divider(),
        ft.Text("Registros Controle Diário:", style=ft.TextThemeStyle.TITLE_MEDIUM),
        ft.DataTable(columns=columns, rows=rows, expand=True)
    ])
