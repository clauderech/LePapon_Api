import flet as ft
from models.recebido_api import RecebidoAPI
from models.clientes_api import ClientesAPI
import datetime
import pandas as pd
import os
import sys

# Importa as novas classes utilitárias
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../utils'))
from utils.base_view import BaseView
from utils.pdf_generator import PDFGenerator
from utils.common_utils import BASE_URL, parse_float, formatar_data, obter_nome_cliente, sanitize_filename

recebido_api = RecebidoAPI(BASE_URL)
clientes_api = ClientesAPI(BASE_URL)

def recebido_view(page: ft.Page):
    # Inicializa a view base
    view_helper = BaseView(page, recebido_api, clientes_api)
    
    # Cria os controles de filtro usando a classe base
    data_inicial, data_final = view_helper.criar_filtros_data(lambda: filtrar_recebidos_periodo())
    dropdown_clientes = view_helper.criar_dropdown_clientes(lambda: filtrar_recebidos_periodo())
    filtro_nome = view_helper.criar_filtro_nome_cliente(dropdown_clientes)
    
    total_recebidos_label = ft.Text("Total do período: 0.00", style=ft.TextThemeStyle.TITLE_MEDIUM, width=250)
    tabela_ref = ft.Ref[ft.DataTable]()

    def filtrar_recebidos_periodo():
        di = data_inicial.value
        df = data_final.value
        cliente_id = dropdown_clientes.value
        
        if not di or not df:
            return
        
        # Usa a classe base para processar dados do período
        recebidos_periodo = view_helper.processar_dados_periodo(di, df, cliente_id, 'id_cliente')
        
        # Campos para exibir
        campos_exibir = ['data', 'hora', 'nome_cliente', 'valor']
        colunas_legenda = {
            'data': 'Data',
            'hora': 'Hora', 
            'nome_cliente': 'Cliente',
            'valor': 'Valor'
        }
        
        # Formata dados para exibição
        recebidos_exibir = view_helper.formatar_dados_exibicao(recebidos_periodo, campos_exibir)
        
        # Cria a tabela
        columns, rows = view_helper.criar_tabela_datatable(recebidos_exibir, campos_exibir, colunas_legenda)
        
        # Atualiza a tabela
        tabela_ref.current.columns = columns
        tabela_ref.current.rows = rows
        
        # Calcula e exibe o total
        total = view_helper.calcular_total(recebidos_periodo, 'valor')
        total_recebidos_label.value = f"Total do período: R$ {total:.2f}"
        
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
            recebidos_periodo = view_helper.processar_dados_periodo(di, df, cliente_id, 'id_cliente')
            
            if recebidos_periodo.empty:
                view_helper.mostrar_mensagem("Nenhum recebimento encontrado no período.", "orange")
                return
            
            # Formata dados para PDF
            df_pdf = recebidos_periodo.copy()
            df_pdf['data'] = df_pdf['data'].apply(formatar_data)
            df_pdf['nome_cliente'] = df_pdf['id_cliente'].apply(
                lambda x: obter_nome_cliente(view_helper.clientes, x)
            )
            
            # Configurações do PDF
            colunas_legenda = {
                'data': 'Data',
                'hora': 'Hora',
                'nome_cliente': 'Cliente', 
                'valor': 'Valor'
            }
            larguras_colunas = [80, 60, 250, 80]
            
            # Cria nome do arquivo
            cliente_nome = "Todos_Clientes"
            if cliente_id:
                cliente_nome = obter_nome_cliente(view_helper.clientes, cliente_id)
                cliente_nome = sanitize_filename(cliente_nome)
            
            data_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            nome_arquivo = f"recebimentos_{cliente_nome}_{data_str}.pdf"
            pdf_path = os.path.join("Crediario", nome_arquivo)
            
            # Gera o PDF usando a nova classe
            pdf_generator = PDFGenerator()
            titulo = f"Relatório de Recebimentos - {di} a {df}"
            
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
    
    # Campos de entrada para novo recebimento
    id_cliente_field = ft.TextField(label="ID Cliente", width=100)
    valor_field = ft.TextField(label="Valor", width=120)
    descricao_field = ft.TextField(label="Descrição", width=200)
    
    def adicionar_recebido():
        if not id_cliente_field.value or not valor_field.value:
            view_helper.mostrar_mensagem("ID Cliente e Valor são obrigatórios.", "red")
            return
        
        try:
            valor = parse_float(valor_field.value)
            if valor <= 0:
                view_helper.mostrar_mensagem("Valor deve ser maior que zero.", "red")
                return
            
            agora = datetime.datetime.now()
            dados = {
                'id_cliente': int(id_cliente_field.value),
                'valor': valor,
                'descricao': descricao_field.value or '',
                'data': agora.strftime('%Y-%m-%d'),
                'hora': agora.strftime('%H:%M:%S')
            }
            
            recebido_api.create(dados)
            
            # Limpa os campos
            id_cliente_field.value = ""
            valor_field.value = ""
            descricao_field.value = ""
            
            view_helper.mostrar_mensagem("Recebimento adicionado com sucesso!", "green")
            filtrar_recebidos_periodo()  # Atualiza a lista
            
        except ValueError:
            view_helper.mostrar_mensagem("ID Cliente deve ser um número válido.", "red")
        except Exception as e:
            view_helper.mostrar_mensagem(f"Erro ao adicionar recebimento: {e}", "red")
    
    # Inicializa tabela vazia
    tabela_ref.current = ft.DataTable(
        columns=[ft.DataColumn(ft.Text("Data"))],
        rows=[ft.DataRow([ft.DataCell(ft.Text(""))])],
        show_checkbox_column=False,
        heading_row_color=ft.Colors.GREY_200,
        heading_row_height=40
    )
    
    # Layout da view
    content = ft.Column([
        # Título
        ft.Text("Controle de Recebimentos", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
        
        # Filtros
        ft.Row([
            data_inicial,
            data_final,
            ft.ElevatedButton("Exportar PDF", on_click=lambda e: exportar_pdf())
        ]),
        
        ft.Row([
            dropdown_clientes,
            filtro_nome
        ]),
        
        # Adicionar novo recebimento
        ft.Divider(),
        ft.Text("Adicionar Novo Recebimento", style=ft.TextThemeStyle.TITLE_MEDIUM),
        ft.Row([
            id_cliente_field,
            valor_field,
            descricao_field,
            ft.ElevatedButton("Adicionar", on_click=lambda e: adicionar_recebido())
        ]),
        
        # Tabela e total
        ft.Divider(),
        total_recebidos_label,
        ft.Container(
            content=tabela_ref.current,
            height=400,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=8,
            padding=10
        ),
        
        # Mensagens
        view_helper.msg
    ], scroll=ft.ScrollMode.AUTO, spacing=10)
    
    # Carrega dados iniciais
    filtrar_recebidos_periodo()
    
    return content
