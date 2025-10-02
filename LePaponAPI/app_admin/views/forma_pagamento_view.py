import flet as ft
from models.forma_pagamento_api import FormaPagamentoAPI

api = FormaPagamentoAPI(base_url='http://lepapon.api')

def forma_pagamento_view(page: ft.Page):
    formas = api.get_all()

    def listar_formas():
        return ft.Column([
            ft.Row([
                ft.Text("Formas de Pagamento", size=24),
                ft.ElevatedButton("Nova Forma de Pagamento", on_click=lambda e: page.go("/forma_pagamento/novo"))
            ]),
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
                            ft.IconButton("edit", on_click=lambda e, id=f["id"]: editar_forma(id)),
                            ft.IconButton("delete", on_click=lambda e, id=f["id"]: deletar_forma(id)),
                        ])),
                    ]) for f in formas
                ]
            )
        ])

    def nova_forma_view():
        nome = ft.TextField(label="Nome", width=300)
        def salvar(e):
            api.create({"nome": nome.value})
            page.go("/forma_pagamento")
        return ft.Column([
            ft.Text("Nova Forma de Pagamento", size=20),
            nome,
            ft.Row([
                ft.ElevatedButton("Salvar", on_click=salvar),
                ft.ElevatedButton("Voltar", on_click=lambda e: page.go("/forma_pagamento"))
            ])
        ])

    def editar_forma(id):
        forma = api.get_by_id(id)
        nome = ft.TextField(label="Nome", value=forma["nome"], width=300)
        def salvar(e):
            api.update(id, {"nome": nome.value})
            page.go("/forma_pagamento")
        page.views[-1].controls.clear()
        page.views[-1].controls.append(
            ft.Column([
                ft.Text("Editar Forma de Pagamento", size=20),
                nome,
                ft.Row([
                    ft.ElevatedButton("Salvar", on_click=salvar),
                    ft.ElevatedButton("Voltar", on_click=lambda e: page.go("/forma_pagamento"))
                ])
            ])
        )
        page.update()

    def deletar_forma(id):
        api.delete(id)
        page.go("/forma_pagamento")

    if page.route == "/forma_pagamento/novo":
        return nova_forma_view()
    else:
        return listar_formas()
