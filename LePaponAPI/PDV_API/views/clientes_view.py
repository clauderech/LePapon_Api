import flet as ft
from models.clientes_api import ClientesAPI
from views.tema_0_0_0 import *
from config import BASE_URL

clientes_api = ClientesAPI(BASE_URL)


def clientes_view(page: ft.Page):
    # Aplicando o tema da lanchonete
    page.bgcolor = "#FFFBELE"  # Cor de fundo
    page.title = "Clientes - Lanchonete"
    aplicar_tema(page)
    

    # Função para limpar campo ao focar
    def limpar_ao_focar(e):
        e.control.value = ""
        page.update()

    # Formulário para adicionar cliente
    id_field = ft.TextField(label="ID", color=COR_TEXTO, read_only=True)
    nome_field = ft.TextField(label="Nome", on_focus=limpar_ao_focar, color=COR_TEXTO)
    sobrenome_field = ft.TextField(label="Sobrenome", on_focus=limpar_ao_focar, color=COR_TEXTO)
    fone_field = ft.TextField(label="Fone", color=COR_TEXTO)
    msg = ft.Text(visible=False)

    # Busca clientes cadastrados para filtro
    try:
        data = clientes_api.get_all()
        if not isinstance(data, list):
            data = [data] if data else []
    except Exception as e:
        return ft.Text(f"Erro ao buscar clientes: {e}", color="red")

    # Caixa de seleção e filtro por nome
    filtro_nome = ft.TextField(label="Filtrar por nome", width=200)
    opcoes_clientes = [ft.dropdown.Option(text=str(f'{c.get("nome", "")} {c.get("sobrenome", "")}')) for c in data if isinstance(c, dict)]
    dropdown_clientes = ft.Dropdown(options=opcoes_clientes, label="Selecionar cliente", width=350)

    def filtrar_clientes(e):
        nome_filtro = (filtro_nome.value or "").lower()
        lista_clientes = data if isinstance(data, list) else []
        dropdown_clientes.options = [
            ft.dropdown.Option(text=str(f'{c.get("nome", "")} {c.get("sobrenome", "")}'))
            for c in lista_clientes if isinstance(c, dict) and nome_filtro in str(c.get("nome", "")).lower()
        ]
        page.update()

    filtro_nome.on_change = filtrar_clientes

    def adicionar_cliente(e):
        try:
            novo = {
                "id":  id_field.value if id_field.value else None,
                "nome": nome_field.value,
                "sobrenome": sobrenome_field.value,
                "fone": fone_field.value
            }
            resp = clientes_api.create(novo)
            print(f"Resposta da API ao adicionar cliente: {resp}")
            msg.value = "Cliente adicionado com sucesso!"
            msg.color = "green"
            msg.visible = True
            id_field.value = nome_field.value = sobrenome_field.value = fone_field.value = ""
            # Atualiza a lista de clientes e o dropdown
            try:
                data_atualizada = clientes_api.get_all()
                if not isinstance(data_atualizada, list):
                    data_atualizada = [data_atualizada] if data_atualizada else []
            except Exception as e:
                data_atualizada = []
            nonlocal data
            data = data_atualizada  # Atualiza a variável data global
            dropdown_clientes.options = [ft.dropdown.Option(text=str(f'{c.get("nome", "")} {c.get("sobrenome", "")}')) for c in data_atualizada if isinstance(c, dict)]
            page.update()
        except Exception as ex:
            msg.value = f"Erro ao adicionar cliente: {ex}"
            msg.color = "red"
            msg.visible = True
            page.update()

    # Função para preencher campos ao selecionar no dropdown
    def selecionar_cliente(e):
        nome_sobrenome_selecionado = dropdown_clientes.value
        lista_clientes = data if isinstance(data, list) else []
        for c in lista_clientes:
            if isinstance(c, dict) and f"{c.get('nome', '')} {c.get('sobrenome', '')}" == nome_sobrenome_selecionado:
                id_field.value = str(c.get("id", ""))
                nome_field.value = str(c.get("nome", ""))
                sobrenome_field.value = str(c.get("sobrenome", ""))
                fone_field.value = str(c.get("fone", ""))
                break
        page.update()
    dropdown_clientes.on_change = selecionar_cliente

    def atualizar_clientes(e=None):
        try:
            data_atualizada = clientes_api.get_all()
            if not isinstance(data_atualizada, list):
                data_atualizada = [data_atualizada] if data_atualizada else []
        except Exception as e:
            data_atualizada = []
        dropdown_clientes.options = [ft.dropdown.Option(text=str(f'{c.get("nome", "")} {c.get("sobrenome", "")}')) for c in data_atualizada if isinstance(c, dict)]
        page.update()

    def atualizar_cliente(e):
        try:
            cliente_atualizado = {
                "id": id_field.value,
                "nome": nome_field.value,
                "sobrenome": sobrenome_field.value,
                "fone": fone_field.value
            }
            resp = clientes_api.update(id_field.value, cliente_atualizado)
            msg.value = "Cliente atualizado com sucesso!"
            msg.color = "green"
            msg.visible = True
            # Atualiza a lista de clientes e o dropdown
            try:
                data_atualizada = clientes_api.get_all()
                if not isinstance(data_atualizada, list):
                    data_atualizada = [data_atualizada] if data_atualizada else []
            except Exception as e:
                data_atualizada = []
            nonlocal data
            data = data_atualizada  # Atualiza a variável data global
            dropdown_clientes.options = [ft.dropdown.Option(text=str(f'{c.get("nome", "")} {c.get("sobrenome", "")}')) for c in data_atualizada if isinstance(c, dict)]
            page.update()
        except Exception as ex:
            msg.value = f"Erro ao atualizar cliente: {ex}"
            msg.color = "red"
            msg.visible = True
            page.update()

    def criar_pedido_produtos_todos(e):
        import urllib.parse
        from models.numpedidos_api import NumPedidosAPI
        from models.ordempedidos_api import OrdemPedidosAPI
        import datetime
        if not id_field.value:
            msg.value = "Selecione um cliente para criar um pedido."
            msg.color = "orange"
            msg.visible = True
            page.update()
            return
        try:
            numpedidos_api = NumPedidosAPI(BASE_URL)
            agora = datetime.datetime.now()
            data_str = agora.strftime("%Y-%m-%d")
            hora_str = agora.strftime("%H:%M:%S")
            novo_num_pedido = {
                "nome": nome_field.value,
                "sobrenome": sobrenome_field.value,
                "id_Cliente": id_field.value,
                "fone": fone_field.value,
                "data": data_str,
                "hora": hora_str
            }
            num_pedido_resp = numpedidos_api.create(novo_num_pedido)
            if isinstance(num_pedido_resp, (int, str)):
                num_pedido_id = num_pedido_resp
            elif isinstance(num_pedido_resp, dict):
                num_pedido_id = num_pedido_resp.get('id', '')
            elif isinstance(num_pedido_resp, list) and num_pedido_resp and isinstance(num_pedido_resp[0], dict):
                num_pedido_id = num_pedido_resp[0].get('id', '')
            else:
                num_pedido_id = ''
            ordempedidos_api = OrdemPedidosAPI(BASE_URL)
            nova_ordem = {
                "numPedido": str(num_pedido_id),
                "id_cliente": id_field.value,
                "hora": hora_str
            }
            ordem_resp = ordempedidos_api.create(nova_ordem)
            ordem_id = ordem_resp if isinstance(ordem_resp, (int, str)) else (ordem_resp.get('id', '') if ordem_resp is not None else '')
            # Navega para produtos_todos_view passando todos os dados
            page.go(f"/produtos_todos?numPedido={num_pedido_id}&idOrderPedido={ordem_id}&idCliente={id_field.value}&nome={nome_field.value}&sobrenome={sobrenome_field.value}&fone={fone_field.value}")
        except Exception as ex:
            msg.value = f"Erro ao criar pedido: {ex}"
            msg.color = "red"
            msg.visible = True
            page.update()

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
        texto_titulo("Adicionar Cliente"),
        id_field,
        nome_field,
        sobrenome_field,
        fone_field,
        ft.Row([
            botao_acao("Adicionar", on_click=adicionar_cliente),
            botao_acao("Atualizar Cliente", on_click=atualizar_cliente),
        ]),
        ft.Row([
            botao_acao("Novo Pedido Produtos Todos", on_click=criar_pedido_produtos_todos),
            msg
        ]),
        ft.Divider(),
        texto_padrao("Filtrar e Selecionar Cliente"),
        ft.Row([filtro_nome, dropdown_clientes]),
        ft.Divider()
    ])
