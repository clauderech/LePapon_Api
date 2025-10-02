import flet as ft
from models.numpedidos_api import NumPedidosAPI
import urllib.parse
import datetime
from views.tema_0_0_0 import aplicar_tema, texto_titulo, botao_acao

BASE_URL = "http://lepapon.novo:3000"
numpedidos_api = NumPedidosAPI(BASE_URL)

def numpedidos_view(page: ft.Page):
    # Acesso seguro aos parâmetros da query string (compatível com Flet)
    cliente_id = str(urllib.parse.unquote(page.query.get("id") or ""))
    nome_cliente = str(urllib.parse.unquote(page.query.get("nome") or ""))
    sobrenome_cliente = str(urllib.parse.unquote(page.query.get("sobrenome") or ""))
    fone_cliente = str(urllib.parse.unquote(page.query.get("fone") or ""))
    try:
        data = numpedidos_api.get_all()
        if not isinstance(data, list):
            data = [data] if data else []
    except Exception as e:
        return ft.Text(f"Erro ao buscar num. pedidos: {e}", color="red")

    # Função para limpar campo ao focar
    def limpar_ao_focar(e):
        e.control.value = ""
        page.update()

    # Formulário para adicionar número de pedido
    id_num_pedido = ft.TextField(label="ID Num Pedido", read_only=True)
    nome = ft.TextField(label="Nome", value=nome_cliente, on_focus=limpar_ao_focar)
    sobrenome = ft.TextField(label="Sobrenome", value=sobrenome_cliente, on_focus=limpar_ao_focar)
    fone = ft.TextField(label="Fone", value=fone_cliente)
    id_cliente = ft.TextField(label="ID Cliente", value=cliente_id, read_only=True)
    msg = ft.Text(visible=False)
    resultado_busca = ft.Text(visible=False)

    def adicionar_num_pedido(e):
        try:
            data = numpedidos_api.get_all()
            existente = None
            if isinstance(data, list):
                for row in data:
                    if isinstance(row, dict) and str(row.get("fone", "")) == fone.value:
                        existente = row
                        break
            if existente:
                resultado_busca.value = f"Já existe pedido com este fone: {existente}"
                resultado_busca.color = "orange"
                resultado_busca.visible = True
                msg.visible = False
            else:
                agora = datetime.datetime.now()
                data_str = agora.strftime("%Y-%m-%d")
                hora_str = agora.strftime("%H:%M:%S")
                novo = {
                    "nome": nome.value,
                    "sobrenome": sobrenome.value,
                    "id_Cliente": id_cliente.value,
                    "fone": fone.value,
                    "data": data_str,
                    "hora": hora_str
                }
                resp = numpedidos_api.create(novo)
                msg.value = "Número de pedido adicionado com sucesso!"
                msg.color = "green"
                msg.visible = True
                resultado_busca.visible = False
                # Atualiza os campos com os dados do novo pedido
                id_num_pedido.value = str(resp.get('id', '')) if isinstance(resp, dict) else ''
                nome.value = novo["nome"]
                sobrenome.value = novo["sobrenome"]
                fone.value = novo["fone"]
                id_cliente.value = novo["id_Cliente"]
                # Atualiza o dropdown de pedidos
                data_atualizada = numpedidos_api.get_all()
                opcoes_pedidos.clear()
                if isinstance(data_atualizada, list):
                    for row in data_atualizada:
                        if isinstance(row, dict):
                            text = f"{row.get('id', '')} - {row.get('nome', '')} {row.get('sobrenome', '')} ({row.get('fone', '')})"
                            value = str(row.get('id', ''))
                            opcoes_pedidos.append(ft.dropdown.Option(text=text, key=value))
                dropdown_pedidos.options = opcoes_pedidos
            page.update()
        except Exception as ex:
            msg.value = f"Erro ao adicionar número de pedido: {ex}"
            msg.color = "red"
            msg.visible = True
            resultado_busca.visible = False
            page.update()

    def editar_num_pedido(e):
        try:
            if not id_num_pedido.value:
                msg.value = "Selecione um pedido para editar."
                msg.color = "orange"
                msg.visible = True
                page.update()
                return
            novo = {
                "nome": nome.value,
                "id_cliente": id_cliente.value,
                "fone": fone.value
            }
            resp = numpedidos_api.update(id_num_pedido.value, novo)
            msg.value = "Pedido atualizado com sucesso!"
            msg.color = "green"
            msg.visible = True
            page.update()
        except Exception as ex:
            msg.value = f"Erro ao editar pedido: {ex}"
            msg.color = "red"
            msg.visible = True
            page.update()

    def deletar_num_pedido(e):
        try:
            if not id_num_pedido.value:
                msg.value = "Selecione um pedido para deletar."
                msg.color = "orange"
                msg.visible = True
                page.update()
                return
            resp = numpedidos_api.delete(id_num_pedido.value)
            msg.value = "Pedido deletado com sucesso!"
            msg.color = "green"
            msg.visible = True
            id_num_pedido.value = nome.value = fone.value = id_cliente.value = ""
            page.update()
        except Exception as ex:
            msg.value = f"Erro ao deletar pedido: {ex}"
            msg.color = "red"
            msg.visible = True
            page.update()

    def criar_pedido_produtos_todos(e):
        from models.ordempedidos_api import OrdemPedidosAPI
        import datetime
        
        # Verifica se há um num_pedido selecionado
        if not id_num_pedido.value:
            msg.value = "Selecione um número de pedido para criar a ordem."
            msg.color = "orange"
            msg.visible = True
            page.update()
            return
            
        try:
            # Cria ordem de pedido
            ordempedidos_api = OrdemPedidosAPI(BASE_URL)
            agora = datetime.datetime.now()
            hora_str = agora.strftime("%H:%M:%S")
            
            nova_ordem = {
                "numPedido": id_num_pedido.value,
                "id_cliente": id_cliente.value,
                "hora": hora_str
            }
            
            ordem_resp = ordempedidos_api.create(nova_ordem)
            ordem_id = ordem_resp if isinstance(ordem_resp, (int, str)) else ordem_resp.get('id', '')
            
            # Navega para produtos_todos passando os dados necessários
            page.go(f"/produtos_todos?numPedido={id_num_pedido.value}&idOrderPedido={ordem_id}&idCliente={id_cliente.value}&nome={nome.value}&sobrenome={sobrenome.value}&fone={fone.value}")
            
        except Exception as ex:
            msg.value = f"Erro ao criar ordem: {ex}"
            msg.color = "red"
            msg.visible = True
            page.update()

    # Tabela de pedidos existentes

    # Tabela de pedidos existentes
    try:
        data = numpedidos_api.get_all()
        if not isinstance(data, list):
            data = [data] if data else []
    except Exception as e:
        return ft.Text(f"Erro ao buscar num. pedidos: {e}", color="red")
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
    
    # Caixa de seleção para pedidos existentes
    opcoes_pedidos = []
    if data:
        for row in data:
            if isinstance(row, dict):
                text = f"{row.get('id', '')} - {row.get('nome', '')} ({row.get('fone', '')})"
                value = str(row.get('id', ''))
                opcoes_pedidos.append(ft.dropdown.Option(text=text, key=value))
    dropdown_pedidos = ft.Dropdown(options=opcoes_pedidos, label="Selecionar Pedido", width=350)

    def selecionar_pedido(e):
        valor = dropdown_pedidos.value
        for row in data:
            if str(row.get('id', '')) == valor:
                id_num_pedido.value = str(row.get('id', ''))
                nome.value = str(row.get('nome', ''))
                id_cliente.value = str(row.get('id_cliente', ''))
                fone.value = str(row.get('fone', ''))
                break
        page.update()
    dropdown_pedidos.on_change = selecionar_pedido

    def adicionar_telefone_ficticio(e):
        try:
            data = numpedidos_api.get_all()
            telefones = []
            if isinstance(data, list):
                for row in data:
                    if (
                        isinstance(row, dict)
                        and str(row.get("id_cliente", "")) == "13"
                    ):
                        telefones.append(str(row.get("fone", "")))

            if telefones:
                maior = max(int(t) for t in telefones)
                novo_fone = str(maior + 1)
            else:
                novo_fone = "555400000000"
            fone.value = novo_fone
            id_cliente.value = "13"
            page.update()
        except Exception as ex:
            msg.value = f"Erro ao adicionar telefone fictício: {ex}"
            msg.color = "red"
            msg.visible = True
            page.update()

    return ft.Column([
        texto_titulo("Registrar Número de Pedido"),
        id_num_pedido,
        nome,
        sobrenome,
        id_cliente,
        fone,
        ft.Row([
            botao_acao("Criar", on_click=adicionar_num_pedido),
            botao_acao("Editar", on_click=editar_num_pedido),
            botao_acao("Deletar", on_click=deletar_num_pedido),
            botao_acao("Novo Pedido Produtos Todos", on_click=criar_pedido_produtos_todos),
            botao_acao("Adicionar Telefone Fictício", on_click=adicionar_telefone_ficticio),
        ], alignment=ft.MainAxisAlignment.START),
        msg,
        resultado_busca,
        ft.Divider(),
        texto_titulo("Pedidos cadastrados"),
        dropdown_pedidos
    ])
