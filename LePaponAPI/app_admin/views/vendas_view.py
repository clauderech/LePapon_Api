import flet as ft
from models.vendas_api import VendasAPI
from models.produtos_todos_api import ProdutosTodosAPI
import datetime
import pandas as pd

BASE_URL = "http://lepapon.novo:3000"
vendas_api = VendasAPI(BASE_URL)
produtos_todos_api = ProdutosTodosAPI(BASE_URL)

def vendas_view(page: ft.Page):
    msg = ft.Text(visible=False)
    # Filtros de data
    data_inicial = ft.TextField(
        label="Data Inicial",
        value=str(datetime.date.today()),
        on_change=lambda e: filtrar_vendas_periodo(),
        width=140,
        hint_text="AAAA-MM-DD"
    )
    data_final = ft.TextField(
        label="Data Final",
        value=str(datetime.date.today()),
        on_change=lambda e: filtrar_vendas_periodo(),
        width=140,
        hint_text="AAAA-MM-DD"
    )
    total_vendas_label = ft.Text("Total do período: 0.00", style=ft.TextThemeStyle.TITLE_MEDIUM)
    tabela_ref = ft.Ref[ft.DataTable]()

    def filtrar_vendas_periodo():
        di = data_inicial.value
        df = data_final.value
        if not di or not df:
            return
        di_str = str(di)
        df_str = str(df)
        try:
            vendas = vendas_api.get_all()
            
            if not isinstance(vendas, list):
                vendas = [vendas] if vendas else []
            # Busca produtos todos
            produtos_todos = produtos_todos_api.get_all()
            if not isinstance(produtos_todos, list):
                produtos_todos = [produtos_todos] if produtos_todos else []
            # Converte para DataFrame
            vendas_df = pd.DataFrame(vendas)
            produtos_df = pd.DataFrame(produtos_todos)
            # Faz o merge pelo campo de produto (ajuste o nome se necessário)
            if not vendas_df.empty and not produtos_df.empty:
                merged_df = vendas_df.merge(
                    produtos_df[['id_Prod', 'nome_Prod', 'Valor_Prod']],
                    left_on='id_Prod', right_on='id_Prod', how='left'
                )
            else:
                merged_df = vendas_df
            # Filtra por data
            vendas_periodo = merged_df[(merged_df['data'] >= di_str) & (merged_df['data'] <= df_str)]
            # Calcula sub_total e renomeia Valor_Prod para V_unit
            if not vendas_periodo.empty:
                vendas_periodo = vendas_periodo.copy()
                vendas_periodo['V_unit'] = vendas_periodo['Valor_Prod']
                vendas_periodo['sub_total'] = vendas_periodo.apply(
                    lambda row: float(row.get('qtd', 0)) * float(str(row.get('V_unit', 0)).replace(",", ".")), axis=1
                )
            # Seleciona apenas os campos desejados na ordem correta
            campos_exibir = ['hora', 'qtd', 'nome_Prod', 'V_unit', 'sub_total']
            colunas_legenda = {
                'hora': 'Hora',
                'qtd': 'Qtd',
                'nome_Prod': 'Produto',
                'V_unit': 'V_unit',
                'sub_total': 'Subtotal'
            }
            if not vendas_periodo.empty:
                vendas_periodo = vendas_periodo[campos_exibir]
                columns = [ft.DataColumn(ft.Text(colunas_legenda[c])) for c in campos_exibir]
            else:
                columns = [ft.DataColumn(ft.Text("Hora"))]
            rows = []
            total = 0.0
            for _, venda in vendas_periodo.iterrows():
                row = [ft.DataCell(ft.Text(str(venda.get(c, "")))) for c in campos_exibir]
                rows.append(ft.DataRow(row))
                try:
                    total += float(str(venda.get("sub_total", 0)).replace(",", "."))
                except:
                    pass
            if not rows:
                rows = [ft.DataRow([ft.DataCell(ft.Text("")) for _ in columns])]
            tabela_ref.current.columns = columns
            tabela_ref.current.rows = rows
            total_vendas_label.value = f"Total do período: {total:.2f}"
            page.update()
        except Exception as e:
            msg.value = f"Erro ao buscar vendas: {e}"
            msg.color = "red"
            msg.visible = True
            page.update()

    # Inicializa tabela vazia
    tabela = ft.DataTable(ref=tabela_ref, columns=[ft.DataColumn(ft.Text("id"))], rows=[], expand=True)
    # Carrega vendas do dia atual ao abrir
    filtrar_vendas_periodo()

    return ft.Column([
        ft.Text("Lista de Vendas", style=ft.TextThemeStyle.HEADLINE_SMALL),
        ft.Row([
            data_inicial,
            data_final,
            total_vendas_label
        ]),       
        ft.Column(
            [tabela,        
            msg,
            ft.Divider()],
            scroll=ft.ScrollMode.ALWAYS,
            height=600,
            width=800,
        ),
        
    ], spacing=10, expand=True)
