import flet as ft
import urllib.parse
import datetime
from models.produtos_todos_api import ProdutosTodosAPI
from models.pedidostemp_api import PedidosTempAPI
from utils.ui_components import create_filter_field
from config import BASE_URL

def produtos_todos_view(page: ft.Page):
    # Recebe dados via query string
    num_pedido = page.query.get("numPedido")
    id_order = page.query.get("idOrderPedido")
    id_cliente = page.query.get("idCliente")
    nome_cliente = page.query.get("nome")
    sobrenome_cliente = page.query.get("sobrenome")
    fone_cliente = page.query.get("fone")

    # Caixas de texto para exibir/editar dados
    numPedido = ft.TextField(label="Número do Pedido", value=str(num_pedido) if num_pedido is not None else "", read_only=True, width=150)
    idOrder = ft.TextField(label="ID Ordem Pedido", value=str(id_order) if id_order is not None else "", read_only=True, width=150)
    idCliente = ft.TextField(label="ID Cliente", value=str(id_cliente) if id_cliente is not None else "", read_only=True, width=150)
    nome = ft.TextField(label="Nome Cliente", value=str(nome_cliente) if nome_cliente is not None else "", read_only=True, width=200)
    sobrenome = ft.TextField(label="Sobrenome Cliente", value=str(sobrenome_cliente) if sobrenome_cliente is not None else "", read_only=True, width=200)
    fone = ft.TextField(label="Fone Cliente", value=str(fone_cliente) if fone_cliente is not None else "", read_only=True, width=150)

    produtos_todos_api = ProdutosTodosAPI(BASE_URL)
    try:
        produtos_todos = produtos_todos_api.get_all()
        if not isinstance(produtos_todos, list):
            produtos_todos = [produtos_todos] if produtos_todos else []
        
        # Validar estrutura dos produtos
        produtos_validos = []
        for prod in produtos_todos:
            if isinstance(prod, dict) and "nome_Prod" in prod and "Valor_Prod" in prod and "id_Prod" in prod:
                produtos_validos.append(prod)
        produtos_todos = produtos_validos
        
    except Exception as e:
        produtos_todos = []
        print(f"Erro ao carregar produtos: {e}")  # Para debug

    # Cada item é um dict: {"id_Prod":..., "nome_Prod":..., "Valor_Prod":..., "qtd":..., "observ":...}
    lista_provisoria = []

    filtro_valor = {"texto": ""}
    
    def limpar_msg_apos_tempo():
        # Função para limpar mensagem após alguns segundos
        import threading
        import time
        def delayed_clear():
            time.sleep(5)  # 5 segundos
            msg.visible = False
            page.update()
        threading.Thread(target=delayed_clear, daemon=True).start()
    
    def on_filtrar(e):
        filtro_valor['texto'] = e.control.value or ""
        atualizar_sugestoes(filtro_valor['texto'])
    busca_produto = create_filter_field("Buscar produto", on_filtrar, width=300)
    sugestoes = ft.ListView(expand=1, spacing=5, padding=10, width=800)
    lista_view = ft.ListView(expand=1, spacing=8, padding=10, width=1100)

    def atualizar_sugestoes(valor):
        sugestoes.controls.clear()
        if valor and len(valor.strip()) >= 2:  # Mínimo 2 caracteres
            matches = 0
            for prod in produtos_todos:
                if matches >= 10:  # Máximo 10 sugestões
                    break
                nome_prod = str(prod.get("nome_Prod", ""))
                if valor.lower() in nome_prod.lower():
                    valor_formatado = prod.get("Valor_Prod", "0.00")
                    try:
                        valor_float = float(valor_formatado)
                        valor_str = f"{valor_float:.2f}"
                    except (ValueError, TypeError):
                        valor_str = "0.00"
                    
                    sugestoes.controls.append(
                        ft.ListTile(
                            title=ft.Text(f'{nome_prod} - R$ {valor_str}'),
                            on_click=lambda e, prod=prod: adicionar_produto(prod)
                        )
                    )
                    matches += 1
        page.update()

    def atualizar_lista():
        lista_view.controls.clear()
        for idx, prod in enumerate(lista_provisoria):
            prod_id = prod.get("id_Prod", "")
            nome_prod = prod.get("nome_Prod", "")
            valor_prod = prod.get("Valor_Prod", 0)
            
            # Formatar valor do produto
            try:
                valor_formatado = f"{float(valor_prod):.2f}"
            except (ValueError, TypeError):
                valor_formatado = "0.00"
            
            lista_view.controls.append(
                ft.ListTile(
                    title=ft.Text(f'{nome_prod} - R$ {valor_formatado}', width=350),
                    subtitle=ft.Row([
                        ft.Text(f'ID: {prod_id}')
                    ]),
                    trailing=ft.Row([
                        ft.TextField(
                            label="Qtd",
                            value=prod.get("qtd", "1"),
                            width=80,
                            hint_text="Ex: 0.5, 1, 2.5",
                            on_change=lambda e, i=idx: atualizar_quantidade(i, e.control.value)
                        ),
                        ft.TextField(
                            label="Observação",
                            value=prod.get("observ", ""),
                            width=350,
                            hint_text="Ex: sem ervilha, completo, etc.",
                            multiline=True,
                            on_change=lambda e, i=idx: atualizar_observacao(i, e.control.value)
                        ),
                        ft.Checkbox(
                            label="Pago",
                            value=prod.get("pago", False),
                            on_change=lambda e, i=idx: atualizar_status_pago(i, e.control.value)
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE,
                            tooltip="Remover",
                            on_click=lambda e, i=idx: remover_produto(i)
                        )
                    ], width=650),
                    dense=False,
                    width=1000
                ),
            )
        # Atualiza a página após reconstruir a lista
        page.update()

    def adicionar_produto(prod):
        # Validar produto antes de adicionar
        if not isinstance(prod, dict) or not prod.get("id_Prod") or not prod.get("nome_Prod"):
            return
        
        # Verificar se produto já está na lista
        for item in lista_provisoria:
            if item.get("id_Prod") == prod.get("id_Prod"):
                # Se já existe, apenas incrementa quantidade (suporta fracionários)
                try:
                    qtd_atual = float(item.get("qtd", "1"))
                    item["qtd"] = str(round(qtd_atual + 1, 3))
                except ValueError:
                    item["qtd"] = "1"
                atualizar_lista()
                sugestoes.controls.clear()
                busca_produto.value = ""
                page.update()
                return
        
        # Validar e converter valor do produto
        try:
            valor_prod = float(prod.get("Valor_Prod", 0))
        except (ValueError, TypeError):
            valor_prod = 0.00
        
        # Adiciona produto à lista provisória com campo pago
        lista_provisoria.append({
            "id_Prod": prod.get("id_Prod", ""),
            "nome_Prod": prod.get("nome_Prod", ""),
            "Valor_Prod": valor_prod,
            "qtd": "1",
            "observ": "",
            "pago": False
        })
        atualizar_lista()
        # Limpa sugestões e campo de busca após adicionar
        sugestoes.controls.clear()
        busca_produto.value = ""
        page.update()
    def atualizar_observacao(prod_id, valor):
        # Atualiza observação do item pelo índice
        if 0 <= prod_id < len(lista_provisoria):
            lista_provisoria[prod_id]["observ"] = str(valor) if valor is not None else ""

    def atualizar_quantidade(prod_id, valor):
        if 0 <= prod_id < len(lista_provisoria):
            try:
                # Aceitar quantidades fracionárias (ex: 0.5, 1.5, 2.0)
                qtd = float(valor) if valor else 1.0
                if qtd < 0:  # Apenas não permitir negativos
                    qtd = 1.0
                # Manter precisão de até 3 casas decimais
                qtd = round(qtd, 3)
                lista_provisoria[prod_id]["qtd"] = str(qtd)
            except (ValueError, TypeError):
                lista_provisoria[prod_id]["qtd"] = "1"

    def atualizar_status_pago(prod_id, valor):
        # Atualiza status de pagamento do item pelo índice
        if 0 <= prod_id < len(lista_provisoria):
            lista_provisoria[prod_id]["pago"] = bool(valor)

    def remover_produto(produto):
        # Remove pelo índice
        if 0 <= produto < len(lista_provisoria):
            lista_provisoria.pop(produto)
            atualizar_lista()
            page.update()

    # Removido campo de observações gerais, agora cada produto tem seu campo
    msg = ft.Text(visible=False)

    def registrar_produtos(e):
        # Limpar mensagem anterior
        msg.visible = False
        
        # Validações básicas
        if not lista_provisoria:
            msg.value = "Adicione pelo menos um produto à lista"
            msg.color = "red"
            msg.visible = True
            page.update()
            return
        
        if not numPedido.value or not idCliente.value or not idOrder.value:
            msg.value = "Dados do pedido/cliente são obrigatórios"
            msg.color = "red"
            msg.visible = True
            page.update()
            return
        
        pedidos_temp_api = PedidosTempAPI(BASE_URL)
        sucesso = True
        produtos_processados = 0
        
        for prod in lista_provisoria:
            # Validar dados do produto
            id_prod = prod.get("id_Prod", "")
            qtd = prod.get("qtd", "1")
            
            if not id_prod:
                continue  # Pula produtos sem ID
            
            # Validar quantidade (aceitar fracionários como 0.5)
            try:
                qtd_float = float(qtd)
                if qtd_float < 0:  # Apenas não permitir negativos
                    qtd_float = 1.0
                qtd_float = round(qtd_float, 3)  # Precisão de 3 casas decimais
            except (ValueError, TypeError):
                qtd_float = 1.0
            
            # Validar valor unitário
            try:
                v_unit = float(prod.get("Valor_Prod", 0))
            except (ValueError, TypeError):
                v_unit = 0.00
            
            pedido = {
                "numPedido": numPedido.value.strip(),
                "id_cliente": idCliente.value.strip(),
                "idOrderPedido": idOrder.value.strip(),
                "id_Prod": id_prod,
                "qtd": str(qtd_float),
                "V_unit": v_unit,
                "data": datetime.datetime.now().strftime("%Y-%m-%d"),
                "hora": datetime.datetime.now().strftime("%H:%M:%S"),
                "observ": prod.get("observ", "").strip(),
                "pago": bool(prod.get("pago", False))
            }
            
            try:
                pedidos_temp_api.create(pedido)
                produtos_processados += 1
            except Exception as ex:
                sucesso = False
                msg.value = f"Erro ao registrar produto '{prod.get('nome_Prod', 'Unknown')}': {ex}"
                msg.color = "red"
                msg.visible = True
                break
        
        if sucesso and produtos_processados > 0:
            lista_provisoria.clear()
            atualizar_lista()
            msg.value = f"✅ {produtos_processados} produto(s) registrado(s) com sucesso!"
            msg.color = "green"
            msg.visible = True
            limpar_msg_apos_tempo()
        elif produtos_processados == 0:
            msg.value = "⚠️ Nenhum produto válido foi encontrado para registrar"
            msg.color = "orange"
            msg.visible = True
            limpar_msg_apos_tempo()
        
        page.update()

    # Função para retornar à página anterior
    def retornar_pagina(e):
        page.go("/")  # Substitua "/" pelo caminho da página inicial ou anterior

    # Botão de retorno
    botao_retorno = ft.ElevatedButton("Voltar", on_click=retornar_pagina)

    # on_change já configurado via create_filter_field

    return ft.Column([
        ft.Text("Produtos Todos - Dados do Pedido e Cliente", size=20, weight=ft.FontWeight.BOLD),
        ft.Row([numPedido, idOrder, idCliente]),
        ft.Row([nome, sobrenome, fone]),
        ft.Divider(),
        ft.Text("Buscar e adicionar produto à lista provisória:"),
        ft.Text("💡 Dica: Use quantidades fracionárias (ex: 0.5) e observações detalhadas (ex: 'sem ervilha')", 
                size=12, color="blue", italic=True),
        ft.Row([
            busca_produto,
            ft.ElevatedButton("Registrar", on_click=registrar_produtos),
            msg
        ]),
        sugestoes,
        ft.Divider(),
        # Campo de observações gerais removido
        ft.Text("Lista provisória de produtos:"),
        lista_view,
        
    ], width=1100, scroll=ft.ScrollMode.AUTO)

# Para usar: page.go(f"/produtos_todos?numPedido=...&idOrderPedido=...&idCliente=...&nome=...&sobrenome=...&fone=...")
