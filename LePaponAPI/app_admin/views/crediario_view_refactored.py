import flet as ft
from models.crediario_api import CrediarioAPI
from models.clientes_api import ClientesAPI
from models.produtos_todos_api import ProdutosTodosAPI
from models.enviar_conta_cliente import EnviarContaCliente
from models.recebido_api import RecebidoAPI
import datetime
import pandas as pd
import tempfile
import os
import sys

# Importa as novas classes utilitárias
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../utils'))
from utils.base_view import BaseView
from utils.pdf_generator import PDFGenerator
from utils.common_utils import BASE_URL, parse_float, formatar_data, obter_nome_cliente, sanitize_filename, get_current_datetime

# APIs
crediario_api = CrediarioAPI(BASE_URL)
clientes_api = ClientesAPI(BASE_URL)
produtos_todos_api = ProdutosTodosAPI(BASE_URL)
recebido_api = RecebidoAPI(BASE_URL)

# Configurações
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../../../.env'))

API_KEY = os.getenv("MINHA_API_KEY")
HEADERS = {"x-api-key": API_KEY}
GRAPH_API_TOKEN = os.getenv("GRAPH_API_TOKEN")

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
        total = sum(parse_float(s.get('valor', 0)) for s in saldos if str(s.get('id_cliente')) == str(cliente_id))
        return total
    except Exception as e:
        return f"Erro ao buscar saldo recebido: {e}"

def crediario_view(page: ft.Page):
    # Inicializa a view base
    view_helper = BaseView(page, crediario_api, clientes_api)
    
    # Cria os controles de filtro usando a classe base
    data_inicial, data_final = view_helper.criar_filtros_data(lambda: filtrar_crediario_periodo())
    dropdown_clientes = view_helper.criar_dropdown_clientes(lambda: filtrar_crediario_periodo())
    filtro_nome = view_helper.criar_filtro_nome_cliente(dropdown_clientes)
    
    # Controles específicos do crediário
    total_crediario_label = ft.Text("Total do período: 0.00", style=ft.TextThemeStyle.TITLE_MEDIUM, width=250)
    saldo_cliente_label = ft.Text("Saldo recebido do cliente: 0.00", style=ft.TextThemeStyle.TITLE_SMALL, width=300)
    tabela_ref = ft.Ref[ft.DataTable]()

    def filtrar_crediario_periodo():
        di = data_inicial.value
        df = data_final.value
        cliente_id = dropdown_clientes.value
        
        if not di or not df:
            return
        
        # Usa a classe base para processar dados do período
        crediario_periodo = view_helper.processar_dados_periodo(di, df, cliente_id, 'id_cliente')
        
        # Campos para exibir
        campos_exibir = ['data', 'hora', 'nome_cliente', 'id_produto', 'nome_produto', 'quantidade', 'valor_unitario', 'total']
        colunas_legenda = {
            'data': 'Data',
            'hora': 'Hora',
            'nome_cliente': 'Cliente',
            'id_produto': 'ID Produto',
            'nome_produto': 'Produto',
            'quantidade': 'Qtd',
            'valor_unitario': 'Valor Unit.',
            'total': 'Total'
        }
        
        # Adiciona informações dos produtos
        if not crediario_periodo.empty:
            try:
                produtos = produtos_todos_api.get_all()
                if not isinstance(produtos, list):
                    produtos = [produtos] if produtos else []
                
                produtos_dict = {str(p.get('id', '')): p for p in produtos if isinstance(p, dict)}
                
                def obter_nome_produto(produto_id):
                    produto = produtos_dict.get(str(produto_id), {})
                    return produto.get('nome', f'Produto {produto_id}')
                
                crediario_periodo = crediario_periodo.copy()
                crediario_periodo['nome_produto'] = crediario_periodo['id_produto'].apply(obter_nome_produto)
            except Exception:
                crediario_periodo['nome_produto'] = crediario_periodo['id_produto'].apply(lambda x: f'Produto {x}')
        
        # Formata dados para exibição
        crediario_exibir = view_helper.formatar_dados_exibicao(crediario_periodo, campos_exibir)
        
        # Cria a tabela
        columns, rows = view_helper.criar_tabela_datatable(crediario_exibir, campos_exibir, colunas_legenda)
        
        # Atualiza a tabela
        tabela_ref.current.columns = columns
        tabela_ref.current.rows = rows
        
        # Calcula e exibe o total
        total = view_helper.calcular_total(crediario_periodo, 'total')
        total_crediario_label.value = f"Total do período: R$ {total:.2f}"
        
        # Atualiza saldo do cliente se selecionado
        if cliente_id:
            try:
                saldo = get_saldo_recebido_por_cliente(cliente_id)
                if isinstance(saldo, (int, float)):
                    saldo_cliente_label.value = f"Saldo recebido do cliente: R$ {saldo:.2f}"
                else:
                    saldo_cliente_label.value = f"Saldo recebido do cliente: {saldo}"
            except Exception as e:
                saldo_cliente_label.value = f"Erro ao buscar saldo: {e}"
        else:
            saldo_cliente_label.value = "Saldo recebido do cliente: Selecione um cliente"
        
        page.update()

    def exportar_pdf():
        di = data_inicial.value
        df = data_final.value
        cliente_id = dropdown_clientes.value
        
        if not di or not df:
            view_helper.mostrar_mensagem("Por favor, selecione um período.", "red")
            return
        
        try:
            # Processa dados do período
            crediario_periodo = view_helper.processar_dados_periodo(di, df, cliente_id, 'id_cliente')
            
            if crediario_periodo.empty:
                view_helper.mostrar_mensagem("Nenhum registro encontrado no período.", "orange")
                return
            
            # Adiciona informações dos produtos
            try:
                produtos = produtos_todos_api.get_all()
                if not isinstance(produtos, list):
                    produtos = [produtos] if produtos else []
                
                produtos_dict = {str(p.get('id', '')): p for p in produtos if isinstance(p, dict)}
                
                def obter_nome_produto(produto_id):
                    produto = produtos_dict.get(str(produto_id), {})
                    return produto.get('nome', f'Produto {produto_id}')
                
                crediario_periodo = crediario_periodo.copy()
                crediario_periodo['nome_produto'] = crediario_periodo['id_produto'].apply(obter_nome_produto)
            except Exception:
                crediario_periodo['nome_produto'] = crediario_periodo['id_produto'].apply(lambda x: f'Produto {x}')
            
            # Formata dados para PDF
            df_pdf = crediario_periodo.copy()
            df_pdf['data'] = df_pdf['data'].apply(formatar_data)
            df_pdf['nome_cliente'] = df_pdf['id_cliente'].apply(
                lambda x: obter_nome_cliente(view_helper.clientes, x)
            )
            
            # Configurações do PDF
            colunas_legenda = {
                'data': 'Data',
                'hora': 'Hora',
                'nome_cliente': 'Cliente',
                'nome_produto': 'Produto',
                'quantidade': 'Qtd',
                'valor_unitario': 'Vlr Unit.',
                'total': 'Total'
            }
            larguras_colunas = [60, 50, 120, 150, 40, 60, 60]
            
            # Cria nome do arquivo
            cliente_nome = "Todos_Clientes"
            if cliente_id:
                cliente_nome = obter_nome_cliente(view_helper.clientes, cliente_id)
                cliente_nome = sanitize_filename(cliente_nome)
            
            data_atual = get_current_datetime()
            nome_arquivo = f"crediario_{cliente_nome}_{data_atual['data']}.pdf"
            
            # Cria pasta do cliente se não existir
            pasta_cliente = os.path.join("Crediario", cliente_nome)
            os.makedirs(pasta_cliente, exist_ok=True)
            pdf_path = os.path.join(pasta_cliente, nome_arquivo)
            
            # Gera o PDF usando a nova classe
            pdf_generator = PDFGenerator()
            titulo = f"Relatório de Crediário - {di} a {df}"
            
            pdf_generator.gerar_pdf_completo(
                df_pdf[list(colunas_legenda.keys())],
                titulo,
                pdf_path,
                colunas_legenda,
                larguras_colunas
            )
            
            view_helper.mostrar_mensagem(f"PDF exportado: {pdf_path}", "green")
            
        except Exception as e:
            view_helper.mostrar_mensagem(f"Erro ao exportar PDF: {e}", "red")

    def enviar_whatsapp():
        cliente_id = dropdown_clientes.value
        if not cliente_id:
            view_helper.mostrar_mensagem("Selecione um cliente primeiro.", "red")
            return
        
        try:
            # Exporta PDF temporário
            temp_file = tempfile.mktemp(suffix='.pdf')
            
            # Processa dados do período
            di = data_inicial.value
            df = data_final.value
            crediario_periodo = view_helper.processar_dados_periodo(di, df, cliente_id, 'id_cliente')
            
            if crediario_periodo.empty:
                view_helper.mostrar_mensagem("Nenhum registro encontrado para enviar.", "orange")
                return
            
            # Prepara dados para o PDF (mesmo código da exportação)
            try:
                produtos = produtos_todos_api.get_all()
                if not isinstance(produtos, list):
                    produtos = [produtos] if produtos else []
                
                produtos_dict = {str(p.get('id', '')): p for p in produtos if isinstance(p, dict)}
                
                def obter_nome_produto(produto_id):
                    produto = produtos_dict.get(str(produto_id), {})
                    return produto.get('nome', f'Produto {produto_id}')
                
                crediario_periodo = crediario_periodo.copy()
                crediario_periodo['nome_produto'] = crediario_periodo['id_produto'].apply(obter_nome_produto)
            except Exception:
                crediario_periodo['nome_produto'] = crediario_periodo['id_produto'].apply(lambda x: f'Produto {x}')
            
            df_pdf = crediario_periodo.copy()
            df_pdf['data'] = df_pdf['data'].apply(formatar_data)
            df_pdf['nome_cliente'] = df_pdf['id_cliente'].apply(
                lambda x: obter_nome_cliente(view_helper.clientes, x)
            )
            
            # Gera PDF temporário
            colunas_legenda = {
                'data': 'Data',
                'hora': 'Hora', 
                'nome_cliente': 'Cliente',
                'nome_produto': 'Produto',
                'quantidade': 'Qtd',
                'valor_unitario': 'Vlr Unit.',
                'total': 'Total'
            }
            larguras_colunas = [60, 50, 120, 150, 40, 60, 60]
            
            pdf_generator = PDFGenerator()
            titulo = f"Conta - {di} a {df}"
            
            pdf_generator.gerar_pdf_completo(
                df_pdf[list(colunas_legenda.keys())],
                titulo,
                temp_file,
                colunas_legenda,
                larguras_colunas
            )
            
            # Envia via WhatsApp
            enviar_conta = EnviarContaCliente(
                token=GRAPH_API_TOKEN,
                phone_number_id=""  # Configurar conforme necessário
            )
            
            # Busca dados do cliente
            cliente = next((c for c in view_helper.clientes if str(c.get('id', '')) == str(cliente_id)), None)
            if not cliente:
                view_helper.mostrar_mensagem("Cliente não encontrado.", "red")
                return
            
            telefone = cliente.get('telefone', '')
            if not telefone:
                view_helper.mostrar_mensagem("Cliente não possui telefone cadastrado.", "red")
                return
            
            # Envia a conta
            resultado = enviar_conta.enviar_pdf(cliente_id, temp_file, telefone)
            
            if "sucesso" in str(resultado).lower():
                view_helper.mostrar_mensagem("Conta enviada via WhatsApp com sucesso!", "green")
            else:
                view_helper.mostrar_mensagem(f"Erro ao enviar: {resultado}", "red")
            
            # Remove arquivo temporário
            try:
                os.unlink(temp_file)
            except:
                pass
                
        except Exception as e:
            view_helper.mostrar_mensagem(f"Erro ao enviar via WhatsApp: {e}", "red")

    # Inicializa tabela vazia
    tabela_ref.current = ft.DataTable(
        columns=[ft.DataColumn(ft.Text("Data"))],
        rows=[ft.DataRow([ft.DataCell(ft.Text(""))])],
        show_checkbox_column=False,
        heading_row_height=40
    )
    
    # Layout da view
    content = ft.Column([
        # Título
        ft.Text("Controle de Crediário", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
        
        # Filtros
        ft.Row([
            data_inicial,
            data_final,
            ft.ElevatedButton("Exportar PDF", on_click=lambda e: exportar_pdf()),
            ft.ElevatedButton("Enviar WhatsApp", on_click=lambda e: enviar_whatsapp())
        ]),
        
        ft.Row([
            dropdown_clientes,
            filtro_nome
        ]),
        
        # Totais
        ft.Row([
            total_crediario_label,
            saldo_cliente_label
        ]),
        
        # Tabela
        ft.Container(
            content=tabela_ref.current,
            height=400,
            border=ft.border.all(1),
            border_radius=8,
            padding=10
        ),
        
        # Mensagens
        view_helper.msg
    ], scroll=ft.ScrollMode.AUTO, spacing=10)
    
    # Carrega dados iniciais
    filtrar_crediario_periodo()
    
    return content
