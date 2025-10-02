import flet as ft
from models.crediario_api import CrediarioAPI
from models.clientes_api import ClientesAPI
from models.produtos_todos_api import ProdutosTodosAPI
from models.enviar_conta_cliente import EnviarContaCliente
from models.recebido_api import RecebidoAPI
import datetime
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import tempfile
import os
import re
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env'))

BASE_URL = "http://lepapon.api:3000"
crediario_api = CrediarioAPI(BASE_URL)
clientes_api = ClientesAPI(BASE_URL)
produtos_todos_api = ProdutosTodosAPI(BASE_URL)
recebido_api = RecebidoAPI(BASE_URL)

API_KEY = os.getenv("MINHA_API_KEY")
HEADERS = {"x-api-key": API_KEY}
GRAPH_API_TOKEN = os.getenv("GRAPH_API_TOKEN")

#print(f"Graph API Token: {GRAPH_API_TOKEN}")

def get_saldo_recebido_por_cliente(cliente_id):
    """
    Retorna o saldo_recebido para um cliente específico.
    """
    from models.saldo_recebido_api import SaldoRecebidoAPI
    saldo_api = SaldoRecebidoAPI(BASE_URL)
    try:
        saldos = saldo_api.get_all()
        if not isinstance(saldos, list):
            saldos = [saldos] if saldos else []
        total = sum(float(str(s.get('valor', 0)).replace(',', '.')) for s in saldos if str(s.get('id_cliente')) == str(cliente_id))
        return total
    except Exception as e:
        return f"Erro ao buscar saldo recebido: {e}"
    

def crediario_view(page: ft.Page):
    msg = ft.Text(visible=False)
    # Filtros de data (entrada manual)
    data_inicial = ft.TextField(
        label="Data Inicial",
        value=str(datetime.date.today()),
        on_change=lambda e: filtrar_crediario_periodo(),
        width=140,
        hint_text="AAAA-MM-DD"
    )
    data_final = ft.TextField(
        label="Data Final",
        value=str(datetime.date.today()),
        on_change=lambda e: filtrar_crediario_periodo(),
        width=140,
        hint_text="AAAA-MM-DD"
    )
    # Caixa de seleção de clientes
    try:
        clientes = clientes_api.get_all()
        if not isinstance(clientes, list):
            clientes = [clientes] if clientes else []
    except Exception:
        clientes = []
    opcoes_clientes = [ft.dropdown.Option(text=f"{c.get('id', '')} - {c.get('nome', '')} - {c.get('sobrenome', '')}", key=str(c.get('id', ''))) for c in clientes if isinstance(c, dict)]
    dropdown_clientes = ft.Dropdown(
        options=opcoes_clientes,
        label="Selecionar Cliente",
        width=350,
        on_change=lambda e: filtrar_crediario_periodo()
    )
    # Caixa de seleção para filtrar por pago
    dropdown_pago = ft.Dropdown(
        options=[
            ft.dropdown.Option(text="Ativo", key="0"),
            ft.dropdown.Option(text="Pago", key="1"),
            ft.dropdown.Option(text="Todos", key="")
        ],
        label="Ativo",
        width=120,
        on_change=lambda e: filtrar_crediario_periodo()
    )
    total_crediario_label = ft.Text("Total do período: 0.00", style=ft.TextThemeStyle.TITLE_MEDIUM, width=250)
    saldo_recebido = ft.Text("Saldo Recebido: 0.00", style=ft.TextThemeStyle.TITLE_MEDIUM, width=250)
    saldo_devedor = ft.Text("Saldo Devedor: 0.00", style=ft.TextThemeStyle.TITLE_MEDIUM, width=250)
    tabela_ref = ft.Ref[ft.DataTable]()

    def filtrar_crediario_periodo():
        di = data_inicial.value
        df = data_final.value
        cliente_id = dropdown_clientes.value
        pago_val = dropdown_pago.value
        if not di or not df:
            return
        di_str = str(di)
        df_str = str(df)
        try:
            crediarios = crediario_api.get_all()
            if not isinstance(crediarios, list):
                crediarios = [crediarios] if crediarios else []
            # Busca produtos todos
            produtos_todos = produtos_todos_api.get_all()
            if not isinstance(produtos_todos, list):
                produtos_todos = [produtos_todos] if produtos_todos else []
            # Converte para DataFrame
            crediario_df = pd.DataFrame(crediarios)
            produtos_df = pd.DataFrame(produtos_todos)
            # Faz o merge pelo campo de produto (ajuste o nome se necessário)
            if not crediario_df.empty and not produtos_df.empty:
                merged_df = crediario_df.merge(
                    produtos_df[['id_Prod', 'nome_Prod', 'Valor_Prod']],
                    left_on='id_Prod', right_on='id_Prod', how='left'
                )
            else:
                merged_df = crediario_df
            # Filtra por data e cliente (se selecionado)
            crediarios_periodo = merged_df[(merged_df['data'] >= di_str) & (merged_df['data'] <= df_str)]
            if cliente_id:
                crediarios_periodo = crediarios_periodo[crediarios_periodo['id_cliente'].astype(str) == cliente_id]
                # Quando um cliente específico é selecionado, mostra apenas os não pagos
                crediarios_periodo = crediarios_periodo[crediarios_periodo['pago'].astype(str) == '0']
            elif pago_val in ("1", "0"):
                # Só aplica o filtro de pago quando nenhum cliente específico está selecionado
                crediarios_periodo = crediarios_periodo[crediarios_periodo['pago'].astype(str) == pago_val]
            
            # Ordena sempre colocando pago=0 primeiro, depois por data
            if not crediarios_periodo.empty:
                crediarios_periodo = crediarios_periodo.sort_values(['pago', 'data'], ascending=[True, True])
            # Monta tabela apenas com os campos desejados
            campos_exibir = ['data', 'hora', 'qtd', 'nome_Prod', 'Valor_Prod', 'sub_total_calc']
            colunas_legenda = {
                'data': 'Data',
                'hora': 'Hora',
                'qtd': 'Qtd',
                'nome_Prod': 'Produto',
                'Valor_Prod': 'Valor Unit.',
                'sub_total_calc': 'Subtotal'
            }
            # Formata a data para exibição na tabela (compatível com datas ISO e com hora)
            if not crediarios_periodo.empty:
                crediarios_periodo = crediarios_periodo.copy()
                if 'data' in crediarios_periodo.columns:
                    def formatar_data(d):
                        try:
                            # Tenta extrair apenas a parte da data (YYYY-MM-DD)
                            data_str = str(d).split('T')[0]
                            return datetime.datetime.strptime(data_str, '%Y-%m-%d').strftime('%d/%m/%Y')
                        except Exception:
                            return d or ''
                    crediarios_periodo['data'] = crediarios_periodo['data'].apply(formatar_data)
            # Garante que a coluna de subtotal calculado existe
            if not crediarios_periodo.empty:
                if 'sub_total_calc' not in crediarios_periodo.columns:
                    crediarios_periodo['sub_total_calc'] = crediarios_periodo.apply(
                        lambda row: float(row.get('qtd', 0)) * float(str(row.get('Valor_Prod', 0)).replace(",", ".")), axis=1
                    )
            # Seleciona apenas os campos desejados
            if not crediarios_periodo.empty:
                crediarios_periodo = crediarios_periodo[campos_exibir]
                columns = [ft.DataColumn(ft.Text(colunas_legenda[c])) for c in campos_exibir]
            else:
                columns = [ft.DataColumn(ft.Text("Data"))]
            rows = []
            total = 0.0
            for _, cred in crediarios_periodo.iterrows():
                row = [ft.DataCell(ft.Text(str(cred.get(c, "")))) for c in campos_exibir]
                rows.append(ft.DataRow(row))
                try:
                    total += float(str(cred.get("sub_total_calc", 0)).replace(",", "."))
                except:
                    pass
            #print(f"Total calculado: {total}")
            if not rows:
                rows = [ft.DataRow([ft.DataCell(ft.Text("")) for _ in columns])]
            tabela_ref.current.columns = columns
            tabela_ref.current.rows = rows
            # Atualiza saldo recebido e devedor
            saldoRecebido = float(get_saldo_recebido_por_cliente(cliente_id) if cliente_id else 0.0)
            saldoDevedor = total - saldoRecebido
            saldo_recebido.value = f"Saldo Recebido: {saldoRecebido:.2f}"
            saldo_devedor.value = f"Saldo Devedor: {saldoDevedor:.2f}"
            total_crediario_label.value = f"Total do período: {total:.2f}"
            page.update()
        except Exception as e:
            msg.value = f"Erro ao buscar crediário: {e}"
            msg.color = "red"
            msg.visible = True
            page.update()

    # Inicializa tabela vazia
    tabela = ft.DataTable(ref=tabela_ref, columns=[ft.DataColumn(ft.Text("id"))], rows=[])
    # Carrega crediário do dia atual ao abrir
    filtrar_crediario_periodo()

    filtro_nome = ft.TextField(
        label="Filtrar cliente por nome",
        width=200,
        on_change=lambda e: filtrar_opcoes_clientes()
    )
    def filtrar_opcoes_clientes():
        nome_filtro = (filtro_nome.value or "").lower()
        dropdown_clientes.options = [
            ft.dropdown.Option(text=f"{c.get('id', '')} - {c.get('nome', '')} - {c.get('sobrenome', '')}", key=str(c.get('id', '')))
            for c in clientes if isinstance(c, dict) and nome_filtro in str(c.get('nome', '')).lower()
        ]
        page.update()

    def exportar_pdf():
        try:
            # Usa os mesmos dados filtrados da tabela
            di = data_inicial.value
            df = data_final.value
            cliente_id = dropdown_clientes.value
            pago_val = dropdown_pago.value
            di_str = str(di)
            df_str = str(df)
            crediarios = crediario_api.get_all()
            if not isinstance(crediarios, list):
                crediarios = [crediarios] if crediarios else []
            produtos_todos = produtos_todos_api.get_all()
            if not isinstance(produtos_todos, list):
                produtos_todos = [produtos_todos] if produtos_todos else []
            crediario_df = pd.DataFrame(crediarios)
            produtos_df = pd.DataFrame(produtos_todos)
            if not crediario_df.empty and not produtos_df.empty:
                merged_df = crediario_df.merge(
                    produtos_df[['id_Prod', 'nome_Prod', 'Valor_Prod']],
                    left_on='id_Prod', right_on='id_Prod', how='left'
                )
            else:
                merged_df = crediario_df
            crediarios_periodo = merged_df[(merged_df['data'] >= di_str) & (merged_df['data'] <= df_str)]
            if cliente_id:
                crediarios_periodo = crediarios_periodo[crediarios_periodo['id_cliente'].astype(str) == cliente_id]
                # Quando um cliente específico é selecionado, mostra apenas os não pagos
                crediarios_periodo = crediarios_periodo[crediarios_periodo['pago'].astype(str) == '0']
            elif pago_val in ("1", "0"):
                # Só aplica o filtro de pago quando nenhum cliente específico está selecionado
                crediarios_periodo = crediarios_periodo[crediarios_periodo['pago'].astype(str) == pago_val]
            
            # Ordena sempre colocando pago=0 primeiro, depois por data
            if not crediarios_periodo.empty:
                crediarios_periodo = crediarios_periodo.sort_values(['pago', 'data'], ascending=[True, True])
            # Remove a coluna 'hora' do PDF
            campos_exibir = ['data', 'qtd', 'nome_Prod', 'Valor_Prod', 'sub_total_calc']
            colunas_legenda = {
                'data': 'Data',
                'qtd': 'Qtd',
                'nome_Prod': 'Produto',
                'Valor_Prod': 'Valor Unit.',
                'sub_total_calc': 'Subtotal'
            }
            if not crediarios_periodo.empty:
                crediarios_periodo = crediarios_periodo.copy()
                if 'data' in crediarios_periodo.columns:
                    def formatar_data(d):
                        try:
                            data_str = str(d).split('T')[0]
                            return datetime.datetime.strptime(data_str, '%Y-%m-%d').strftime('%d/%m/%Y')
                        except Exception:
                            return d or ''
                    crediarios_periodo['data'] = crediarios_periodo['data'].apply(formatar_data)
                if 'sub_total_calc' not in crediarios_periodo.columns:
                    crediarios_periodo['sub_total_calc'] = crediarios_periodo.apply(
                        lambda row: float(row.get('qtd', 0)) * float(str(row.get('Valor_Prod', 0)).replace(",", ".")), axis=1
                    )
                # Geração do PDF
                if cliente_id:
                    cliente_nome = next((c.get('nome', '') + ' ' + c.get('sobrenome', '') for c in clientes if str(c.get('id', '')) == str(cliente_id)), f'cliente_{cliente_id}')
                else:
                    cliente_nome = 'todos_clientes'
                # Remove caracteres inválidos do nome do cliente para pasta
                cliente_nome_pasta = re.sub(r'[^a-zA-Z0-9_\-]', '_', cliente_nome)
                pasta_destino = os.path.join(os.path.dirname(__file__), '../Crediario', cliente_nome_pasta)
                os.makedirs(pasta_destino, exist_ok=True)
                data_pdf = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                pdf_path = os.path.join(pasta_destino, f'{data_pdf}.pdf')
                c = canvas.Canvas(pdf_path, pagesize=A4)
                width, height = A4
                # Cabeçalho personalizado
                logo_path = os.path.join(os.path.dirname(__file__), '../../acents/L.png')
                try:
                    c.drawImage(logo_path, 40, height-100, width=60, height=60, preserveAspectRatio=True, mask='auto')
                except Exception:
                    pass  # Se não encontrar o logo, ignora
                c.setFont("Helvetica-Bold", 16)
                c.drawString(110, height-60, "LePapon Lanches - Claudemir")
                c.setFont("Helvetica", 10)
                c.drawString(110, height-80, "Endereço: João Venâncio Girarde, nº 260")
                c.drawString(110, height-95, "CNPJ: 33.794.253/0001-33   Fone: (55) 5499-2635135")
                # Data do relatório
                c.setFont("Helvetica", 10)
                c.drawString(400, height-60, f"Data: {datetime.datetime.now().strftime('%d/%m/%Y')}")
                # Título do relatório
                c.setFont("Helvetica-Bold", 14)
                c.drawString(40, height-120, f"Relatório de Crediário: {cliente_nome}")
                c.setFont("Helvetica", 10)
                y = height-150
                # Definição das larguras das colunas
                col_widths = [70, 50, 200, 70, 70]  # data, qtd, nome_Prod, Valor_Prod, sub_total_calc
                x_positions = [40]
                for w in col_widths[:-1]:
                    x_positions.append(x_positions[-1] + w)
                # Cabeçalho
                for i, campo in enumerate(campos_exibir):
                    c.drawString(x_positions[i], y, colunas_legenda[campo])
                y -= 20
                # Dados
                for _, row in crediarios_periodo.iterrows():
                    for i, campo in enumerate(campos_exibir):
                        c.drawString(x_positions[i], y, str(row.get(campo, "")))
                    y -= 18
                    if y < 60:
                        c.showPage()
                        y = height-40
                # Escreve o total no final do PDF
                if y < 80:
                    c.showPage()
                    y = height-40
                c.setFont("Helvetica-Bold", 12)
                c.drawString(40, y-10, f"Total do período: R$ {crediarios_periodo['sub_total_calc'].sum():.2f}")
                c.save()
                # Upload PDF para o droplet usando EnviarContaCliente
                try:
                    uploader = EnviarContaCliente(token=GRAPH_API_TOKEN, phone_number_id="465787769946848")
                    # Parâmetros do droplet
                    host = "64.23.179.108"
                    usuario = "claus"
                    caminho_chave = "/home/claus/.ssh/id_rsa"
                    caminho_remoto = f"/var/www/lepapon.com.br/Android-LePapon-Pedidos/files/{cliente_nome_pasta}_{data_pdf}.pdf"
                    uploader.upload_pdf_droplet(host, usuario, pdf_path, caminho_remoto, caminho_chave)
                    # Gera a URL pública do PDF (ajuste conforme seu domínio)
                    pdf_url = f"https://lepapon.com.br/pdf/{data_pdf}.pdf"
                    msg.value = f"PDF gerado e enviado! URL: {pdf_url}"
                    msg.color = "green"
                except Exception as upload_err:
                    msg.value = f"PDF gerado, mas erro ao enviar: {upload_err}"
                    msg.color = "orange"
                msg.visible = True
            else:
                msg.value = "Nenhum dado para exportar."
                msg.color = "red"
                msg.visible = True
            page.update()
        except Exception as e:
            msg.value = f"Erro ao exportar PDF: {e}"
            msg.color = "red"
            msg.visible = True
            page.update()

    botao_pdf = ft.ElevatedButton("Exportar PDF", on_click=lambda e: exportar_pdf())

    def enviar_conta_cliente(e):
        print("Enviando conta para o cliente...")
        try:
            di = data_inicial.value
            df = data_final.value
            cliente_id = dropdown_clientes.value
            if not cliente_id:
                msg.value = "Selecione um cliente para enviar a conta."
                msg.color = "red"
                msg.visible = True
                page.update()
                return
            # Nome do cliente e nome do arquivo
            cliente_nome = next((c.get('nome', '') + ' ' + c.get('sobrenome', '') for c in clientes if str(c.get('id', '')) == str(cliente_id)), f'cliente_{cliente_id}')
            cliente_nome_pasta = re.sub(r'[^a-zA-Z0-9_\-]', '_', cliente_nome)
            data_pdf = datetime.datetime.now().strftime('%Y-%m-%d')
            pdf_path = os.path.join(os.path.dirname(__file__), '../Crediario', cliente_nome_pasta, f'{cliente_nome_pasta}_{data_pdf}.pdf')
            # URL pública do PDF
            #data_pdf = '2025-06-15'
            pdf_url = "https://lepapon.com.br/api/pdf/"+ cliente_nome_pasta + '_' + data_pdf + ".pdf"
            # Número do cliente (ajuste para buscar do cadastro se necessário)
            numero_cliente = '555491253180' #next((c.get('telefone', '') for c in clientes if str(c.get('id', '')) == str(cliente_id)), None)
            if not numero_cliente:
                msg.value = "Telefone do cliente não encontrado."
                msg.color = "red"
                msg.visible = True
                page.update()
                return
            uploader = EnviarContaCliente(token=GRAPH_API_TOKEN, phone_number_id="469403086249830")
            resposta = uploader.enviar_pdf(numero_cliente, pdf_url, nome_arquivo=cliente_nome_pasta + '_' + data_pdf + '.pdf')
            print(f"Resposta do envio: {resposta}")
            if resposta.get('messages'):
                msg.value = f"Conta enviada para o cliente via WhatsApp!"
                msg.color = "green"
            else:
                msg.value = f"Falha ao enviar pelo WhatsApp: {resposta}"
                msg.color = "orange"
            msg.visible = True
            page.update()
        except Exception as e:
            msg.value = f"Erro ao enviar conta: {e}"
            msg.color = "red"
            msg.visible = True
            page.update()

    botao_enviar_conta = ft.ElevatedButton("Enviar conta para o cliente", on_click=enviar_conta_cliente)
    # Adicionar campo para novo recebimento
    novo_recebimento_valor = ft.TextField(label="Valor Recebido", width=120)

    def marcar_crediario_pago(cliente_id, valor_pagamento):
        """
        Marca itens do crediário do cliente como pagos (pago=1) até consumir o valor do pagamento.
        Retorna a diferença (troco se negativo, valor restante se positivo).
        """
        try:
            # Busca todos os crediários do cliente, não pagos, ordenados por data
            crediarios = crediario_api.get_all()
            if not isinstance(crediarios, list):
                crediarios = [crediarios] if crediarios else []
            # Faz o merge para adicionar Valor_Prod do produto pelo id_Prod
            produtos_todos = produtos_todos_api.get_all()
            if not isinstance(produtos_todos, list):
                produtos_todos = [produtos_todos] if produtos_todos else []
            crediario_df = pd.DataFrame(crediarios)
            produtos_df = pd.DataFrame(produtos_todos)
            if not crediario_df.empty and not produtos_df.empty:
                crediario_df = crediario_df.merge(
                    produtos_df[['id_Prod', 'Valor_Prod']],
                    left_on='id_Prod', right_on='id_Prod', how='left'
                )
                # Atualiza os itens com o novo Valor_Prod
                crediarios = crediario_df.to_dict(orient='records')
            # Filtra do cliente e não pagos
            itens = [c for c in crediarios if str(c.get('id_cliente')) == str(cliente_id) and str(c.get('pago', '0')) == '0']
            # Ordena por data e hora (FIFO)                
            itens.sort(key=lambda x: (x.get('data', ''), x.get('hora', '')))
            valor_restante = float(valor_pagamento)
            for item in itens:
                # Formata a data para 'YYYY-MM-DD' se vier no formato ISO
                if 'data' in item and isinstance(item['data'], str) and 'T' in item['data']:
                    item['data'] = item['data'].split('T')[0]
                sub_total = float(item['qtd']) * float(item['Valor_Prod'])
                if valor_restante >= sub_total:
                    # Marca como pago
                    res_cred_update = crediario_api.update(item['id'], {'pago': 1})
                    print(f"Item marcado como pago: {res_cred_update}")
                    #print(res_cred_update)
                    valor_restante -= sub_total
                elif valor_restante > 0 and valor_restante < sub_total:
                    return valor_restante
                    
            return valor_restante
        except Exception as e:
            print(f"Erro ao marcar crediário pago: {e}")
            return f"Erro: {e}"
        

    def adicionar_saldo_recebido(cliente_id, valor):
        """
        Adiciona um registro em saldo_recebido com id_cliente e valor, ou faz update se já existir.
        """
        from models.saldo_recebido_api import SaldoRecebidoAPI
        saldo_api = SaldoRecebidoAPI(BASE_URL)
        # Busca todos os saldos recebidos do cliente
        saldos = saldo_api.get_all()
        if not isinstance(saldos, list):
            saldos = [saldos] if saldos else []
        saldo_existente = next((s for s in saldos if str(s.get('id_cliente')) == str(cliente_id)), None)
        data = {
            "id_cliente": cliente_id,
            'data': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "valor": valor
        }
        if saldo_existente:
            return saldo_api.update(saldo_existente['id'], data)
        else:
            return saldo_api.create(data)

    def get_saldo_recebido_por_cliente(cliente_id):
        """
        Retorna a soma do saldo_recebido para um cliente específico.
        """
        from models.saldo_recebido_api import SaldoRecebidoAPI
        saldo_api = SaldoRecebidoAPI(BASE_URL)
        try:
            saldos = saldo_api.get_all()
            if not isinstance(saldos, list):
                saldos = [saldos] if saldos else []
            total = sum(float(str(s.get('valor', 0)).replace(',', '.')) for s in saldos if str(s.get('id_cliente')) == str(cliente_id))
            return total
        except Exception as e:
            return f"Erro ao buscar saldo recebido: {e}"

    def processar_pagamento_cliente(cliente_id, valor_pagamento):
        """
        Processa o pagamento do cliente, usando saldo_recebido se existir, soma ao valor do pagamento,
        marca crediário como pago e atualiza saldo_recebido com o restante (troco ou saldo).
        """
        saldo_atual = get_saldo_recebido_por_cliente(cliente_id)
        try:
            saldo_atual = float(saldo_atual)
        except:
            saldo_atual = 0.0
        valor_total = float(valor_pagamento) + saldo_atual
        diferenca = marcar_crediario_pago(cliente_id, valor_total)
        print(f"Saldo atual: {saldo_atual}, Valor total: {valor_total}, Diferença: {diferenca}")
        # Atualiza saldo_recebido com a diferença
        res_saldo_recebido = adicionar_saldo_recebido(cliente_id, diferenca)
        print(f"Saldo recebido atualizado: {res_saldo_recebido}")
        return diferenca
    
    def adicionar_recebimento(e=None):
        try:
            valor = novo_recebimento_valor.value
            cliente_id = dropdown_clientes.value
            if not valor or not cliente_id:
                msg.value = "Informe o valor e selecione um cliente."
                msg.color = "red"
                msg.visible = True
                page.update()
                return
            agora = datetime.datetime.now()
            data_str = agora.strftime('%Y-%m-%d')
            hora_str = agora.strftime('%H:%M:%S')
            data = {
                "id_cliente": cliente_id,
                "data": data_str,
                "hora": hora_str,
                "valor": valor
            }
            recebido_api.create(data)
            msg.value = "Recebimento adicionado com sucesso!"
            msg.color = "green"
            msg.visible = True
            novo_recebimento_valor.value = ""
            # Processa o pagamento do cliente
            diferenca = processar_pagamento_cliente(cliente_id, valor)
            print(f"Diferença após pagamento: {diferenca}")
            page.update()
        except Exception as e:
            msg.value = f"Erro ao adicionar recebimento: {e}"
            msg.color = "red"
            msg.visible = True
            page.update()
    botao_adicionar_recebimento = ft.ElevatedButton("Adicionar Recebimento", on_click=adicionar_recebimento)

    def limpar_pdfs_servidor(e):
        """Limpa todos os PDFs do servidor remoto"""
        try:
            uploader = EnviarContaCliente(token=GRAPH_API_TOKEN, phone_number_id="469403086249830")
            host = "64.23.179.108"
            usuario = "claus"
            caminho_chave = "/home/claus/.ssh/id_rsa"
            pasta_remota = "/var/www/lepapon.com.br/Android-LePapon-Pedidos/files"
            
            pdfs_removidos = uploader.delete_all_pdfs_from_folder(host, usuario, pasta_remota, caminho_chave)
            
            if pdfs_removidos > 0:
                msg.value = f"{pdfs_removidos} arquivos PDF removidos do servidor!"
                msg.color = "green"
            else:
                msg.value = "Nenhum arquivo PDF encontrado para remover."
                msg.color = "orange"
            
            msg.visible = True
            page.update()
        except Exception as ex:
            msg.value = f"Erro ao limpar PDFs do servidor: {ex}"
            msg.color = "red"
            msg.visible = True
            page.update()

    botao_limpar_pdfs = ft.ElevatedButton("Limpar PDFs do Servidor", on_click=limpar_pdfs_servidor)

    return ft.Column([
        ft.Text("Lista de Crediário", style=ft.TextThemeStyle.HEADLINE_SMALL),
        ft.Row([
            data_inicial,
            data_final,
            filtro_nome,
            dropdown_clientes,
            dropdown_pago
        ]),
        ft.Row([
            botao_pdf,
            botao_enviar_conta,
            total_crediario_label,
            saldo_recebido,
            saldo_devedor
        ]),
        ft.Row([
            novo_recebimento_valor,
            botao_adicionar_recebimento,
            botao_limpar_pdfs
        ]),
        ft.Column(controls=[
            tabela,
            ft.Divider(),
            msg
        ]
        , scroll=ft.ScrollMode.ALWAYS, height=600, width=900),
    ])
