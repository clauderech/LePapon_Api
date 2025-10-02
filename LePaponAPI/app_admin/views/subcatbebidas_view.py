import flet as ft
from models.subcategoriabebidas_api import SubCategoriaBebidasAPI

BASE_URL = "http://lepapon.novo:3000"
subcategoriabebidas_api = SubCategoriaBebidasAPI(BASE_URL)

def subcatbebidas_view(page: ft.Page):
    try:
        data = subcategoriabebidas_api.get_all()
        if not isinstance(data, list):
            data = [data] if data else []
    except Exception as e:
        return ft.Text(f"Erro ao buscar subcategorias de bebidas: {e}", color="red")
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
    return ft.Column([
        ft.Text("Lista de Subcategorias de Bebidas", style=ft.TextThemeStyle.HEADLINE_SMALL),
        ft.DataTable(columns=columns, rows=rows)
    ])
