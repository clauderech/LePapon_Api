import flet as ft
from models.controle_semanal_api import ControleSemanalAPI
from models.controle_semanal import ControleSemanal
import datetime
from utils.date_tz_converter import DateTZConverter

BASE_URL = "http://lepapon.api:3000"
controle_semanal_api = ControleSemanalAPI(BASE_URL)
controle_semanal = ControleSemanal(BASE_URL)

def controle_semanal_view(page: ft.Page):
    msg = ft.Text(visible=False)
    data_field = ft.TextField(label="Data (YYYY-MM-DD)", width=150, value=str(datetime.date.today()))

    # Formulário para novo registro
    data_inicial_field = ft.TextField(label="Data Inicial (YYYY-MM-DD)", width=150)
    data_final_field = ft.TextField(label="Data Final (YYYY-MM-DD)", width=150)
    total_vendas_field = ft.TextField(label="Total Vendas", width=120, input_filter=ft.NumbersOnlyInputFilter())
    total_crediario_field = ft.TextField(label="Total Crediário", width=120, input_filter=ft.NumbersOnlyInputFilter())
    total_recebido_field = ft.TextField(label="Total Recebido", width=120, input_filter=ft.NumbersOnlyInputFilter())
    total_despesas_field = ft.TextField(label="Total Despesas", width=120, input_filter=ft.NumbersOnlyInputFilter())
    msg_form = ft.Text(visible=False)

    def salvar_registro(e=None):
        try:
            data = {
                "data_inicial": (data_inicial_field.value or "").strip(),
                "data_final": (data_final_field.value or "").strip(),
                "total_vendas": float(total_vendas_field.value or 0),
                "total_crediario": float(total_crediario_field.value or 0),
                "total_recebido": float(total_recebido_field.value or 0),
                "total_despesas": float(total_despesas_field.value or 0),
            }
            controle_semanal_api.create(data)
            msg_form.value = "Registro salvo com sucesso!"
            msg_form.color = "green"
            msg_form.visible = True
            # Limpa campos
            data_inicial_field.value = ""
            data_final_field.value = ""
            total_vendas_field.value = ""
            total_crediario_field.value = ""
            total_recebido_field.value = ""
            total_despesas_field.value = ""
            page.update()
        except Exception as ex:
            msg_form.value = f"Erro ao salvar: {ex}"
            msg_form.color = "red"
            msg_form.visible = True
            page.update()

    columns = [
        ft.DataColumn(ft.Text("ID")),
        ft.DataColumn(ft.Text("Data Inicial")),
        ft.DataColumn(ft.Text("Data Final")),
        ft.DataColumn(ft.Text("Total Vendas")),
        ft.DataColumn(ft.Text("Total Crediário")),
        ft.DataColumn(ft.Text("Total Recebido")),
        ft.DataColumn(ft.Text("Total Despesas")),
    ]
    rows = []

    def buscar_por_data(e=None):
        data_str = (data_field.value or "").strip() or str(datetime.date.today())
        try:
            registros = controle_semanal_api.get_by_data(data_str)
            if not isinstance(registros, list):
                registros = [registros] if registros else []
            rows.clear()
            
            for reg in registros:
                datainicial = DateTZConverter.iso_to_date(reg.get("data_inicial", ""))
                datafinal = DateTZConverter.iso_to_date(reg.get("data_final", ""))
                rows.append(ft.DataRow([
                    ft.DataCell(ft.Text(str(reg.get("id", "")))),
                    ft.DataCell(ft.Text(str(datainicial))),
                    ft.DataCell(ft.Text(str(datafinal))),
                    ft.DataCell(ft.Text(str(reg.get("total_vendas", "")))),
                    ft.DataCell(ft.Text(str(reg.get("total_crediario", "")))),
                    ft.DataCell(ft.Text(str(reg.get("total_recebido", "")))),
                    ft.DataCell(ft.Text(str(reg.get("total_despesas", "")))),
                ]))
            if not rows:
                rows.append(ft.DataRow([ft.DataCell(ft.Text("")) for _ in columns]))
            msg.value = f"{len(registros)} registro(s) encontrado(s) para {data_str}."
            msg.color = "blue"
            msg.visible = True
            page.update()
        except Exception as ex:
            msg.value = f"Erro ao buscar: {ex}"
            msg.color = "red"
            msg.visible = True
            page.update()

    def buscar_ultima_semana(e=None):
        try:
            reg = controle_semanal_api.get_last()
            rows.clear()
            if reg:
                if isinstance(reg, list):
                    reg = reg[0] if reg else {}
                datainicial = DateTZConverter.iso_to_date(reg.get("data_inicial", ""))
                datafinal = DateTZConverter.iso_to_date(reg.get("data_final", ""))
                rows.append(ft.DataRow([
                    ft.DataCell(ft.Text(str(reg.get("id", "")))),
                    ft.DataCell(ft.Text(str(datainicial))),
                    ft.DataCell(ft.Text(str(datafinal))),
                    ft.DataCell(ft.Text(str(reg.get("total_vendas", "")))),
                    ft.DataCell(ft.Text(str(reg.get("total_crediario", "")))),
                    ft.DataCell(ft.Text(str(reg.get("total_recebido", "")))),
                    ft.DataCell(ft.Text(str(reg.get("total_despesas", "")))),
                ]))
                msg.value = "Última semana carregada."
                msg.color = "blue"
            else:
                rows.append(ft.DataRow([ft.DataCell(ft.Text("")) for _ in columns]))
                msg.value = "Nenhum registro encontrado para a última semana."
                msg.color = "orange"
            msg.visible = True
            page.update()
        except Exception as ex:
            msg.value = f"Erro ao buscar última semana: {ex}"
            msg.color = "red"
            msg.visible = True
            page.update()

    def preencher_automatico(e=None):
        try:
            hoje = datetime.date.today()
            ontem = hoje - datetime.timedelta(days=1)
            data_final_field.value = ontem.isoformat()
            data_inicial_field.value = (ontem - datetime.timedelta(days=6)).isoformat()
            resultado = controle_semanal.consultar()
            total_vendas_field.value = str(resultado.get('total_vendas', 0))
            total_crediario_field.value = str(resultado.get('total_crediario', 0))
            total_recebido_field.value = str(resultado.get('total_recebido', 0))
            total_despesas_field.value = str(resultado.get('total_despesas', 0))
            msg_form.value = "Campos preenchidos automaticamente com os últimos 7 dias (excluindo hoje)."
            msg_form.color = "blue"
            msg_form.visible = True
            page.update()
        except Exception as ex:
            msg_form.value = f"Erro ao preencher automaticamente: {ex}"
            msg_form.color = "red"
            msg_form.visible = True
            page.update()

    def preencher_por_periodo(e=None):
        try:
            data_inicio = (data_inicial_field.value or "").strip()
            data_fim = (data_final_field.value or "").strip()
            if not data_inicio or not data_fim:
                msg_form.value = "Preencha as datas inicial e final."
                msg_form.color = "orange"
                msg_form.visible = True
                page.update()
                return
            # Substitua por um método válido da classe ControleSemanal, por exemplo consultar_periodo pode ser implementado assim:
            resultado = controle_semanal.consultar_periodo(data_inicio, data_fim)
            print(resultado)  # Debugging line to check the result
            if not resultado:
                msg_form.value = "Nenhum registro encontrado para o período especificado."
                msg_form.color = "orange"
                msg_form.visible = True
                page.update()
                return
            total_vendas_field.value = str(resultado.get('total_vendas', 0))
            total_crediario_field.value = str(resultado.get('total_crediario', 0))
            total_recebido_field.value = str(resultado.get('total_recebido', 0))
            total_despesas_field.value = str(resultado.get('total_despesas', 0))
            msg_form.value = f"Campos preenchidos para o período de {data_inicio} até {data_fim}."
            msg_form.color = "blue"
            msg_form.visible = True
            page.update()
        except Exception as ex:
            msg_form.value = f"Erro ao preencher por período: {ex}"
            msg_form.color = "red"
            msg_form.visible = True
            page.update()
       

    def buscar_ultimos_cinco(e=None):
        try:
            registros = controle_semanal_api.get_lastfive()
            if not isinstance(registros, list):
                registros = [registros] if registros else []
            rows.clear()
            for reg in registros:
                datainicial = DateTZConverter.iso_to_date(reg.get("data_inicial", ""))
                datafinal = DateTZConverter.iso_to_date(reg.get("data_final", ""))
                rows.append(ft.DataRow([
                    ft.DataCell(ft.Text(str(reg.get("id", "")))),
                    ft.DataCell(ft.Text(str(datainicial))),
                    ft.DataCell(ft.Text(str(datafinal))),
                    ft.DataCell(ft.Text(str(reg.get("total_vendas", "")))),
                    ft.DataCell(ft.Text(str(reg.get("total_crediario", "")))),
                    ft.DataCell(ft.Text(str(reg.get("total_recebido", "")))),
                    ft.DataCell(ft.Text(str(reg.get("total_despesas", "")))),
                ]))
            if not rows:
                rows.append(ft.DataRow([ft.DataCell(ft.Text("")) for _ in columns]))
            msg.value = f"{len(registros)} registro(s) mais recentes carregados."
            msg.color = "blue"
            msg.visible = True
            page.update()
        except Exception as ex:
            msg.value = f"Erro ao buscar últimos 5 registros: {ex}"
            msg.color = "red"
            msg.visible = True
            page.update()

    return ft.Column([
        ft.Text("Controle Semanal", style=ft.TextThemeStyle.HEADLINE_SMALL),
        ft.Container(
            content=ft.Column([
                ft.Text("Adicionar novo registro", weight=ft.FontWeight.BOLD),
                ft.Row([
                    data_inicial_field,
                    data_final_field,
                    total_vendas_field,
                    total_crediario_field,
                    total_recebido_field,
                    total_despesas_field,
                    ft.ElevatedButton("Salvar", on_click=salvar_registro),
                    ft.ElevatedButton("Preencher Últimos 7 Dias", on_click=preencher_automatico),
                    ft.ElevatedButton("Preencher pelo Período", on_click=preencher_por_periodo),
                ]),
                msg_form,
                ft.Divider(),
            ]),
            bgcolor="#f5f5f5",
            padding=10,
            border_radius=8,
        ),
        ft.Row([
            data_field,
            ft.ElevatedButton("Buscar por Data", on_click=buscar_por_data),
            ft.ElevatedButton("Buscar Última Semana", on_click=buscar_ultima_semana),
                ft.ElevatedButton("Buscar Últimos 5 Registros", on_click=buscar_ultimos_cinco),
        ]),
        msg,
        ft.Divider(),
        ft.DataTable(columns=columns, rows=rows, expand=True)
    ])
