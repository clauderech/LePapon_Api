import flet as ft
from models.despesas_diarias_api import DespesasDiariasAPI
from models.fornecedores_api import FornecedoresAPI
from models.forma_pagamento_api import FormaPagamentoAPI


despesas_api = DespesasDiariasAPI(base_url='http://lepapon.api')
fornecedores_api = FornecedoresAPI(base_url='http://lepapon.api')
forma_pagamento_api = FormaPagamentoAPI(base_url='http://lepapon.api')

def despesas_diarias_view(page: ft.Page):
    despesas = despesas_api.get_all()
    fornecedores = {f['id']: f['nome'] for f in fornecedores_api.get_all()}
    formas_pagamento = {f['id']: f['nome'] for f in forma_pagamento_api.get_all()}

    main_container = ft.Column()

    def atualizar():
        main_container.controls.clear()
        main_container.controls.append(listar_despesas())
        page.update()

    def listar_despesas():
        return ft.Column([
            ft.Row([
                ft.Text("Despesas Diárias", size=24),
                ft.ElevatedButton("Nova Despesa", on_click=lambda e: page.go("/despesas_diarias/novo"))
            ]),
            ft.Column([
                ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("ID")),
                        ft.DataColumn(ft.Text("Fornecedor")),
                        ft.DataColumn(ft.Text("Descrição")),
                        ft.DataColumn(ft.Text("Valor")),
                        ft.DataColumn(ft.Text("Data")),
                        ft.DataColumn(ft.Text("Forma Pagamento")),
                        ft.DataColumn(ft.Text("Ações")),
                    ],
                    rows=[
                        ft.DataRow([
                            ft.DataCell(ft.Text(str(d["id"]))),
                            ft.DataCell(ft.Text(fornecedores.get(d["id_fornecedor"], ""))),
                            ft.DataCell(ft.Text(d["descricao"])),
                            ft.DataCell(ft.Text(str(d["valor"]))),
                            ft.DataCell(ft.Text(d["data"])),
                            ft.DataCell(ft.Text(formas_pagamento.get(d.get("id_form_Pag"), ""))),
                            ft.DataCell(ft.Row([
                                ft.IconButton("edit", on_click=lambda e, id=d["id"]: editar_despesa(id)),
                                ft.IconButton("delete", on_click=lambda e, id=d["id"]: deletar_despesa(id)),
                            ])),
                        ]) for d in despesas
                    ]
                )
            ],scroll=ft.ScrollMode.AUTO, expand=False, height=800)
        ])

    def nova_despesa_view():
        fornecedores_list = fornecedores_api.get_all()
        formas_pagamento_list = forma_pagamento_api.get_all()
        id_fornecedor = ft.Dropdown(
            options=[ft.dropdown.Option(str(f["id"]), f["nome"]) for f in fornecedores_list],
            label="Fornecedor",
            width=300
        )
        id_forma_pagamento = ft.Dropdown(
            options=[ft.dropdown.Option(str(f["id"]), f["nome"]) for f in formas_pagamento_list],
            label="Forma de Pagamento",
            width=300
        )
        descricao = ft.TextField(label="Descrição", width=300)
        valor = ft.TextField(label="Valor", width=150)
        data = ft.TextField(label="Data (YYYY-MM-DD)", width=150)
        def salvar(e):
            if id_fornecedor.value is not None and id_forma_pagamento.value is not None:
                if valor.value is not None and valor.value != "":
                    valor_float = float(valor.value)
                else:
                    valor_float = 0.0
                despesas_api.create({
                    "id_fornecedor": int(id_fornecedor.value),
                    "id_form_Pag": int(id_forma_pagamento.value),
                    "descricao": descricao.value,
                    "valor": valor_float,
                    "data": data.value
                })
                page.go("/despesas_diarias")
            else:
                page.add(ft.SnackBar(ft.Text("Selecione fornecedor e forma de pagamento!")))
                page.update()
        return ft.Column([
            ft.Text("Nova Despesa Diária", size=20),
            id_fornecedor,
            id_forma_pagamento,
            descricao,
            valor,
            data,
            ft.Row([
                ft.ElevatedButton("Salvar", on_click=salvar),
                ft.ElevatedButton("Voltar", on_click=lambda e: page.go("/despesas_diarias"))
            ])
        ])

    def editar_despesa(id):
        despesa = despesas_api.get_by_id(id)
        print(despesa)
        fornecedores_list = fornecedores_api.get_all()
        formas_pagamento_list = forma_pagamento_api.get_all()
        id_fornecedor = ft.Dropdown(
            options=[ft.dropdown.Option(str(f["id"]), f["nome"]) for f in fornecedores_list],
            value=str(despesa["id_fornecedor"]),
            label="Fornecedor",
            width=300
        )
        id_forma_pagamento = ft.Dropdown(
            options=[ft.dropdown.Option(str(f["id"]), f["nome"]) for f in formas_pagamento_list],
            value=str(despesa["id_form_Pag"]),
            label="Forma de Pagamento",
            width=300
        )
        descricao = ft.TextField(label="Descrição", value=despesa["descricao"], width=300)
        valor = ft.TextField(label="Valor", value=str(despesa["valor"]), width=150)
        data = ft.TextField(label="Data (YYYY-MM-DD)", value=despesa["data"], width=150)
        def salvar(e):
            if id_fornecedor.value is not None and id_forma_pagamento.value is not None:
                if valor.value is not None and valor.value != "":
                    valor_float = float(valor.value)
                else:
                    valor_float = 0.0  # ou trate conforme necessário

                despesas_api.update(id, {
                    "id_fornecedor": int(id_fornecedor.value),
                    "id_form_Pag": int(id_forma_pagamento.value),
                    "descricao": descricao.value,
                    "valor": valor_float,
                    "data": data.value
                })
                page.go("/despesas_diarias")
            else:
                page.add(ft.SnackBar(ft.Text("Selecione um fornecedor e uma forma de pagamento!")))
        page.views.append(
            ft.View(
                "/despesas_diarias/editar",
                [
                    ft.Column([
                        ft.Text("Editar Despesa Diária", size=20),
                        id_fornecedor,
                        id_forma_pagamento,
                        descricao,
                        valor,
                        data,
                        ft.Row([
                            ft.ElevatedButton("Salvar", on_click=salvar),
                            ft.ElevatedButton("Voltar", on_click=lambda e: page.go("/despesas_diarias"))
                        ])
                    ])
                ]
            )
        )
        page.update()

    def deletar_despesa(id):
        despesas_api.delete(id)
        page.go("/despesas_diarias")

    if page.route == "/despesas_diarias/novo":
        return nova_despesa_view()
    else:
        return listar_despesas()

