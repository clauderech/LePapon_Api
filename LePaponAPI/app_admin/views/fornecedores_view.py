import flet as ft
from models.fornecedores_api import FornecedoresAPI

api = FornecedoresAPI(base_url='http://lepapon.api')

def fornecedores_view(page: ft.Page):
    fornecedores = api.get_all()

    def atualizar():
        container = page.views[-1].controls[0]
        if isinstance(container, (ft.Column, ft.Row)) and len(container.controls) > 0:
            inner_container = container.controls[0]
            if isinstance(inner_container, (ft.Column, ft.Row)):
                inner_container.controls.clear()
                inner_container.controls.append(listar_fornecedores())
        page.update()

    def listar_fornecedores():
        return ft.Column([
            ft.Row([
                ft.Text("Fornecedores", size=24),
                ft.ElevatedButton("Novo Fornecedor", on_click=lambda e: page.go("/fornecedores/novo"))
            ]),
            ft.Column([
                ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("ID")),
                        ft.DataColumn(ft.Text("Nome")),
                        ft.DataColumn(ft.Text("Ações")),
                    ],
                    rows=[
                        ft.DataRow([
                            ft.DataCell(ft.Text(str(f["id"]))),
                            ft.DataCell(ft.Text(f["nome"])),
                            ft.DataCell(ft.Row([
                                ft.IconButton("edit", on_click=lambda e, id=f["id"]: editar_fornecedor(id)),
                                ft.IconButton("delete", on_click=lambda e, id=f["id"]: deletar_fornecedor(id)),
                            ])),
                        ]) for f in fornecedores
                    ]
                )
            ], scroll=ft.ScrollMode.AUTO, expand=True, height=800)
        ])

    def novo_fornecedor_view():
        nome = ft.TextField(label="Nome", width=300)
        def salvar(e):
            res_forn = api.create({"nome": nome.value})
            print(f"Fornecedor criado: {res_forn}")
            page.go("/fornecedores")
        return ft.Column([
            ft.Text("Novo Fornecedor", size=20),
            nome,
            ft.Row([
                ft.ElevatedButton("Salvar", on_click=salvar),
                ft.ElevatedButton("Voltar", on_click=lambda e: page.go("/fornecedores"))
            ])
        ])

    def editar_fornecedor(id):
        fornecedor = api.get_by_id(id)
        nome = ft.TextField(label="Nome", value=fornecedor["nome"], width=300)
        def salvar(e):
            api.update(id, {"nome": nome.value})
            page.go("/fornecedores")
        container = page.views[-1].controls[0]
        if isinstance(container, (ft.Column, ft.Row)) and len(container.controls) > 0 and isinstance(container.controls[0], (ft.Column, ft.Row)):
            container.controls[0].controls.clear()
            container.controls[0].controls.append(
                ft.Column([
                    ft.Text("Editar Fornecedor", size=20),
                    nome,
                    ft.Row([
                        ft.ElevatedButton("Salvar", on_click=salvar),
                        ft.ElevatedButton("Voltar", on_click=lambda e: page.go("/fornecedores"))
                    ])
                ])
            )
            page.update()

    def deletar_fornecedor(id):
        api.delete(id)
        page.go("/fornecedores")

    if page.route == "/fornecedores/novo":
        return novo_fornecedor_view()
    else:
        return listar_fornecedores()
